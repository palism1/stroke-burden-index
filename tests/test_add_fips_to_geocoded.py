import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
import pandas as pd
import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "reference" / "ct_crosswalk"))

from add_fips_to_geocoded import (
    _query_county,
    lookup_fips,
    add_fips,
    _CT_VINTAGE,
    _MAX_RETRIES,
)


# Helpers

def _ok(state, county):
    resp = MagicMock()
    resp.raise_for_status.return_value = None
    resp.json.return_value = {
        "result": {"geographies": {"Counties": [{"STATE": state, "COUNTY": county}]}}
    }
    return resp


def _empty():
    resp = MagicMock()
    resp.raise_for_status.return_value = None
    resp.json.return_value = {"result": {"geographies": {"Counties": []}}}
    return resp


def _err():
    resp = MagicMock()
    resp.raise_for_status.side_effect = requests.RequestException("timeout")
    return resp


# _query_county

def test_query_county_success():
    with patch("add_fips_to_geocoded.requests.get", return_value=_ok("36", "001")):
        assert _query_county(-73.9, 40.7, "4") == ("36", "001")


def test_query_county_empty_counties_returns_none():
    with patch("add_fips_to_geocoded.requests.get", return_value=_empty()):
        assert _query_county(-73.9, 40.7, "4") is None


def test_query_county_retries_and_succeeds():
    sides = [_err(), _err(), _ok("36", "001")]
    with patch("add_fips_to_geocoded.requests.get", side_effect=sides):
        with patch("add_fips_to_geocoded.time.sleep"):
            assert _query_county(-73.9, 40.7, "4") == ("36", "001")


def test_query_county_exhausts_retries_and_raises():
    with patch("add_fips_to_geocoded.requests.get", side_effect=[_err()] * _MAX_RETRIES):
        with patch("add_fips_to_geocoded.time.sleep"):
            with pytest.raises(requests.RequestException):
                _query_county(-73.9, 40.7, "4")


def test_query_county_calls_exactly_max_retries_times():
    mock_get = MagicMock(side_effect=[_err()] * _MAX_RETRIES)
    with patch("add_fips_to_geocoded.requests.get", mock_get):
        with patch("add_fips_to_geocoded.time.sleep"):
            with pytest.raises(requests.RequestException):
                _query_county(-73.9, 40.7, "4")
    assert mock_get.call_count == _MAX_RETRIES


# lookup_fips

def test_lookup_fips_non_ct():
    with patch("add_fips_to_geocoded.requests.get", return_value=_ok("36", "1")):
        assert lookup_fips(-73.9, 40.7) == "36001"


def test_lookup_fips_zero_pads():
    with patch("add_fips_to_geocoded.requests.get", return_value=_ok("9", "1")):
        assert lookup_fips(-73.9, 40.7) == "09001"


def test_lookup_fips_ct_requeries_with_ct_vintage():
    sides = [_ok("09", "110"), _ok("09", "001")]
    with patch("add_fips_to_geocoded.requests.get", side_effect=sides) as mock_get:
        result = lookup_fips(-72.7, 41.5)
    assert result == "09001"
    second_params = mock_get.call_args_list[1].kwargs["params"]
    assert second_params["vintage"] == _CT_VINTAGE


def test_lookup_fips_ct_fallback_when_ct_vintage_empty():
    # CT vintage returns empty counties — falls back to default-vintage result
    with patch("add_fips_to_geocoded.requests.get", side_effect=[_ok("09", "110"), _empty()]):
        result = lookup_fips(-72.7, 41.5)
    assert result == "09110"


def test_lookup_fips_returns_empty_when_no_county():
    with patch("add_fips_to_geocoded.requests.get", return_value=_empty()):
        assert lookup_fips(0.0, 0.0) == ""


def test_lookup_fips_raises_on_api_failure():
    # lookup_fips propagates; add_fips is what catches and converts to empty string
    with patch("add_fips_to_geocoded.requests.get", side_effect=[_err()] * _MAX_RETRIES):
        with patch("add_fips_to_geocoded.time.sleep"):
            with pytest.raises(requests.RequestException):
                lookup_fips(0.0, 0.0)


# add_fips

def test_add_fips_default_output_name(tmp_path):
    csv = tmp_path / "centers.csv"
    csv.write_text("latitude,longitude,name\n40.7,-73.9,Test\n")
    with patch("add_fips_to_geocoded.lookup_fips", return_value="36061"):
        with patch("add_fips_to_geocoded.validate_ct_codes"):
            with patch("add_fips_to_geocoded.time.sleep"):
                out = add_fips(csv)
    assert out == tmp_path / "centers_with_fips.csv"


def test_add_fips_output_contains_fips_column(tmp_path):
    csv = tmp_path / "centers.csv"
    csv.write_text("latitude,longitude,name\n40.7,-73.9,Test\n")
    with patch("add_fips_to_geocoded.lookup_fips", return_value="36061"):
        with patch("add_fips_to_geocoded.validate_ct_codes"):
            with patch("add_fips_to_geocoded.time.sleep"):
                out = add_fips(csv)
    result = pd.read_csv(out, dtype={"fips": str})
    assert "fips" in result.columns
    assert result.iloc[0]["fips"] == "36061"


def test_add_fips_raises_on_missing_latitude(tmp_path):
    csv = tmp_path / "bad.csv"
    csv.write_text("longitude,name\n-73.9,Test\n")
    with pytest.raises(ValueError, match="latitude"):
        add_fips(csv)


def test_add_fips_raises_on_missing_longitude(tmp_path):
    csv = tmp_path / "bad.csv"
    csv.write_text("latitude,name\n40.7,Test\n")
    with pytest.raises(ValueError, match="longitude"):
        add_fips(csv)
