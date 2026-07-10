# Stroke Burden Index

Identifying high-priority stroke intervention areas across the United States by combining a **Stroke Risk Index (SRI)** (community stroke risk), a **Stroke Care Access Index (SCAI)** (treatment availability), and a **Geographic Accessibility Index (GAI)** (travel to care) at the county level into a single **Stroke Burden Priority Index (SBPI)**.

**Live site:** [palism1.github.io/stroke-burden-index](https://palism1.github.io/stroke-burden-index/)

**Status:** All data is collected and all four indices are computed for the 91 NY/NJ/CT counties. The committed scores live in `data/indices.csv` (canonical producer: `src/compute_indices.py`, CI-gated against staleness) along with each county's priority class and top-3 risk drivers. The live site serves the full write-up (methodology, data sources, project outcome) plus the interactive dashboard: choropleth over 32 metrics, county search, a Risk-vs-Access quadrant matrix, and a per-county recommendation generated from the team's priority framework (`docs/DECISIONS.md`, 2026-07-07/08).

---

## Resources

| Resource | Path |
|---|---|
| Project plan and methodology | [docs/plan.md](docs/plan.md) |
| Decisions log (every methodology call, dated) | [docs/DECISIONS.md](docs/DECISIONS.md) |
| Interactive county dashboard | [docs/dashboard/](docs/dashboard/) — live at [/dashboard](https://palism1.github.io/stroke-burden-index/dashboard/) |
| Pipeline guide (adding data, contracts, building indices) | [docs/pipeline_guide.md](docs/pipeline_guide.md) |
| Data dictionary and naming conventions | [data/data_dictionary.md](data/data_dictionary.md) |

---

## Repository layout

```
data/
  indices.csv                     computed index scores + priority class + top-3 drivers (CI-gated)
  acs_data/                       ACS demographics notebook and outputs
  cdcwonder_data/                 CDC WONDER stroke mortality notebook and outputs
  cdcplaces_data/                 CDC PLACES health prevalence notebook and outputs
  pop_density_data/               population density notebook and outputs
  geographic_accessibility_data/  stroke center geocoding and accessibility outputs
  scai_data/                      SCAI variables (hospitals, physicians, stroke centers per capita)
docs/                             GitHub Pages site (Jekyll, vendored Zolan theme) + dashboard
  dashboard/                      interactive county dashboard (client-side JS, no server)
  notebook_html/                  exported HTML views of the analysis notebooks
reference/                        crosswalks and reference tables (CT county crosswalk, boundaries, UX research)
src/                              data pipelines (merge, indices, database, site data export)
tests/                            automated test suite (pytest + dashboard smoke test)
notebooks/                        exploratory analysis and index EDA
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

Available tables: `counties`, `acs`, `mortality`, `geographic`, `cdc_places`, `pop_density`, `scai`, `indices`. The `master` view joins all loaded tables on `fips` — except `indices`, which derives *from* master and must be joined explicitly (`JOIN indices USING (fips)`) to keep the data DAG acyclic.

### Compute the index scores

```bash
python src/compute_indices.py
```

Writes `data/indices.csv` — SRI/SCAI/GAI/SBPI scores (0–100), the 1–4 priority class, the threshold flags behind it, and each county's top-3 percentile risk drivers. This file **is** committed; CI recomputes it on every push and fails if the committed copy is stale, so the scores can never silently drift from the data. The index definitions mirror `docs/DECISIONS.md` entry-by-entry in the script's CONFIG block.

### Export dashboard data

```bash
python src/build_site_data.py
```

Writes `docs/data/counties.json` (+ boundary GeoJSON) for the dashboard, including the per-county recommendation payload. Also CI-gated: regenerate and commit alongside any data change.

### Adding a new data source

Add a loader function to `src/merge.py` and register it in the same file's `build_master()` call, then mirror the same in `src/build_db.py` (see the existing loaders for the pattern — `_read` handles fips dtype + float parsing). Full walkthrough in [docs/pipeline_guide.md](docs/pipeline_guide.md).

---

## Tests

```bash
python -m pytest tests/ -q            # 135 tests: contracts, pipeline, indices, db, site export
node tests/smoke/smoke_dashboard.js   # runs the real dashboard JS against the real data
```

All tests must pass before merging changes to pipeline code or data files. CI runs the suite plus staleness gates (recompute `indices.csv` and `docs/data/`, fail on diff) on every push and pull request.

---

## Connecticut FIPS note

The Census Bureau replaced Connecticut's 8 historical counties (09001–09015) with 9 planning regions (09110–09190) in 2022. All data in this project uses the old 8-county codes. A validation gate (`reference/ct_crosswalk/validate_ct_codes.py`) raises an error if planning region codes are detected, preventing CT rows from silently dropping in any join.
