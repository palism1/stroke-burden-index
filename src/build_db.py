"""
Build stroke_burden.db — a SQLite database containing all cleaned county-level data.

Run this whenever source files are updated:
    python src/build_db.py

The database is not committed to the repo (see .gitignore). Anyone on the team
can regenerate it locally by running this script.

Loaders are shared with src/merge.py and live in src/loaders.py — add new
sources there, and this script picks them up automatically. Every loader runs
the CT validation gate on its own file, so a source in planning-region codes
fails loudly instead of producing blank CT rows.

Tables
------
counties        Spine: 91 counties with fips, county name, state
acs             ACS demographic and socioeconomic variables
mortality       CDC WONDER stroke mortality rates
geographic      Drive time and distance to nearest stroke center
cdc_places      CDC PLACES health prevalence variables
pop_density     Population density
scai            Hospitals, providers, stroke centers per capita (once collected)

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
import sqlite3
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
import loaders  # noqa: E402
from loaders import SOURCE_LOADERS, load_spine  # noqa: E402

REPO_ROOT = loaders.REPO_ROOT
DB_PATH = loaders.DATA / "stroke_burden.db"


def build_db() -> None:
    if DB_PATH.exists():
        DB_PATH.unlink()

    con = sqlite3.connect(DB_PATH)

    spine = load_spine()
    spine.to_sql("counties", con, index=False, if_exists="replace")

    loaded = []
    skipped = []
    for table_name, loader in SOURCE_LOADERS.items():
        try:
            df = loader()
        except FileNotFoundError:
            skipped.append(table_name)
            continue
        df.to_sql(table_name, con, index=False, if_exists="replace")
        loaded.append(table_name)

    # Build a master view joining everything that is available.
    # Exclude fips from joined tables to avoid duplicate columns in the view.
    joined_columns = []
    for t in loaded:
        rows = con.execute(f"PRAGMA table_info({t})").fetchall()
        cols = [row[1] for row in rows if row[1] != "fips"]
        joined_columns.extend(f"{t}.{c}" for c in cols)

    select_cols = ["c.fips", "c.county", "c.state"] + joined_columns
    join_clauses = "\n    ".join(f"LEFT JOIN {t} USING (fips)" for t in loaded)

    master_sql = f"""
    CREATE VIEW IF NOT EXISTS master AS
    SELECT {', '.join(select_cols)}
    FROM counties c
    {join_clauses}
    """
    con.execute(master_sql)
    con.commit()

    row_count = con.execute("SELECT COUNT(*) FROM master").fetchone()[0]
    col_count = len(con.execute("SELECT * FROM master LIMIT 1").description)

    con.close()

    try:
        shown = DB_PATH.relative_to(REPO_ROOT)
    except ValueError:
        shown = DB_PATH
    print(f"wrote {shown}")
    print(f"tables: {', '.join(['counties'] + loaded)}")
    if skipped:
        print(f"skipped (file not found): {', '.join(skipped)}")
    print(f"master view: {row_count} rows, {col_count} columns")


if __name__ == "__main__":
    build_db()
