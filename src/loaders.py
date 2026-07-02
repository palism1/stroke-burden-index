"""
Shared data loaders for the merge pipeline (src/merge.py) and the database
builder (src/build_db.py). Both import from here — add new sources once,
in this file, not in both places.

Every loader:
  - reads fips as a zero-padded string (dtype={"fips": str})
  - runs the CT validation gate on the file it just read, so a source that
    arrives in planning-region codes fails loudly at load time instead of
    silently dropping CT rows in a later left join
  - drops county/state columns (the spine is the only source of those;
    join on fips, never on county or state)

To add a new source: write a load_<name>() that calls _read_gated() and
drops county/state, then register it in SOURCE_LOADERS at the bottom.
"""

from pathlib import Path
import sys

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "reference" / "ct_crosswalk"))
from validate_ct_codes import validate_ct_codes, CTCodeError  # noqa: E402,F401

DATA = REPO_ROOT / "data"


def _strip_county_suffix(series: pd.Series) -> pd.Series:
    return series.str.replace(r"\s+County$", "", regex=True)


def _read_gated(path: Path) -> pd.DataFrame:
    """Read a source CSV with fips as string and run the CT gate on it."""
    df = pd.read_csv(path, dtype={"fips": str})
    validate_ct_codes(df, fips_col="fips")
    return df


def load_spine() -> pd.DataFrame:
    """91-county FIPS reference — the join backbone."""
    df = _read_gated(DATA / "ny_nj_ct_fips.csv")
    df["county"] = _strip_county_suffix(df["county"])
    return df[["fips", "county", "state"]]


def load_acs() -> pd.DataFrame:
    return _read_gated(DATA / "acs_data.csv").drop(columns=["county", "state"], errors="ignore")


def load_mortality() -> pd.DataFrame:
    return _read_gated(DATA / "stroke_mortality.csv").drop(columns=["county", "state"], errors="ignore")


def load_geographic() -> pd.DataFrame:
    df = _read_gated(DATA / "geographic_accessibility_data" / "geographic_stroke_accessibility.csv")
    return df.drop(columns=["county", "state"], errors="ignore")


def load_cdc_places() -> pd.DataFrame:
    return _read_gated(DATA / "cdcplaces_data.csv").drop(columns=["county", "state"], errors="ignore")


def load_pop_density() -> pd.DataFrame:
    return _read_gated(DATA / "pop_density.csv").drop(columns=["county", "state"], errors="ignore")


def load_scai() -> pd.DataFrame:
    # Expected columns: fips, hospitals_per_100k, hospital_beds_per_100k,
    #                   pcp_per_100k, neurologists_per_100k, stroke_centers_per_100k
    return _read_gated(DATA / "scai_data.csv").drop(columns=["county", "state"], errors="ignore")


# Ordered registry of non-spine sources. merge.py joins these onto the spine
# in this order; build_db.py makes one table per entry. Both skip an entry
# whose file is not on disk yet (and say so), so registering a source before
# its data lands is safe — scai below is exactly that.
SOURCE_LOADERS = {
    "acs": load_acs,
    "mortality": load_mortality,
    "geographic": load_geographic,
    "cdc_places": load_cdc_places,
    "pop_density": load_pop_density,
    "scai": load_scai,
}
