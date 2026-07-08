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
    "data/indices.csv": [
        "fips", "sri", "scai", "gai", "sbpi", "sbpi_class",
        "sri_flag", "scai_flag", "gai_flag",
        "driver_1", "driver_1_pctile", "driver_2", "driver_2_pctile",
        "driver_3", "driver_3_pctile",
    ],
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
def test_sbpi_layer_flags_match_thresholds():
    # sri_flag/scai_flag/gai_flag are the exact three predicates _add_sbpi uses
    # internally to classify critical/high/moderate — persisted so the
    # recommendation copy (which layer tripped Moderate?) doesn't have to
    # reverse-engineer them from sbpi_class or (unreliably) from driver_1,
    # since PC1 aggregates several raw variables and the single most-extreme
    # one doesn't always belong to the index that actually crossed threshold.
    indices, _ = _compute()
    sri, scai, gai = indices["sri"], indices["scai"], indices["gai"]
    assert (indices["sri_flag"] == (sri >= sri.quantile(0.75))).all()
    assert (indices["scai_flag"] == (scai <= scai.quantile(0.25))).all()
    assert (indices["gai_flag"] == (gai <= gai.quantile(0.25))).all()
    # Moderate class guarantees at least one flag; critical guarantees all three.
    moderate = indices["sbpi_class"] == 2
    any_flag = indices["sri_flag"] | indices["scai_flag"] | indices["gai_flag"]
    assert any_flag[moderate].all()
    critical = indices["sbpi_class"] == 4
    all_flags = indices["sri_flag"] & indices["scai_flag"] & indices["gai_flag"]
    assert all_flags[critical].all()


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


# ---------------------------------------------------------------------------
# Top-3 percentile risk drivers (docs/DECISIONS.md 2026-07-07, "per-county
# recommendations engine"). For each county, the 3 raw input variables (across
# all of SRI/SCAI/GAI) that are most extreme in the direction that makes that
# specific variable "bad" for the county — independent of any one index's own
# PCA sign convention.
# ---------------------------------------------------------------------------

def _all_index_variables():
    import compute_indices
    variables = set()
    for cfg in compute_indices.INDEX_CONFIG.values():
        variables.update(cfg["variables"])
    return variables


# _oriented_badness_pct is the orientation-critical piece: `flip` alone isn't
# enough to know a variable's "badness" direction, because SRI's own index
# direction is high=bad while SCAI/GAI's is high=good, so the same flip flag
# means the opposite thing for badness depending on which index it came from.
# These 4 cases cover every combination of flip x bad_when_high.

@pytest.mark.parametrize(
    "flip, bad_when_high, worst_raw_value",
    [
        (False, True, 3),   # SRI-style non-flip var (e.g. smoking_prevalence): high raw = bad
        (True, True, 1),    # SRI-style flip var (e.g. pcnt_bachelors): low raw = bad
        (False, False, 1),  # SCAI-style non-flip var (e.g. hospital_beds_per_100k): low raw = bad
        (True, False, 3),   # SCAI/GAI-style flip var (e.g. pcnt_uninsured, drive_time): high raw = bad
    ],
)
def test_oriented_badness_pct_orientation(flip, bad_when_high, worst_raw_value):
    import compute_indices

    raw = pd.Series([1, 2, 3])
    badness = compute_indices._oriented_badness_pct(raw, flip=flip, bad_when_high=bad_when_high)
    worst_idx = raw[raw == worst_raw_value].index[0]
    assert badness.loc[worst_idx] == badness.max(), (
        f"flip={flip}, bad_when_high={bad_when_high}: expected raw={worst_raw_value} "
        f"to be the worst (highest badness pctile), got {badness.to_dict()}"
    )
    assert badness.between(0, 100).all()


@_needs_master
def test_top_drivers_are_known_variables():
    indices, _ = _compute()
    known = _all_index_variables()
    for i in (1, 2, 3):
        col = indices[f"driver_{i}"]
        assert col.notna().all(), f"driver_{i} has a missing value"
        assert set(col.unique()) <= known, f"driver_{i} contains an unrecognized variable name"


@_needs_master
def test_top_drivers_percentiles_descending_and_in_range():
    indices, _ = _compute()
    for i in (1, 2, 3):
        col = indices[f"driver_{i}_pctile"]
        assert col.notna().all(), f"driver_{i}_pctile has NaN"
        assert (col >= 0).all() and (col <= 100).all(), f"driver_{i}_pctile outside [0, 100]"
    ordered = (
        (indices["driver_1_pctile"] >= indices["driver_2_pctile"])
        & (indices["driver_2_pctile"] >= indices["driver_3_pctile"])
    )
    assert ordered.all(), "driver percentiles are not in descending order for every county"


@_needs_master
def test_top_drivers_worst_gai_county_flags_distance():
    # Clinton (GAI_WORST_FIPS) has the longest drive time/distance nationally
    # under the nearest-any-tier definition — its top-3 drivers should be
    # exactly the distance/time variables, not e.g. a health-prevalence rate.
    indices, _ = _compute()
    row = indices.set_index("fips").loc[GAI_WORST_FIPS]
    drivers = {row["driver_1"], row["driver_2"], row["driver_3"]}
    distance_vars = {
        "drive_time_any", "drive_time_advanced",
        "nearest_stroke_distance_any", "nearest_stroke_distance_advanced",
    }
    assert drivers <= distance_vars, f"expected distance/time drivers, got {drivers}"


@_needs_master
def test_top_drivers_deterministic():
    a, _ = _compute()
    b, _ = _compute()
    driver_cols = [f"driver_{i}{s}" for i in (1, 2, 3) for s in ("", "_pctile")]
    assert (a[driver_cols].astype(str).to_numpy() == b[driver_cols].astype(str).to_numpy()).all()


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
