# Stroke Burden Index

Identifying high-priority stroke intervention areas across the United States by combining a **Stroke Vulnerability Index** (community stroke risk) and a **Stroke Care Access Index** (treatment availability) at the county level into a single **Stroke Burden Priority Index**.

**Live site:** [palism1.github.io/stroke-burden-index](https://palism1.github.io/stroke-burden-index/)

**Status:** Data collection is nearly complete for all 91 NY/NJ/CT counties. ACS demographics, CDC WONDER stroke mortality, CDC PLACES health prevalence, population density, and geographic accessibility (drive time and distance to nearest basic and advanced stroke center) are collected. SCAI variables (hospitals, physicians, and stroke centers per capita) are in progress.

---

## Resources

| Resource | Path |
|---|---|
| Project plan and methodology | [docs/plan.md](docs/plan.md) |
| Pipeline guide (adding data, contracts, building indices) | [docs/pipeline_guide.md](docs/pipeline_guide.md) |
| Data dictionary and naming conventions | [data/data_dictionary.md](data/data_dictionary.md) |

---

## Repository layout

```
data/
  acs_data/                       ACS demographics notebook and outputs
  cdcwonder_data/                 CDC WONDER stroke mortality notebook and outputs
  cdcplaces_data/                 CDC PLACES health prevalence notebook and outputs
  pop_density_data/               population density notebook and outputs
  geographic_accessibility_data/  stroke center geocoding and accessibility outputs
  scai_data/                      SCAI variables (hospitals, physicians, stroke centers per capita)
docs/                             GitHub Pages site (Jekyll, jekyll-theme-cayman)
reference/                        crosswalks and reference tables (CT county crosswalk)
src/                              data pipelines (merge, database, FIPS utilities)
tests/                            automated test suite
notebooks/                        exploratory analysis
outputs/                          figures, maps, tables
```

`raw/` and `interim/` subdirectories inside `data/` are gitignored and can be regenerated locally.

---

## Setup

```bash
pip install -r requirements.txt
```

---

## Data pipeline

### Merge all sources into a single table

```bash
python src/merge.py
```

Produces `data/master.csv` — one row per county (91 total) with all sources joined on FIPS and cleaned. The file is gitignored; regenerate it locally as needed.

### Build the local database

```bash
python src/build_db.py
```

Creates `data/stroke_burden.db` (gitignored). Query it from any notebook without manual merges:

```python
import sqlite3
import pandas as pd

con = sqlite3.connect("data/stroke_burden.db")
df = pd.read_sql("SELECT * FROM master", con)
con.close()
```

Available tables: `counties`, `acs`, `mortality`, `geographic`, `cdc_places`, `pop_density`. The `master` view joins all loaded tables on `fips`. A `scai` table will be added once that data is collected.

### Adding a new data source

Add a loader function to `src/merge.py` and register it in the same file's `build_master()` call, then mirror the same in `src/build_db.py`:

```python
def _load_scai() -> pd.DataFrame:
    df = pd.read_csv(DATA / "scai_data/scai_data.csv", dtype={"fips": str})
    return df.drop(columns=["county", "state"], errors="ignore")
```

---

## Tests

```bash
python -m pytest tests/ -q
```

34 tests covering the CT FIPS validation gate, the merge pipeline, and the FIPS geocoding utility. All tests must pass before merging changes to pipeline code or data files. CI runs automatically on every push and pull request.

---

## Connecticut FIPS note

The Census Bureau replaced Connecticut's 8 historical counties (09001–09015) with 9 planning regions (09110–09190) in 2022. All data in this project uses the old 8-county codes. A validation gate (`reference/ct_crosswalk/validate_ct_codes.py`) raises an error if planning region codes are detected, preventing CT rows from silently dropping in any join.
