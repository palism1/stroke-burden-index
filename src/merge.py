"""
Merge all county-level data sources into one master table.

Cleaning applied at merge time (per data/data_dictionary.md):
  - county: strips " County" suffix from acs_data and stroke_mortality
  - state:  converts full names to 2-letter abbreviations in geographic file

Output: data/master.csv — one row per county (91 total), keyed by fips.

To add a new source: write a load_<name>() function that returns a DataFrame
with 'fips' as a string column, drop county/state if present, then add one
loader to the list in build_master(). That's it.
"""

from pathlib import Path
import sys
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "reference" / "ct_crosswalk"))
from validate_ct_codes import validate_ct_codes, CTCodeError  # noqa: E402

DATA = REPO_ROOT / "data"

_STATE_NAME_TO_ABBR = {
    "New York": "NY",
    "New Jersey": "NJ",
    "Connecticut": "CT",
}


def _strip_county_suffix(series: pd.Series) -> pd.Series:
    return series.str.replace(r"\s+County$", "", regex=True)


def _load_spine() -> pd.DataFrame:
    """91-county FIPS reference — the join backbone."""
    df = pd.read_csv(DATA / "ny_nj_ct_fips.csv", dtype={"fips": str})
    df["county"] = _strip_county_suffix(df["county"])
    return df[["fips", "county", "state"]]


def _load_acs() -> pd.DataFrame:
    df = pd.read_csv(DATA / "acs_data.csv", dtype={"fips": str})
    return df.drop(columns=["county", "state"])


def _load_mortality() -> pd.DataFrame:
    df = pd.read_csv(DATA / "stroke_mortality.csv", dtype={"fips": str})
    return df.drop(columns=["county", "state"])


def _load_geographic() -> pd.DataFrame:
    df = pd.read_csv(
        DATA / "geographic_accessibility_data" / "geographic_stroke_accessibility.csv",
        dtype={"fips": str},
    )
    df["state"] = df["state"].map(_STATE_NAME_TO_ABBR)
    return df.drop(columns=["county", "state"])


def _load_cdc_places() -> pd.DataFrame:
    df = pd.read_csv(DATA / "cdcplaces_data.csv", dtype={"fips": str})
    return df.drop(columns=["county", "state"], errors="ignore")


def _load_pop_density() -> pd.DataFrame:
    df = pd.read_csv(DATA / "pop_density.csv", dtype={"fips": str})
    return df.drop(columns=["county", "state"], errors="ignore")


def _load_scai() -> pd.DataFrame | None:
    """SCAI is still being collected — returns None until the file lands.

    Expected columns: fips, hospitals_per_100k, hospital_beds_per_100k,
    pcp_per_100k, neurologists_per_100k, stroke_centers_per_100k
    (see data/scai_data/README.md).
    """
    path = DATA / "scai_data" / "scai_data.csv"
    if not path.exists():
        return None
    df = pd.read_csv(path, dtype={"fips": str})
    return df.drop(columns=["county", "state"], errors="ignore")


# ---------------------------------------------------------------------------
# Add new sources here when they land. Pattern:
#   def _load_<name>() -> pd.DataFrame:
#       df = pd.read_csv(DATA / "<file>.csv", dtype={"fips": str})
#       return df.drop(columns=["county", "state"], errors="ignore")
# A loader may return None to signal its file isn't collected yet.
# ---------------------------------------------------------------------------


def build_master() -> pd.DataFrame:
    spine = _load_spine()
    validate_ct_codes(spine, fips_col="fips")

    master = spine
    skipped = []
    for loader in [_load_acs, _load_mortality, _load_geographic, _load_cdc_places, _load_pop_density, _load_scai]:
        df = loader()
        if df is None:
            skipped.append(loader.__name__.removeprefix("_load_"))
            continue
        master = master.merge(df, on="fips", how="left")

    out = DATA / "master.csv"
    master.to_csv(out, index=False)

    out_label = out.relative_to(REPO_ROOT) if out.is_relative_to(REPO_ROOT) else out
    print(f"wrote {out_label}  ({len(master)} rows, {len(master.columns)} columns)")
    if skipped:
        print(f"skipped (file not found): {', '.join(skipped)}")
    missing = master.isnull().sum()
    missing = missing[missing > 0]
    if not missing.empty:
        print("columns with missing values:")
        for col, n in missing.items():
            print(f"  {col}: {n} missing")
    else:
        print("no missing values")

    return master


if __name__ == "__main__":
    build_master()
