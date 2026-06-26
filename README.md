# Stroke Burden Index

Identifying high-priority stroke intervention areas in the US by combining a Stroke Vulnerability Index (stroke risk) and a Stroke Care Access Index (treatment availability) at the county level.

**Status:** data collection nearly complete. ACS demographics, CDC WONDER stroke mortality, CDC PLACES health prevalence, population density, and geographic accessibility (drive time + distance to nearest stroke center) are collected for all 91 NY/NJ/CT counties. SCAI variables (hospitals, physicians, stroke centers per capita) are in progress. Geographic analysis and EDA are underway.

- Project plan and methodology: [docs/plan.md](docs/plan.md)
- Data dictionary and naming conventions: [data/data_dictionary.md](data/data_dictionary.md)
- Live site: https://palism1.github.io/stroke-burden-index/

## Layout

```
docs/        GitHub Pages source (Jekyll, jekyll-theme-cayman)
data/        county-level data files and collection notebooks
  acs_data/                        ACS demographics notebook and outputs
  cdcwonder_data/                  CDC WONDER stroke mortality notebook and outputs
  cdcplaces_data/                  CDC PLACES health prevalence notebook and outputs
  pop_density_data/                population density notebook and outputs
  geographic_accessibility_data/   stroke center geocoding and accessibility outputs
reference/   crosswalks and reference tables (CT county crosswalk)
src/         analysis pipelines (merge, database)
tests/       test suite for SWE pipeline code
geographic accessibility analysis/  mapping and EDA notebooks (geographic access)
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

Available tables: `counties`, `acs`, `mortality`, `geographic`, `cdc_places`, `pop_density`. `scai` will be added once that data is merged. The `master` view joins all loaded tables on `fips`.

## Running the merge pipeline

```bash
pip install -r requirements.txt
python src/merge.py
```

This produces `data/master.csv` — one row per county (91 total) with all sources joined and cleaned. `master.csv` is not committed (it is generated). The script prints a summary of row count and any missing values when it runs.

### Adding a new data source

Add one function and one line to `src/merge.py` and the same to `src/build_db.py`:

```python
def _load_scai() -> pd.DataFrame:
    df = pd.read_csv(DATA / "scai_data.csv", dtype={"fips": str})
    return df.drop(columns=["county", "state"], errors="ignore")
```

Then add the loader to the list in `build_master()` (merge.py) and to `optional_tables` (build_db.py).

## Tests

```bash
python -m pytest tests/ -q
```

19 tests covering the CT validation gate and the merge pipeline. All must pass before merging any changes to the pipeline or data files.
