"""
Merge all county-level data sources into one master table.

Loaders are shared with src/build_db.py and live in src/loaders.py. Every
loader runs the CT validation gate on its own file, so a source arriving in
planning-region codes fails loudly at load time instead of silently dropping
CT rows in the join. Sources whose file is not on disk yet (e.g. scai) are
skipped with a printed note.

Cleaning applied at load time (per data/data_dictionary.md):
  - county: strips " County" suffix from the FIPS spine
  - county/state are dropped from every non-spine source; join on fips only

Output: data/master.csv — one row per county (91 total), keyed by fips.

To add a new source: add a load_<name>() to src/loaders.py and register it
in SOURCE_LOADERS there. That's it — merge and build_db both pick it up.
"""

from pathlib import Path
import sys

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import loaders  # noqa: E402
from loaders import SOURCE_LOADERS, load_spine, _strip_county_suffix  # noqa: E402,F401

REPO_ROOT = loaders.REPO_ROOT


def build_master() -> pd.DataFrame:
    master = load_spine()

    skipped = []
    for name, loader in SOURCE_LOADERS.items():
        try:
            df = loader()
        except FileNotFoundError:
            skipped.append(name)
            continue
        master = master.merge(df, on="fips", how="left")

    out = loaders.DATA / "master.csv"
    master.to_csv(out, index=False)

    try:
        shown = out.relative_to(REPO_ROOT)
    except ValueError:
        shown = out
    print(f"wrote {shown}  ({len(master)} rows, {len(master.columns)} columns)")
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
