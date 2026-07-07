"""
Compute the three stroke-burden indices — SRI, SCAI, GAI — and write the
canonical result to data/indices.csv.

Run whenever the underlying data changes (after src/merge.py):
    python src/compute_indices.py

This is the CI-enforced, single source of truth for the index scores. The
scores used to live only inside `notebooks/Calculating Indices.ipynb`; this
script reproduces that notebook's committed outputs exactly (see the EVR
regression test in tests/test_data_contracts.py) so the numbers can be
committed, joined into the database, and served without re-running a notebook.

Data source
-----------
Reads data/master.csv (produced by src/merge.py) with the same
float_precision="round_trip" convention the other pipelines use, so the same
raw values feed PCA on every machine. The indices derive FROM master; nothing
here writes back into master — the data DAG stays acyclic.

Output
------
data/indices.csv with columns exactly: fips, sri, scai, gai
  - 91 rows, one per county, keyed by fips (zero-padded 5-char strings)
  - scores are 0-100 floats rounded to 4 decimal places

The rounding is deliberate. PC1 comes from an SVD whose last ~1e-12 digits move
between BLAS builds; rounding to 4 dp keeps data/indices.csv byte-identical
across machines so CI's `git diff --exit-code` staleness gate can't flake.

The index definitions (which variables, which flips, which transforms) are
settled team decisions logged in docs/DECISIONS.md — see the CONFIG block below,
where each choice is annotated with the decision date it implements.
"""

from pathlib import Path
import sys

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "src"))
from index_pipeline import build_index  # noqa: E402

DATA = REPO_ROOT / "data"
MASTER = DATA / "master.csv"
OUT = DATA / "indices.csv"

# Scores are rounded to this many decimals before writing (see module docstring:
# byte-stability of the committed CSV across BLAS builds).
SCORE_DECIMALS = 4


# ---------------------------------------------------------------------------
# CONFIG — index definitions. One entry per index; each field mirrors a
# build_index() argument (variables / flip / transforms) exactly, so the
# canonical computation is auditable against docs/DECISIONS.md line by line.
#
# `build_index` orients each index automatically (it anchors PC1's sign to the
# majority direction of the aligned variables and raises if that direction is
# ambiguous), so there is no manual sign/anchor argument to configure here —
# orientation is expressed entirely through `flip`. Put every variable whose
# HIGH raw value points AGAINST the index direction in `flip`.
# ---------------------------------------------------------------------------
INDEX_CONFIG = {
    # SRI — Stroke Risk Index (higher = higher stroke risk).
    # Excludes pcnt_insured: that variable belongs to SCAI, not SRI
    #   (docs/DECISIONS.md 2026-07-05, "pcnt_insured belongs to SCAI, not SRI").
    # pcnt_bachelors is protective (more education -> lower risk), so it flips.
    # pop_density is heavily right-skewed, so it gets log1p (rule: |skew| > 2
    #   heavy tails should not dominate PC1 — the same team PCA rule the GAI and
    #   insurance decisions cite).
    "sri": {
        "variables": [
            "pop_density",
            "pcnt_65_plus",
            "poverty_rate",
            "pcnt_low_income",
            "pcnt_bachelors",
            "smoking_prevalence",
            "obesity_prevalence",
            "diabetes_prevalence",
            "physical_inactivity",
            "hypertension_prevalence",
            "high_cholesterol_prevalence",
            "binge_drinking_prevalence",
            "stroke_prevalence",
        ],
        "flip": ["pcnt_bachelors"],
        "transforms": {"pop_density": "log1p"},
    },
    # SCAI — Stroke Care Access Index (higher = better access).
    # hospitals_per_100k and stroke_centers_per_100k are EXCLUDED from the index
    #   (they stay in the EDA / scai_data.csv) — docs/DECISIONS.md 2026-07-06,
    #   "hospitals_per_100k and stroke_centers_per_100k dropped from the SCAI index".
    # Insurance enters as the uninsured rate: pcnt_uninsured = 100 - pcnt_insured,
    #   then log1p, then flip (higher uninsured = worse access) —
    #   docs/DECISIONS.md 2026-07-06, "pcnt_insured ... recast as the uninsured
    #   rate with log1p + flip". pcnt_uninsured is derived in memory below; it is
    #   never written to a data file.
    # PENDING TEAM VOTE: neurologists_per_100k has |skew| ~3.21 (> 2) and gets NO
    #   transform here. The team's PCA rule ("rule over metric") would log1p it,
    #   but this is NOT YET DECIDED — see docs/DECISIONS.md "Open —
    #   neurologists_per_100k exceeds the skew rule inside SCAI". Leaving it
    #   untransformed matches the notebook's committed output; it will surface in
    #   the high_skew diagnostic below (that's expected). If the vote lands, add
    #   `"neurologists_per_100k": "log1p"` to transforms.
    "scai": {
        "variables": [
            "hospital_beds_per_100k",
            "pcp_per_100k",
            "neurologists_per_100k",
            "pcnt_uninsured",  # derived: 100 - pcnt_insured (see below)
        ],
        "flip": ["pcnt_uninsured"],
        "transforms": {"pcnt_uninsured": "log1p"},
    },
    # GAI — Geographic Accessibility Index (higher = better access).
    # All four drive-time/distance variables get log1p and all four flip
    #   (lower time/distance = closer = better access) — docs/DECISIONS.md
    #   2026-07-05, "GAI uses log1p transforms on all four
    #   drive-time/distance variables". EVR drops slightly under log1p (0.82 raw
    #   -> 0.77) and the team took the rule over the metric.
    "gai": {
        "variables": [
            "drive_time_min",
            "drive_time_advanced",
            "nearest_stroke_distance",
            "nearest_stroke_distance_advanced",
        ],
        "flip": [
            "drive_time_min",
            "drive_time_advanced",
            "nearest_stroke_distance",
            "nearest_stroke_distance_advanced",
        ],
        "transforms": {
            "drive_time_min": "log1p",
            "drive_time_advanced": "log1p",
            "nearest_stroke_distance": "log1p",
            "nearest_stroke_distance_advanced": "log1p",
        },
    },
}


