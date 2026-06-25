# Stroke Burden Index

Identifying high-priority stroke intervention areas in the US by combining a Stroke Vulnerability Index (stroke risk) and a Stroke Care Access Index (treatment availability) at the county level.

**Status:** data gathering — ACS demographics, CDC WONDER stroke mortality, and geographic accessibility (drive time + distance to nearest stroke center) are collected for all 91 NY/NJ/CT counties. SCAI variables and SVI health variables are in progress.

- Project plan and methodology: [docs/plan.md](docs/plan.md)
- Data dictionary and naming conventions: [data/data_dictionary.md](data/data_dictionary.md)
- Live site: https://palism1.github.io/stroke-burden-index/

## Layout

```
docs/        GitHub Pages source (Jekyll, jekyll-theme-cayman)
data/        county-level data files and collection notebooks
  acs_data/                ACS demographics notebook and outputs
  cdcwonder_data/          CDC WONDER stroke mortality notebook and outputs
  geographic_accessibility_data/  stroke center geocoding and accessibility outputs
reference/   crosswalks and reference tables (CT county crosswalk)
src/         analysis pipelines (index construction, modeling)
notebooks/   exploratory work
outputs/     figures, maps, tables
```

`raw/` and `interim/` inside `data/` are gitignored (re-downloadable). Everything else is committed when small.

## Database

For querying across all data sources without manual merges, build the local SQLite database:

```bash
python src/build_db.py
```

This creates `data/stroke_burden.db` (not committed — regenerate locally). Query it from any notebook:

```python
import sqlite3, pandas as pd
con = sqlite3.connect("data/stroke_burden.db")
df = pd.read_sql("SELECT * FROM master", con)
con.close()
```

Available tables: `counties`, `acs`, `mortality`, `geographic`, `cdc_places`, `pop_density`. The `master` view joins all of them on `fips`.

## Running the merge pipeline

Once all data files are in place, run:

```bash
pip install -r requirements.txt
python src/merge.py
```

This produces `data/master.csv` — one row per county with all sources joined and cleaned. `master.csv` is not committed (it is generated). The script prints a summary of row count and any missing values when it runs.

Not all source files are collected yet. The script will still run with what is available; columns from missing sources will show as `NaN` in the output.

### Adding a new data source

When a new file is ready, add one function and one line to `src/merge.py`:

```python
def _load_svi_health() -> pd.DataFrame:
    df = pd.read_csv(DATA / "svi_health.csv", dtype={"fips": str})
    return df.drop(columns=["county", "state"], errors="ignore")
```

Then add `_load_svi_health` to the list in `build_master()`. That's all. The script re-runs and master.csv updates.
