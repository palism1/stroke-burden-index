import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "reference" / "ct_crosswalk"))

import build_site_data
from build_site_data import FIELD_LABELS, _join_indices, export_site_data


def _frame():
    return pd.DataFrame({
        "fips": ["36001", "09001"],
        "county": ["Albany", "Fairfield"],
        "state": ["NY", "CT"],
        "total_pop": [100000, 950000],
        "drive_time_min": [12.34567, np.nan],
        "some_new_metric": [1.0, 2.0],
    })


def test_counties_keyed_by_fips():
    payload = export_site_data(_frame())
    assert set(payload["counties"]) == {"36001", "09001"}
    assert payload["counties"]["36001"]["county"] == "Albany"
    assert payload["counties"]["09001"]["state"] == "CT"


def test_fips_county_state_not_repeated_as_fields():
    payload = export_site_data(_frame())
    assert "fips" not in payload["fields"]
    assert "county" not in payload["fields"]
    assert "state" not in payload["fields"]


def test_known_field_gets_plain_language_label():
    payload = export_site_data(_frame())
    assert payload["fields"]["drive_time_min"]["label"] == "Drive to nearest stroke center"
    assert payload["fields"]["drive_time_min"]["unit"] == "min"


def test_unknown_field_gets_fallback_label():
    payload = export_site_data(_frame())
    assert payload["fields"]["some_new_metric"]["label"] == "Some new metric"


def test_floats_rounded_and_nan_becomes_none():
    payload = export_site_data(_frame())
    assert payload["counties"]["36001"]["drive_time_min"] == 12.35
    assert payload["counties"]["09001"]["drive_time_min"] is None


def test_payload_is_json_serializable():
    import json

    json.dumps(export_site_data(_frame()))


def test_every_field_label_has_a_known_group():
    payload = export_site_data(_frame())
    for col, meta in payload["fields"].items():
        assert meta["group"] in payload["groups"], f"{col} has unknown group {meta['group']}"


def test_field_labels_registry_groups_are_valid():
    from build_site_data import GROUP_TITLES

    for col, meta in FIELD_LABELS.items():
        assert meta["group"] in GROUP_TITLES, f"{col} has unknown group {meta['group']}"


def test_join_indices_excludes_driver_columns(tmp_path, monkeypatch):
    # driver_* (top-3 risk driver name/percentile) are contextual, not a
    # standalone browsable metric — the metric selector/choropleth expect
    # continuous values, and driver_N is a variable-name string. Same
    # exclusion treatment as sbpi_class until the dashboard renders them
    # explicitly (recommendations-engine dashboard integration).
    indices_csv = tmp_path / "indices.csv"
    indices_csv.write_text(
        "fips,sri,scai,gai,sbpi,sbpi_class,driver_1,driver_1_pctile,driver_2,driver_2_pctile,driver_3,driver_3_pctile\n"
        "36001,50.0,50.0,50.0,50.0,2,smoking_prevalence,90.0,poverty_rate,80.0,pop_density,70.0\n"
    )
    monkeypatch.setattr(build_site_data, "INDICES_CSV", indices_csv)

    master = pd.DataFrame({"fips": ["36001"], "county": ["Albany"], "state": ["NY"]})
    joined = _join_indices(master)

    assert "sbpi_class" not in joined.columns
    for col in ("driver_1", "driver_1_pctile", "driver_2", "driver_2_pctile", "driver_3", "driver_3_pctile"):
        assert col not in joined.columns, f"{col} should be excluded from the dashboard join"
    assert joined.loc[0, "sbpi"] == 50.0
