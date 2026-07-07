---
layout: page
title: Data lineage review
nav_order: 6
---

# Geographic accessibility data — lineage review

*2026-07-02. Read-only review of the geocoding and OpenRouteService drive-time
notebooks and the CSVs they produce. Nothing in `data/` was modified; two stale
documentation notes were corrected in the same change that adds this page.*

**TL;DR:** the final output (`geographic_stroke_accessibility.csv`) is complete
and internally consistent — 91 rows, no gaps, values verified against the
notebook's stated methods. Five findings, two of which need action: an API key
is committed in the drive-time notebook (rotate it), and the "nearest basic
stroke center" definition excludes advanced centers, which understates access
in 19 of 91 counties (team decision needed before GAI is finalized).

---

## Lineage map

```
NY DOH / NJ DOH / CT DPH stroke-center lists   (web pages, undated snapshots)
        │
        │  geocoding
        │   ├─ CT:    "Geocoding CT Stroke Centers.ipynb" — Nominatim by
        │   │          hospital name (+3 manually entered coordinates)
        │   └─ NY/NJ: geocoding code NOT in the repo — outputs only
        ▼
6 geocoded CSVs   (ct_basic, ct_advanced, ny_primary, ny_all,
        │          nj_primary, nj_all — see the folder README for which
        │          file is authoritative for what)
        │
        │   + Census CenPop2020 county population centroids
        │     (CenPop2020_Mean_CO09/34/36.txt, committed)
        ▼
"Geographic_Accessibility_Data_Gathering.ipynb"
   ├─ geopy geodesic → straight-line miles to nearest basic / advanced center
   ├─ OpenRouteService matrix API → drive minutes to nearest basic / advanced
   └─ Essex NY + Hamilton NY: ORS could not route → imputed at 45 mph
        ▼
geographic_stroke_accessibility.csv   (91 rows, no empty cells,
        │                              schema-contract-covered in CI)
        ▼
src/merge.py → data/master.csv → build_db.py / build_site_data.py → dashboard
                              └→ GAI via src/index_pipeline.py (all 4 columns)
(also read by "Mapping Geographic Accessibility.ipynb")
```

## What holds up well

- The ORS matrix calls are chunked to respect the 3,500-route API limit
  (91 counties × 20 hospitals = 1,820 routes per call).
- The Essex/Hamilton NY imputation (straight-line ÷ 45 mph) is reasonable for
  unroutable Adirondack centroids and is disclosed inside the notebook.
- FIPS codes are zero-filled correctly, and the CT centroid file uses the old
  8-county codes, so all 91 rows join the project spine cleanly.
- The folder README's warnings are exactly right: join on `fips` (the `state`
  column uses full names), don't stack `nj_primary` + `nj_all` (double
  counting), and always pass `vintage=419` when reverse-geocoding CT.
- Sanity-check cells (NYC-metro drive times) are present in the notebook, and
  the final CSV is covered by the schema contract tests in CI.

## Findings

### F1 — OpenRouteService API key committed in the notebook *(security — action required)*

`Geographic_Accessibility_Data_Gathering.ipynb` instantiates the ORS client
with a literal API key, which is now in the pushed git history. Anyone who
finds it can consume the account's quota.

**Action:** the key's owner should revoke/regenerate it in their
openrouteservice.org account settings, and future runs should read it from an
environment variable (`os.environ["ORS_API_KEY"]`) instead. Once rotated, the
old key in history is inert; scrubbing history becomes optional and could
piggyback on a future history rewrite if one ever happens.

### F2 — "Basic" access excludes advanced centers; nearest care overstated in 19/91 counties *(methodology — decision needed)*

`drive_time_min` and `nearest_stroke_distance` measure the nearest
**primary/acute-designated** center only. Advanced (comprehensive /
thrombectomy-capable) centers also treat stroke — they are the *preferred*
destination — but are excluded from the basic-tier columns. In **19 of 91
counties** the nearest advanced center is closer than the nearest basic one:

