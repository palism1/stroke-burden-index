---
layout: default
title: Pipeline guide
nav_order: 4
---

# Pipeline guide — how to use the data infrastructure

One-page reference for working with the repo's data pipeline. Audience: anyone
adding data files or building indices in notebooks. For methodology see the
[project plan](./plan.html); for variable definitions see
`data/data_dictionary.md`.

---

## Adding a data file

Every county-level CSV must follow the data dictionary conventions:

- **`fips`**: zero-padded 5-character string (`"09001"`, never `9001`). Read it
  back with `pd.read_csv(path, dtype={"fips": str})` to check yours survives a
  round trip.
- **Columns**: lowercase snake_case (`pcp_per_100k`, not `PCP Per 100k`).
- **Rows**: exactly 91 (62 NY, 21 NJ, 8 CT), one per county.
- **Rates**: `_per_100k` suffix for per-100,000 rates.

CI checks all of this automatically on every push and PR
(`tests/test_data_contracts.py`). If your PR goes red there, the error names
the file and the offending values — fix and push again. If you are
*intentionally* adding or renaming a column, update two things in the same PR:
the registry at the top of `tests/test_data_contracts.py` and
`data/data_dictionary.md`.

### SCAI specifically

Commit the file to exactly `data/scai_data/scai_data.csv` (inside the folder,
not the repo root) with columns `fips`, `hospitals_per_100k`,
`hospital_beds_per_100k`, `pcp_per_100k`, `neurologists_per_100k`,
`stroke_centers_per_100k`. That's all — the merge and database pipelines are
already wired to pick it up automatically the moment it merges. Full spec:
`data/scai_data/README.md`. Note that `pcnt_insured` is part of the SCAI *index
calculation* (recast there as the uninsured rate) but is NOT a column of
`scai_data.csv` — it lives in `data/acs_data.csv` and joins in via the master
merge. Conversely, `hospitals_per_100k` and `stroke_centers_per_100k` stay
columns of this file but are excluded from the index calculation
(`docs/DECISIONS.md`, 2026-07-06).

---

## Getting the merged data in a notebook

Regenerate locally whenever data files change (both outputs are gitignored):

```bash
python src/merge.py       # -> data/master.csv, one row per county
python src/build_db.py    # -> data/stroke_burden.db (SQLite)
```

```python
import sqlite3, pandas as pd

con = sqlite3.connect("data/stroke_burden.db")
df = pd.read_sql("SELECT * FROM master", con)   # everything joined on fips
con.close()
```

Always join on `fips`, never on county/state names.

---

## Building an index (SRI / SCAI / GAI)

Don't hand-roll the PCA pipeline — `src/index_pipeline.py` implements the
standard pipeline from the plan (align direction → standardize → PCA → sign
check → normalize 0–100) once, with tests.

```python
import sys; sys.path.insert(0, "src")    # adjust to your notebook's location
from index_pipeline import build_index

result = build_index(
    df,
    ["pcnt_65_plus", "poverty_rate", "smoking_prevalence", "pcnt_bachelors"],
    flip=["pcnt_bachelors"],     # variables whose high value points the "wrong" way
    name="sri",
)
df["sri"] = result.scores                # 0-100
result.loadings                          # PC1 loadings per variable (for write-ups)
result.explained_variance_ratio          # fraction of variance PC1 captures
```

**The one thing you must get right is `flip`.** Put every variable whose
*high* raw value points against the index direction in it:

| Index | Direction | What to flip |
|---|---|---|
| SRI | higher = more vulnerable | protective vars (education); percent low income is harmful-direction, so it is *not* flipped |
| SCAI | higher = better access | `pcnt_uninsured` (= `100 − pcnt_insured`, log1p-transformed; higher = more uninsured = worse access). The per-capita access vars already point up. Note the index uses only beds/PCP/neurologists — hospitals and stroke centers per capita are excluded (see `docs/DECISIONS.md` 2026-07-06) |
| GAI | higher = better access | all four drive-time/distance vars (lower = closer = better) |

Everything else is automatic — in particular the PC1 sign check, so the index
can't silently come out backwards. The function raises on NaN on purpose:
imputing or dropping is an analytical decision that belongs in your notebook,
never silently inside the pipeline.

### Skew and transforms

Team rule: PCA is sensitive to extreme outliers and heavy skew, so a heavily
skewed variable needs a non-linear fix (e.g. a log) *before* scaling — z-scoring
can't undo the shape. To act on it, pass `transforms`:

```python
result = build_index(df, variables, transforms={"poverty_rate": "log1p"})
```

`transforms` reshapes each named variable's raw values ("log" or "log1p") and
nothing auto-applies — the choice is yours. `result.skewness` reports each
variable's skewness, and `result.high_skew` lists untransformed variables with
`|skew| > 2.0` (`HIGH_SKEW_THRESHOLD`) so you can see what the rule would flag;
both are diagnostics and never change the scores. Order is **transform → align
(flip) → standardize → PCA**: transforms hit the raw values first, because a log
of a negated variable is nonsense. `"log"` raises on any value ≤ 0 and `"log1p"`
on any value < 0.

### The committed index scores

`src/compute_indices.py` is the canonical producer of the committed scores —
its CONFIG block encodes the settled decisions from
[the decisions log](./DECISIONS.html), one annotated entry per index:

```
python src/merge.py              # master.csv must be current first
python src/compute_indices.py   # -> data/indices.csv (fips, sri, scai, gai)
```

CI reruns this on every push and fails if `data/indices.csv` is stale, exactly
like the dashboard-data gate. So when a methodology decision changes: edit the
CONFIG block, rerun the two commands plus `python src/build_site_data.py`, and
commit the CONFIG + regenerated `indices.csv` + `counties.json` together — the
decision shows up as one reviewable diff. An EVR regression test pins the
numbers, so an accidental config change fails loudly.

The scores also land in the database as their own `indices` table. They are
deliberately **not** in the `master` view (they derive *from* master — keeping
the DAG acyclic); join them explicitly:

```sql
SELECT m.*, i.sri, i.scai, i.gai
FROM master m JOIN indices i USING (fips);
```

---

## Mapping

County boundary geometry keyed on `fips` lives at
`reference/county_boundaries/ny_nj_ct_counties.geojson` — ready for Plotly or
geopandas choropleths once index scores exist. See the README in that folder.

---

## Dashboard

An interactive county dashboard (static, client-side — no server) lives at
`docs/dashboard/` and is served on the Pages site. Its data comes from
`docs/data/counties.json`, generated by:

```bash
python src/build_site_data.py
```

Run this after any data change and commit the regenerated files in `docs/data/`
— CI fails if they are stale. New columns in `master.csv` (scai variables,
index scores) appear on the dashboard automatically; add a plain-language
label to `FIELD_LABELS` in `src/build_site_data.py` when you introduce one.