def _read(path) -> pd.DataFrame:
    # float_precision="round_trip" — correctly rounded float parsing, identical
    # across pandas versions and platforms (matches merge.py / build_db.py), so
    # PCA sees the same raw values everywhere and the output stays byte-stable.
    return pd.read_csv(path, dtype={"fips": str}, float_precision="round_trip")


def _load_master() -> pd.DataFrame:
    df = _read(MASTER)
    # Recast insurance coverage as the uninsured rate in memory only. Higher
    # uninsured = worse access; it is right-skewed, so CONFIG applies log1p and a
    # flip (docs/DECISIONS.md 2026-07-06). This column is never written anywhere
    # permanent — it exists solely as a SCAI input.
    df["pcnt_uninsured"] = 100 - df["pcnt_insured"]
    return df


def compute_indices(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Return (indices_df, results) where indices_df has columns fips,sri,scai,gai.

    `results` maps index name -> IndexResult, for the terminal summary and tests.
    """
    out = df[["fips"]].copy()
    results = {}
    for name, cfg in INDEX_CONFIG.items():
        result = build_index(
            df,
            cfg["variables"],
            flip=cfg.get("flip", ()),
            transforms=cfg.get("transforms"),
            name=name,
        )
        # Round before storing so the committed CSV is byte-stable across BLAS
        # builds (see module docstring).
        out[name] = result.scores.round(SCORE_DECIMALS).to_numpy()
        results[name] = result
    return out, results


def _print_summary(results: dict) -> None:
    # Terminal summary in merge.py's style: per index, EVR + top loadings + any
    # high_skew flags. neurologists_per_100k is expected under SCAI (pending
    # vote) — the flag is a useful reminder, not an error.
    print("index summary (PC1):")
    for name, res in results.items():
        print(f"  {name}: explained variance = {res.explained_variance_ratio:.4f}")
        top = res.loadings.reindex(res.loadings.abs().sort_values(ascending=False).index)
        top_str = ", ".join(f"{v}={w:+.3f}" for v, w in top.head(3).items())
        print(f"    top loadings: {top_str}")
        if res.high_skew:
            print(f"    high skew (|skew| > 2, untransformed): {', '.join(res.high_skew)}")


def main() -> None:
    df = _load_master()
    indices, results = compute_indices(df)

    indices.to_csv(OUT, index=False)

    out_label = OUT.relative_to(REPO_ROOT) if OUT.is_relative_to(REPO_ROOT) else OUT
    print(f"wrote {out_label}  ({len(indices)} rows, {len(indices.columns)} columns)")
    _print_summary(results)


if __name__ == "__main__":
    main()
