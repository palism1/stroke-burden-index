import sys
from pathlib import Path
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "reference" / "ct_crosswalk"))
from validate_ct_codes import validate_ct_codes, CTCodeError


def df(fips_list):
    return pd.DataFrame({"fips": fips_list})


# Valid cases — should pass without raising

def test_valid_ct_county_codes():
    validate_ct_codes(df(["09001", "09003", "09005"]), fips_col="fips")


def test_non_ct_codes_are_ignored():
    validate_ct_codes(df(["36001", "34003", "36059"]), fips_col="fips")


def test_mixed_valid_ct_and_other_states():
    validate_ct_codes(df(["09001", "36001", "34003"]), fips_col="fips")


def test_all_91_counties_pass():
    """The actual spine file should pass the gate cleanly."""
    spine = pd.read_csv(
        Path(__file__).resolve().parents[1] / "data" / "ny_nj_ct_fips.csv",
        dtype={"fips": str},
    )
    validate_ct_codes(spine, fips_col="fips")


# Error cases — should raise

def test_planning_region_code_raises():
    with pytest.raises(CTCodeError, match="09110"):
        validate_ct_codes(df(["09110", "09001"]), fips_col="fips")


def test_all_planning_region_codes_raise():
    for code in ["09110", "09120", "09130", "09140", "09150", "09160", "09170", "09180", "09190"]:
        with pytest.raises(CTCodeError):
            validate_ct_codes(df([code]), fips_col="fips")


def test_integer_fips_raises():
    with pytest.raises(CTCodeError, match="non-string"):
        validate_ct_codes(pd.DataFrame({"fips": [9001, 36001]}), fips_col="fips")


def test_unknown_system_raises():
    with pytest.raises(ValueError, match="unknown system"):
        validate_ct_codes(df(["09001"]), fips_col="fips", system="bad_system")


def test_returns_dataframe_unchanged():
    frame = df(["09001", "36001"])
    result = validate_ct_codes(frame, fips_col="fips")
    assert result is frame


def test_empty_string_fips_passes_the_gate():
    # "" does not start with "09", so the gate ignores it. add_fips relies on
    # this by filtering unresolved rows before validating — pinned here so a
    # refactor does not change it silently.
    validate_ct_codes(df(["", "09001"]), fips_col="fips")
