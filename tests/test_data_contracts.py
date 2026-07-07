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
    # Computed index scores (src/compute_indices.py). Skipped until it lands.
    "data/indices.csv": ["fips", "sri", "scai", "gai", "sbpi", "sbpi_class"],
}


@pytest.mark.parametrize("rel_path", REGISTRY)
def test_data_file_matches_contract(rel_path):
    path = REPO_ROOT / rel_path
    if not path.exists():
        pytest.skip(f"{rel_path} not collected yet")
    df = pd.read_csv(path, dtype={"fips": str})
    validate_schema(df, rel_path, expected_columns=REGISTRY[rel_path])


# ---------------------------------------------------------------------------
# Index computation (src/compute_indices.py)
#
# The index scores used to live only in notebooks/Calculating Indices.ipynb;
# compute_indices.py is now the canonical source. These tests pin its output to
# the notebook's committed numbers so the two can't silently drift.
# ---------------------------------------------------------------------------

# PC1 explained-variance ratios from the notebook's committed outputs
# (notebooks/Calculating Indices.ipynb). compute_indices.py must reproduce them.
# Updated 2026-07-07 after the team decisions landed (neurologists log1p,
# Hunterdon beds corrected, GAI nearest-any-tier) — see docs/DECISIONS.md.
NOTEBOOK_EVR = {
    "sri": 0.5223875266272116,
    "scai": 0.5490574193488794,
    "gai": 0.8217631411124711,
}
# The county at each end of GAI (higher = better geographic access). Under the
# nearest-any-tier definition (2026-07-07) Manhattan takes the top spot — its
# comprehensive center is ~2.5 min from the population centroid.
GAI_BEST_FIPS = "36061"   # New York (Manhattan) — max GAI (100)
GAI_WORST_FIPS = "36019"  # Clinton — min GAI (0)

_MASTER_EXISTS = (REPO_ROOT / "data" / "master.csv").exists()
_needs_master = pytest.mark.skipif(
    not _MASTER_EXISTS, reason="data/master.csv not built yet (run src/merge.py)"
)


def _compute():
    """Run compute_indices in-process, returning (indices_df, results)."""
    import compute_indices  # imported here so collection never depends on it

    df = compute_indices._load_master()
    return compute_indices.compute_indices(df)


@_needs_master
def test_index_evr_matches_notebook():
    _, results = _compute()
    for name, expected in NOTEBOOK_EVR.items():
        got = results[name].explained_variance_ratio
        assert abs(got - expected) < 1e-3, f"{name} EVR {got} != notebook {expected}"


@_needs_master
def test_index_scores_in_range_and_finite():
    indices, _ = _compute()
    for name in ("sri", "scai", "gai"):
        col = indices[name]
        assert col.notna().all(), f"{name} has NaN"
        assert (col >= 0).all() and (col <= 100).all(), f"{name} outside [0, 100]"


@_needs_master
def test_sbpi_score_and_class():
    indices, _ = _compute()
    sri, scai, gai = indices["sri"], indices["scai"], indices["gai"]
    expected = (0.5 * sri + 0.3 * (100 - scai) + 0.2 * (100 - gai)).round(4)
    assert (indices["sbpi"] == expected).all(), "sbpi != 50/30/20 weighted deficits"
    assert indices["sbpi"].between(0, 100).all()
    assert set(indices["sbpi_class"].unique()) <= {1, 2, 3, 4}
    # Critical class must be exactly the triple-threshold counties.
    crit = (sri >= sri.quantile(0.75)) & (scai <= scai.quantile(0.25)) & (gai <= gai.quantile(0.25))
    assert (indices.loc[crit, "sbpi_class"] == 4).all()
    assert (indices.loc[~crit, "sbpi_class"] < 4).all()


@_needs_master
def test_index_computation_is_deterministic(tmp_path):
    import compute_indices

    df = compute_indices._load_master()
    a, _ = compute_indices.compute_indices(df)
    b, _ = compute_indices.compute_indices(df)
    first = tmp_path / "a.csv"
    second = tmp_path / "b.csv"
    a.to_csv(first, index=False)
    b.to_csv(second, index=False)
    assert first.read_bytes() == second.read_bytes(), "two runs differ byte-for-byte"


@_needs_master
def test_gai_best_and_worst_county():
    indices, _ = _compute()
    gai = indices.set_index("fips")["gai"]
    assert gai.idxmax() == GAI_BEST_FIPS, f"best GAI is {gai.idxmax()}, expected {GAI_BEST_FIPS}"
    assert gai.idxmin() == GAI_WORST_FIPS, f"worst GAI is {gai.idxmin()}, expected {GAI_WORST_FIPS}"


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