| County | "Basic" drive (min) | Advanced drive (min) |
|---|---|---|
| Fairfield, CT | 34.1 | 19.3 |
| Dutchess, NY | 36.7 | 16.3 |
| New York (Manhattan), NY | 10.1 | 2.5 |
| Herkimer, NY | 44.4 | 28.3 |
| Erie, NY | 25.7 | 12.2 |
| …14 more | | |

If `drive_time_min` is meant to be "time to any stroke-capable hospital," it
is overstated in those counties, and the GAI inherits the bias (all four
columns feed its PCA — the two basic-tier ones carry the artifact).

**No re-querying is needed to fix it:** `min(basic, advanced)` per county
gives "nearest any-tier center" directly from the existing CSV. The
alternative is to keep the current values and explicitly rename/document the
variables as designation-specific. Either is defensible; it should be a
deliberate choice before the GAI is finalized. Tracked as an open question in
[the plan](./plan.html).

### F3 — Docs claimed Essex/Hamilton `drive_time_advanced` was empty; the CSV is complete *(docs — fixed)*

The folder README and `data/data_dictionary.md` both said `drive_time_advanced`
was missing for Essex NY and Hamilton NY and told consumers to impute it. The
notebook actually imputes **both** drive-time columns at 45 mph before saving,
and the committed CSV has zero empty cells (the values match the formula to
the sixth decimal). Both docs are corrected in this change.

### F4 — Rerun hazards in the ORS chunk loop *(code — fix before the notebook is next rerun)*

Current output is correct, but two patterns would bite on a rerun:

- `durations.min(axis=1)` and `np.minimum(...)` both propagate NaN, so a
  single unreachable county↔hospital pair poisons that county's running
  minimum even if every other hospital routed fine. (Essex/Hamilton were
  genuinely unroutable from every chunk, so it made no difference this time.)
- A fully failed chunk is skipped with `continue`; a county whose only
  reachable hospitals were in that chunk would keep its `np.inf` initial
  value, which the `isna()` completeness check does not catch.

**Fix on next touch:** use `np.nanmin(..., axis=1)` within a chunk, `np.fmin`
across chunks, and assert `np.isfinite` on the result before saving.

### F5 — Provenance gaps *(reproducibility)*

- The NY/NJ geocoding code is not in the repo — only its outputs (committed
  2026-06-22). Tool, query strings, and retrieval date are unrecorded.
- The 3 NJ comprehensive centers with empty coordinates in
  `nj_all_stroke_centers_geocoded.csv` are patched only inside the drive-time
  notebook; anyone reconstructing from the CSVs alone re-inherits the gap.
  Consider writing the patched coordinates back into the CSV.
- CT geocoding matches Nominatim by hospital name + ", Connecticut" with a
  bare `except` that returns None — there is no verification that the match
  is actually the hospital. Spot checks pass; a systematic check
  (reverse-geocode each coordinate and compare towns) would close this.
- The state stroke-center lists are undated web snapshots; designations
  change. Record retrieval dates on the next update.
- Minor: the CT notebook writes a combined `ct_stroke_centers_geocoded.csv`
  that is not committed, and `county_stroke_distances.csv` is a superseded
  intermediate fully contained in the main output — keep or prune, but decide.

## Action list

| # | Action | Who | When |
|---|---|---|---|
| F1 | Rotate the ORS key; switch the notebook to an env var | key owner | now |
| F2 | Decide the basic-access definition (min-of-tiers vs. rename) | team | before GAI is finalized |
| F3 | Correct stale imputation docs | done (this change) | — |
| F4 | Harden the chunk loop (`nanmin`/`fmin`/`isfinite`) | anyone | next notebook rerun |
| F5 | Commit NY/NJ geocoding code or record tool + date; bake NJ coordinate patches into the CSV | data team | when convenient |
