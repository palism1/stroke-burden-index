"""
Contract tests for every committed county-level data CSV.

The REGISTRY below is the single place to update when a data file gains,
loses, or renames a column — update data/data_dictionary.md in the same PR.
Files are listed explicitly (no globbing) so raw/interim artifacts are never
accidentally checked.

The scai_data.csv entry activates automatically once that file is committed;
until then its test is skipped.
"""

import sys
from pathlib import Path

import pandas as pd
import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from validate_schema import SchemaError, load_spine_fips, validate_schema

# file (relative to repo root) -> exact expected columns
REGISTRY = {
    "data/ny_nj_ct_fips.csv": ["fips", "county", "state"],
    "data/acs_data.csv": [
        "fips", "county", "state", "total_pop", "pcnt_65_plus", "poverty_rate",
        "pcnt_insured", "pcnt_bachelors", "pcnt_low_income",
        "pcnt_middle_class", "pcnt_upper_class",
    ],
    "data/stroke_mortality.csv": [
        "fips", "county", "state",
        "acute_stroke_mortality_per_100k", "sequelae_stroke_mortality_per_100k",
    ],
    "data/cdcplaces_data.csv": [
        "fips", "county", "state", "binge_drinking_prevalence",
        "smoking_prevalence", "physical_inactivity", "hypertension_prevalence",
        "high_cholesterol_prevalence", "diabetes_prevalence",
        "obesity_prevalence", "stroke_prevalence",
    ],
    "data/pop_density.csv": ["fips", "county", "state", "pop_density"],
    "data/geographic_accessibility_data/geographic_stroke_accessibility.csv": [
        "fips", "county", "state", "drive_time_min", "drive_time_advanced",
        "nearest_stroke_distance", "nearest_stroke_distance_advanced",
    ],
    # Not collected yet — spec from data/scai_data/README.md. Skipped until it lands.
    "data/scai_data/scai_data.csv": [
        "fips", "hospitals_per_100k", "hospital_beds_per_100k",
        "pcp_per_100k", "neurologists_per_100k", "stroke_centers_per_100k",
    ],
}


@pytest.mark.parametrize("rel_path", REGISTRY)
def test_data_file_matches_contract(rel_path):
    path = REPO_ROOT / rel_path
    if not path.exists():
        pytest.skip(f"{rel_path} not collected yet")
    df = pd.read_csv(path, dtype={"fips": str})
    validate_schema(df, rel_path, expected_columns=REGISTRY[rel_path])


# validate_schema unit tests (synthetic frames)

SPINE_FIPS = sorted(load_spine_fips())


def _good_frame(n=91):
    return pd.DataFrame({"fips": SPINE_FIPS[:n], "some_rate": 1.0})


def test_good_frame_passes():
    validate_schema(_good_frame(), "good", expect_rows=91)


def test_expected_columns_enforced():
    validate_schema(_good_frame(), "good", expected_columns=["fips", "some_rate"])
    with pytest.raises(SchemaError, match="missing expected columns"):
        validate_schema(_good_frame(), "bad", expected_columns=["fips", "some_rate", "other"])
    with pytest.raises(SchemaError, match="unexpected columns"):
        validate_schema(_good_frame(), "bad", expected_columns=["fips"])


def test_int_fips_fails():
    df = _good_frame()
    df["fips"] = df["fips"].astype(int)
    with pytest.raises(SchemaError, match="must be read as string"):
        validate_schema(df, "bad")


def test_unpadded_fips_fails():
    df = _good_frame()
    df.loc[0, "fips"] = "9001"
    with pytest.raises(SchemaError, match="not zero-padded"):
        validate_schema(df, "bad")


def test_fips_outside_spine_fails():
    df = _good_frame()
    df.loc[0, "fips"] = "99999"
    with pytest.raises(SchemaError, match="not in the 91-county spine"):
        validate_schema(df, "bad")


def test_duplicate_fips_fails():
    df = _good_frame()
    df.loc[1, "fips"] = df.loc[0, "fips"]
    with pytest.raises(SchemaError, match="duplicate fips"):
        validate_schema(df, "bad")


def test_wrong_row_count_fails():
    with pytest.raises(SchemaError, match="expected 91 rows, got 5"):
        validate_schema(_good_frame(5), "bad", expect_rows=91)


def test_row_count_check_skippable():
    validate_schema(_good_frame(5), "ok", expect_rows=None)


def test_non_snake_case_column_fails():
    df = _good_frame().rename(columns={"some_rate": "Some Rate"})
    with pytest.raises(SchemaError, match="snake_case"):
        validate_schema(df, "bad")


def test_missing_fips_column_fails():
    df = _good_frame().drop(columns=["fips"])
    with pytest.raises(SchemaError, match="no fips column"):
        validate_schema(df, "bad", expect_rows=None)


def test_error_names_the_file():
    with pytest.raises(SchemaError, match="^myfile.csv:"):
        validate_schema(_good_frame(5), "myfile.csv")
