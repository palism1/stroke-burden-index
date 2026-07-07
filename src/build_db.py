"""
Build stroke_burden.db — a SQLite database containing all cleaned county-level data.

Run this whenever source files are updated:
    python src/build_db.py

The database is not committed to the repo (see .gitignore). Anyone on the team
can regenerate it locally by running this script.

Tables
------
counties        Spine: 91 counties with fips, county name, state
acs             ACS demographic and socioeconomic variables
mortality       CDC WONDER stroke mortality rates
geographic      Drive time and distance to nearest stroke center
cdc_places      CDC PLACES health prevalence variables
pop_density     Population density
scai            Stroke-care supply counts (hospital beds, PCPs, neurologists, ...)
indices         Computed index scores: sri, scai, gai (NOT in the master view —
                they derive from master; join explicitly on fips)

Querying from a notebook
------------------------
    import sqlite3, pandas as pd
    con = sqlite3.connect("data/stroke_burden.db")

    # All data joined
    df = pd.read_sql("SELECT * FROM master", con)

    # Just geographic + mortality
    df = pd.read_sql('''
        SELECT c.fips, c.county, c.state,
               m.acute_stroke_mortality_per_100k,
               g.drive_time_advanced
        FROM counties c
        JOIN mortality m USING (fips)
        JOIN geographic g USING (fips)
    ''', con)

    con.close()
"""

from pathlib import Path
import sys
import sqlite3
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "reference" / "ct_crosswalk"))
from validate_ct_codes import validate_ct_codes  # noqa: E402

DATA = REPO_ROOT / "data"
DB_PATH = DATA / "stroke_burden.db"

_STATE_NAME_TO_ABBR = {
    "New York": "NY",
    "New Jersey": "NJ",
    "Connecticut": "CT",
}


def _strip_county_suffix(series: pd.Series) -> pd.Series:
    return series.str.replace(r"\s+County$", "", regex=True)


def _read(path) -> pd.DataFrame:
    # float_precision="round_trip" — correctly rounded float parsing,
    # identical across pandas versions and platforms (see merge.py).
    return pd.read_csv(path, dtype={"fips": str}, float_precision="round_trip")


def _load_spine() -> pd.DataFrame:
    df = _read(DATA / "ny_nj_ct_fips.csv")
    df["county"] = _strip_county_suffix(df["county"])
    return df[["fips", "county", "state"]]


def _load_acs() -> pd.DataFrame:
    df = _read(DATA / "acs_data.csv")
    return df.drop(columns=["county", "state"])


def _load_mortality() -> pd.DataFrame:
    df = _read(DATA / "stroke_mortality.csv")
    return df.drop(columns=["county", "state"])


def _load_geographic() -> pd.DataFrame:
    df = _read(DATA / "geographic_accessibility_data" / "geographic_stroke_accessibility.csv")
    df["state"] = df["state"].map(_STATE_NAME_TO_ABBR)
    return df.drop(columns=["county", "state"])


def _load_cdc_places() -> pd.DataFrame | None:
    path = DATA / "cdcplaces_data.csv"
    if not path.exists():
        return None
    df = _read(path)
    return df.drop(columns=["county", "state"], errors="ignore")


def _load_pop_density() -> pd.DataFrame | None:
    path = DATA / "pop_density.csv"
    if not path.exists():
        return None
    df = _read(path)
    return df.drop(columns=["county", "state"], errors="ignore")


def _load_scai() -> pd.DataFrame | None:
    # Expected columns: fips, hospitals_per_100k, hospital_beds_per_100k,
    #                   pcp_per_100k, neurologists_per_100k, stroke_centers_per_100k
    # (see data/scai_data/README.md)
    path = DATA / "scai_data" / "scai_data.csv"
    if not path.exists():
        return None
    df = _read(path)
    return df.drop(columns=["county", "state"], errors="ignore")


def _load_indices() -> pd.DataFrame | None:
    # The computed index scores: fips, sri, scai, gai (see src/compute_indices.py).
    # Regenerate with `python src/compute_indices.py` after a data change.
    path = DATA / "indices.csv"
    if not path.exists():
        return None
    return _read(path)


# Add new loaders here following the same pattern.


def build_db() -> None:
    if DB_PATH.exists():
        DB_PATH.unlink()

    con = sqlite3.connect(DB_PATH)

    spine = _load_spine()
    validate_ct_codes(spine, fips_col="fips")

    spine.to_sql("counties", con, index=False, if_exists="replace")

    optional_tables = {
        "acs": _load_acs,
        "mortality": _load_mortality,
        "geographic": _load_geographic,
        "cdc_places": _load_cdc_places,
        "pop_density": _load_pop_density,
        "scai": _load_scai,
        "indices": _load_indices,
    }

    # Tables loaded for querying but kept OUT of the master view. The index
    # scores derive FROM master (src/compute_indices.py reads master.csv), so
    # folding them back into master would make the data DAG cyclic — join
    # `indices` explicitly when you want scores alongside their inputs.
    VIEW_EXCLUDED = {"indices"}

    loaded = []
    skipped = []
    for table_name, loader in optional_tables.items():
        df = loader()
        if df is None:
            skipped.append(table_name)
            continue
        df.to_sql(table_name, con, index=False, if_exists="replace")
        loaded.append(table_name)

    view_tables = [t for t in loaded if t not in VIEW_EXCLUDED]

    # Build a master view joining everything that is available
    join_clauses = "\n    ".join(
        f"LEFT JOIN {t} USING (fips)" for t in view_tables if t != "counties"
    )
    # Exclude fips from joined tables to avoid duplicate columns in the view
    joined_columns = []
    for t in view_tables:
        df = con.execute(f"PRAGMA table_info({t})").fetchall()
        cols = [row[1] for row in df if row[1] != "fips"]
        joined_columns.extend(f"{t}.{c}" for c in cols)

    master_sql = f"""
    CREATE VIEW IF NOT EXISTS master AS
    SELECT c.fips, c.county, c.state,
           {', '.join(joined_columns)}
    FROM counties c
    {join_clauses}
    """
    con.execute(master_sql)
    con.commit()

    row_count = con.execute("SELECT COUNT(*) FROM master").fetchone()[0]
    col_count = len(con.execute("SELECT * FROM master LIMIT 1").description)

    con.close()

    print(f"wrote {DB_PATH.relative_to(REPO_ROOT)}")
    print(f"tables: {', '.join(['counties'] + loaded)}")
    if skipped:
        print(f"skipped (file not found): {', '.join(skipped)}")
    print(f"master view: {row_count} rows, {col_count} columns")


if __name__ == "__main__":
    build_db()
