---
layout: page
title: Methodology & plan
nav_order: 3
status: living
last_updated: 2026-07-10
---

# Stroke Burden Index — Project Plan

**Status: the core build is COMPLETE (2026-07-09).** All data is collected and audited for the 91 NY/NJ/CT counties, all four indices (SRI, SCAI, GAI, SBPI + priority class) are computed and CI-gated in `data/indices.csv`, and the live site serves the write-up (methodology, data sources, project outcome) plus the interactive dashboard with the Risk-vs-Access matrix and per-county recommendations. Remaining work is polish and the optional analyses below. Items marked `(?)` are still open; every decided item is logged in `DECISIONS.md`.

**Collected (91 NY/NJ/CT counties, all done):**
- ACS demographics: `data/acs_data.csv` — age 65+, poverty, insurance, education, income bins
- CDC WONDER stroke mortality: `data/stroke_mortality.csv` — acute and sequelae age-adjusted rates, 2018–2024 pooled
- CDC PLACES health prevalence: `data/cdcplaces_data.csv` — smoking, obesity, diabetes, inactivity, hypertension, cholesterol, binge drinking, stroke
- Population density: `data/pop_density.csv` (Census TIGER + ACS land area)
- Geographic accessibility: `data/geographic_accessibility_data/geographic_stroke_accessibility.csv` — drive time and distance to nearest basic and advanced stroke center per county, via OpenRouteService
- SCAI variables: `data/scai_data/scai_data.csv` — hospitals, beds, PCPs, neurologists, stroke centers per 100k
- Stroke center coordinates: geocoded for all NY, NJ, CT centers (see `data/geographic_accessibility_data/`)
- CT county crosswalk: `reference/ct_crosswalk/` — town-level mapping to old counties and planning regions

**Next steps (updated 2026-07-10):**
1. ~~**SCAI data collection**~~ *(done — `scai_data.csv` landed 2026-07-05, pipeline auto-activated)*
2. ~~**Compute GAI / SRI / SCAI**~~ *(done — all three computed and persisted: `src/compute_indices.py` → `data/indices.csv`, CI-gated; scores in the db `indices` table and on the dashboard. GAI definition settled 2026-07-07: nearest any-tier center.)*
3. ~~**Risk vs. Access matrix**~~ *(done 2026-07-07 — live scatter on the dashboard: X = SRI, Y = SCAI, 75th/25th-percentile quadrants, linked to county selection)*
4. ~~**SBPI**~~ *(done 2026-07-07 — both methods per the team vote: continuous 50/30/20 score + 1–4 priority class, in `indices.csv`, the db, and the dashboard)*
5. ~~**Per-county recommendations engine**~~ *(done 2026-07-08 — top-3 percentile risk drivers + priority-class action plan from the team framework, rendered in the dashboard details panel)*
6. **Dashboard iteration** — mobile QA, UX-doc pass against the now-complete feature set.
7. **Optional analyses** `(?)` — hotspot clustering (Local Moran's I / Getis-Ord Gi*), predictive models (§5).

---

## 0. The question

**Where do stroke risk and poor access to care overlap? Identifying high-priority stroke intervention areas in the US.**

### Questions to answer

- Which counties exhibit the highest stroke vulnerability? Why?
- Which counties have the poorest access to stroke care?
- Which factors (socioeconomic, health, geographic, etc.) most strongly predict stroke mortality?
- How can resources be prioritized to reduce stroke burden?
- **Combined:** Which US counties face the greatest "stroke burden" from the combination of stroke risk factors AND limited access to stroke care?

---

## 1. Core idea: three components → one priority index

We build two indices plus a geographic score, then combine them into the headline **Stroke Burden Priority Index (SBPI)**.

- **Stroke Risk Index (SRI)** — likelihood a community experiences stroke-related health problems.
- **Stroke Care Access Index (SCAI)** — availability of treatment resources.
- **Geographic Access Score** — travel distance to the nearest stroke center.
- **Stroke Burden Priority Index (SBPI)** — the main, combined index that ranks counties by overall burden.

> **Naming collision (resolved 2026-07-05).** CDC/ATSDR already publishes a "Social Vulnerability Index (SVI)" that dominated any data search for "SVI." To avoid citation/file-name confusion, our index was renamed to the **Stroke Risk Index (SRI)**.

### Stroke Risk Index (SRI)

Candidate variables (audit and trim once data quality is known):

- **Demographics:** % population over 65, population density
- **Socioeconomic:** poverty rate, percent low income, education level
- **Health:** smoking prevalence, obesity prevalence, diabetes prevalence, physical inactivity, etc. `(?)`

### Stroke Care Access Index (SCAI)

Candidate variables (audit and trim):

- **Healthcare access:** hospitals per capita, stroke centers per capita, PCP per capita, insurance coverage
- **Geographic access:** urban / suburban / rural classification `(?)` (the distance half is handled separately, see Geographic Access Score)

> The verified stroke-centers-with-coordinates file (Section 4b) is the foundation for the access side: stroke centers per capita and distance to nearest center.

### Priority matrix (Vulnerability × Access)

| Vulnerability \ Access | Good access | Poor access |
|---|---|---|
| **Low vulnerability** | Low priority | Monitor |
| **High vulnerability** | Prevention focus | Highest priority |
| **Very high vulnerability** | Resource allocation | Critical intervention zone |

---

## 2. Index methodology

Every index follows the same pipeline: **raw → align direction → standardize → PCA → normalize → index (0–100)**.

> **Implemented:** the pipeline below exists once, tested, as `src/index_pipeline.py` (`build_index`) — including the automatic PC1 sign check. Notebooks call it instead of hand-rolling PCA; usage in `docs/pipeline_guide.md`.

### 2a. Stroke Risk Index (SRI)

1. **Align direction** so higher value = worse vulnerability. Percent low income already points the harmful way (higher = worse), so it is left as-is. Flip "protective" variables:
   - education → `-(education)`
2. **Standardize** (scale) all variables.
3. **Compute** the index with **PCA** (use PC1).
4. **Interpret:** higher PC1 → higher vulnerability. The PC1 sign check is automatic — `index_pipeline.build_index` orients the index against the aligned variables, so there is no manual "flip the index if it came out backwards" step. See `docs/pipeline_guide.md`.
5. **Normalize to 0–100.** `0` = lowest risk, `100` = highest risk.

### 2b. Stroke Care Access Index (SCAI)

1. **Align direction** so higher value = better access. Reverse the rurality variable if it is used.
2. **Standardize** (scale) all variables.
3. **Compute** the index with **PCA**.
4. **Check direction** (flip the sign if PC1 points the wrong way).
5. **Normalize to 0–100.** `0` = worst access, `100` = best access.

### 2c. Geographic Accessibility Index (GAI)

- Built from **4 variables**: `drive_time_min`, `drive_time_advanced`, `nearest_stroke_distance`, `nearest_stroke_distance_advanced`.
- All 4 run through the standard pipeline: **align direction** so higher = better access (flip the variables, since lower drive time / distance = better access) → **standardize** → **PCA** → **normalize to 0–100**.
- `0` = worst access (far), `100` = best access (close), same orientation as SCAI.

### 2d. Stroke Burden Priority Index (SBPI)

The main combined index. Two candidate methods:

**Option 1 — simple weighted index.** Everything scaled 0–100 first, with this orientation:

| Component | `0` means | `100` means |
|---|---|---|
| SRI | least vulnerable | most vulnerable |
| SCAI | worst access | best access |
| Geographic distance score | very far | very close |

Build deficits so higher = worse:

- Access deficit = `100 − SCAI`
- Distance deficit = `100 − Distance score`

```
SBPI = 0.5 · SRI + 0.3 · (Access deficit) + 0.2 · (Distance deficit)
```

Weights are tunable, but vulnerability should always carry the most weight.

> ~~`(?)` **Weights need reconciling.**~~ *(resolved 2026-07-07: team vote locked **50 / 30 / 20** — see `DECISIONS.md`.)*

**Option 2 — quadrant-based SBPI.** Instead of a continuous score, classify each county 1–4:

| Class | Rule | Score |
|---|---|---|
| **Critical priority** | Top 25% SRI **and** bottom 25% SCAI **and** top 25% distance | 4 |
| **High priority** | Top 25% SRI **and** bottom 50% SCAI | 3 |
| **Moderate priority** | One elevated risk factor (top 25% SRI, *or* bottom 25% SCAI, *or* top 25% distance) | 2 |
| **Low priority** | Good access **and** low vulnerability | 1 |

### National ranking

Produce a county-level ranking by SBPI. ~~`(?)` Final ranking/combination method TBD~~ *(resolved 2026-07-07: **both** — the continuous score (`sbpi`) and the 1–4 class (`sbpi_class`) ship together in `data/indices.csv`; class counts today: 55 low / 16 moderate / 10 high / 10 critical.)*

---

## 3. Geospatial analysis

**Driving question:** Are there geographic barriers to stroke care in the NY-NJ-CT region, and do those barriers correspond to higher stroke burden?

1. **Map stroke centers.** Point map of stroke centers over county boundaries. Where are they concentrated? Where are the geographic gaps?
2. **Travel distance.** For each county, distance from its population center to the nearest stroke center.
3. **Accessibility map.** Choropleth colored by distance band: 0–10 mi, 10–25 mi, 25–50 mi, 50+ mi.
4. **Accessibility rankings.** Top 5 and bottom 5 counties per state.
5. **Distance vs. mortality.** Scatter of distance to stroke center vs. stroke mortality rate.
6. **Distance vs. SRI.** Scatter of distance vs. SRI — are vulnerable populations also geographically isolated? Those are high-priority areas.
7. **Accessibility × Vulnerability matrix.** X = vulnerability (SRI), Y = access (SCAI or distance, oriented so higher Y = better access). Split each at the 75th / 25th percentile into quadrants:
   - High vulnerability, **low access** → **Critical intervention** (these are the **stroke care deserts**)
   - High vulnerability, high access → focus on prevention
   - Low vulnerability, low access → monitor for changes
   - Low vulnerability, high access → system working well, no action
8. **Hotspot analysis** `(?)` (optional). "Is this county part of a statistically significant cluster?"
   - **Local Moran's I** — High-High (hotspot), Low-Low (coldspot), High-Low / Low-High (outliers); map significant clusters.
   - **Getis-Ord Gi\*** — classic hot/cold-spot clusters.
   - Analyze on: stroke mortality (mortality clusters), distance (care deserts), SRI (vulnerability clusters), SBPI (highest-priority intervention regions).

Then: produce a national ranking.

---

## 4. Data gathering (current phase)

### 4a. Candidate data sources (audit first, not locked)

Audit each before committing: confirm current vintage, county-level granularity, and license. Dogma: prefer one source that already bundles many variables over assembling many.

**Strong "buy not build" candidate to audit first:**

- **County Health Rankings & Roadmaps (RWJF / Univ. of Wisconsin)** — aggregates poverty, smoking, obesity, diabetes, physical inactivity, PCP ratio, uninsured rate, and more at county level. May collapse much of the SRI collection work. `(?)` confirm coverage. <https://www.countyhealthrankings.org/health-data>

**Stroke outcomes:**

- Stroke mortality by county: **CDC WONDER** (mortality) <https://wonder.cdc.gov/> ; CDC Interactive Atlas of Heart Disease and Stroke. `(?)` confirm county-level age-adjusted stroke mortality rate.
- Stroke prevalence (not mortality): CDC PLACES.
- **Pooling note (decided):** single-year county mortality from WONDER is suppressed for many smaller counties, so we **pool a few years** for more stable rates. ~~`(?)` exact year window TBD~~ **Locked: 2018–2024 pooled** — this is what the committed `data/stroke_mortality.csv` contains (see data dictionary).

**Risk-factor prevalence (county):** CDC PLACES (smoking, obesity, diabetes, physical inactivity, etc.).

**Demographics + socioeconomic (county):** US Census ACS 5-year (age 65+, poverty, percent low income, educational attainment). Population density: Census population + land area (TIGER/Line).

**Insurance coverage (county):** Census SAHIE or ACS. `(?)`

**Physicians / PCP per capita (county):** HRSA Area Health Resources Files (AHRF) <https://data.hrsa.gov/topics/health-workforce/nchwa/ahrf> , or the PCP ratio already in County Health Rankings.

**Urban / rural classification (county):** USDA Rural-Urban Continuum Codes (RUCC) <https://www.ers.usda.gov/data-products/rural-urban-continuum-codes> , or NCHS Urban-Rural Classification. `(?)` pick one.

**Hospitals + coordinates:**

- HIFLD Hospitals open dataset. National; includes NAME, ADDRESS, CITY, STATE, COUNTY, TYPE, TRAUMA, BEDS, LATITUDE, LONGITUDE. CSV / GeoJSON + live API. Coordinates already done, so we geocode nothing for hospitals that match.
  - <https://hifld-geoplatform.opendata.arcgis.com/datasets/geoplatform::hospitals/about>
  - Weekly-updated mirror: <https://github.com/rearc-data/hospitals-hifld>

**Stroke-center designation (which hospitals count as stroke centers):**

- Tristate (NY/NJ/CT) authoritative lists:
  - NY: NYSDOH Stroke Designation Program + directory <https://profiles.health.ny.gov>
  - NJ: state-designated stroke centers by county (PDF) <https://nj.gov/health>
  - CT: DPH certified stroke centers <https://portal.ct.gov/dph/emergency-medical-services/ems/certified-stroke-centers>
- National single-source options:
  - EMNet **findERnow** (Mass General) — all certified/designated stroke centers nationally, linked to CMS Provider ID (cleanest join key); available to researchers on request (emnet@partners.org).
  - The Joint Commission Quality Check directory (also DNV, ACHC/HFAP).

**Travel distance to nearest stroke center (done for tristate):**

- Straight-line distance and drive time (via OpenRouteService) from each county's population center to nearest basic and advanced stroke center. Output: `data/geographic_accessibility_data/geographic_stroke_accessibility.csv`.
- Essex NY and Hamilton NY have imputed drive times (ORS could not route). See `data/geographic_accessibility_data/README.md`.

> **Audit step before any of the above:** confirm what fraction of the stroke-center list actually matches HIFLD cleanly. That single number decides whether geocoding leftovers is a footnote or the main event. First thing to test (see 4b).

### 4b. Verified stroke-centers-with-coordinates file (done for tristate)

Geocoded stroke center files for NY, NJ, CT are in `data/geographic_accessibility_data/`. See the README in that folder for file descriptions, missing coordinate counts, and the NJ dual-file usage pattern.

`(?)` **National expansion:** tristate proof-of-concept is complete. National designation data leans on EMNet findERnow (CMS Provider ID) or Joint Commission rather than per-state PDFs — scope decision still open.

**Pipeline (v1):**

1. **Audit.** Pull HIFLD hospitals filtered to the target region. Count rows, inspect fields, note SOURCE/vintage. No transforms yet.
2. **Pull the stroke-center list.** Tristate: NY + NJ + CT. National: EMNet findERnow (CMS Provider ID) or Joint Commission. `(?)`
3. **Join.** Match designation list to HIFLD on NAME + ADDRESS (fuzzy), or CMS Provider ID if EMNet.
4. **Verify.** Report match rate. Any stroke center that fails the join gets its address geocoded with the **US Census Geocoder** (free, no API key, batch up to ~10k addresses).
5. **Output:** write `stroke_centers.csv` and `stroke_centers.geojson` (name, address, designation tier, lat, lon, source, match_method = hifld_match / census_geocode / unmatched); print a terminal summary (counts by tier and state + any unmatched for manual review).

**Tooling order (dogma):** Python stdlib + `pandas` + `requests` first. Add `geopandas` only if needed for GeoJSON / spatial joins. No framework, no heavy GIS stack unless the data forces it.

### 4c. County keying + Connecticut (built)

- One tidy county-level table keyed by **FIPS**, stored as **zero-padded strings everywhere** (never int — leading zeros matter).
- **Connecticut is special.** Census replaced CT's 8 counties with 9 planning regions (2022), but most health sources still ship CT in the old county codes. The repo now contains a town-level crosswalk and a validation gate to prevent CT rows from silently dropping in any join:
  - `reference/ct_crosswalk/ct_town_crosswalk.csv` — 169 towns → old county (09001–09015) **and** planning region (09110–09190).
  - `reference/ct_crosswalk/validate_ct_codes.py` — `validate_ct_codes(df, fips_col, system)` raises on any CT code that doesn't fit the expected system.
  - `(?)` **Canonical CT system on hold pending decision.** Gate default is `county_2020` (the 8 old counties), which matches most sources. The 8-old-county form is the current direction on `main`.

---

## 5. Tasks

### Data engineering

- Data collection, cleaning, integration into one county-level table keyed by FIPS (CT handled via the crosswalk + gate above).

### EDA

- Descriptive statistics; visualizations.
- Investigate: counties with highest stroke mortality, relationships among risk factors, regional differences `(?)`.

### Stroke Risk Index (SRI)

- Variable selection / risk-factor identification, standardize, PCA, component interpretation, construct index.
- **Deliverables:** PCA results, vulnerability scores, ranking table.

### Stroke Care Access Index + spatial analysis

- Access metrics: hospitals / physicians / stroke centers per capita.
- Geographic analysis: map stroke mortality, access measures, vulnerability scores; construct index.
- Clustering `(?)`: K-means, county typology.
- **Deliverables:** maps, cluster analysis, access index.

### Predict stroke mortality (ML)

- Models: linear regression, random forest, XGBoost, etc. `(?)`
- Evaluate with RMSE, MAE, R²; compare to pick the most appropriate.
- Interpret with SHAP / feature importance.
- **Deliverables:** model comparison, SHAP analysis, dashboard `(?)`.

### Policy recommendations

- Translate findings into resource-prioritization recommendations using the priority matrix and SBPI ranking.

---

## 6. Output / delivery surface (decided)

**Decision (2026-07-02): interactive client-side dashboard on the existing GitHub Pages site — no separate host needed.** Everything the UX research doc calls for (search, clickable choropleth, county details panel, linked matrix) is achievable with static files and client-side JS at this data size (91 counties).

- **Built:** dashboard scaffold at `docs/dashboard/` — county search, choropleth (sequential orange, colorblind-safe per the UX doc), plain-language county details. Runs on real data today; index scores appear automatically when computed. Data exported by `src/build_site_data.py` (CI keeps it in sync).
- ~~**Heavier `(?)`:** an interactive dashboard (Streamlit / Dash) does **not** run on GitHub Pages (static-only) — it needs a separate host.~~ *(moot — no server required)*

---

## Open questions to resolve

- ~~`(?)` Basic-access definition (lineage review finding F2).~~ *(resolved 2026-07-07, team vote: nearest **any-tier** center — the basic-tier GAI inputs use the columnwise `min` of the two tiers, derived at index time; source CSVs unchanged. See `DECISIONS.md`.)*
- ~~`(?)` Reconcile SBPI weights: formula is 50/30/20, prose target was 50/25/25.~~ *(resolved 2026-07-07: 50/30/20 — see `DECISIONS.md`)*
- ~~`(?)` SBPI method: continuous weighted (Option 1), quadrant classification (Option 2), or both.~~ *(resolved 2026-07-07: both — `sbpi` + `sbpi_class` in `data/indices.csv`)*
- ~~`(?)` Canonical CT code system (old counties vs planning regions).~~ *(settled in practice: all committed data uses the old 8-county codes, enforced by the `validate_ct_codes` gate in every pipeline)*
- ~~`(?)` Pooled-mortality year window for CDC WONDER.~~ *(locked: 2018–2024, matches the committed data)*
- ~~`(?)` Rename SVI to avoid the CDC Social Vulnerability Index collision.~~ *(resolved 2026-07-05: renamed to SRI, Stroke Risk Index)*
- `(?)` Stroke-center file scope: tristate proof-of-concept or national. *(tristate shipped; going national is a possible extension)*
- `(?)` National stroke-center designation source: EMNet vs Joint Commission. *(only relevant if the national extension happens)*
- ~~`(?)` Does County Health Rankings cover enough SRI variables to skip multi-source assembly.~~ *(moot — multi-source assembly is done: ACS + CDC PLACES + WONDER + TIGER)*
- ~~`(?)` Final SRI / SCAI variable lists (trim after seeing data quality).~~ *(locked in `src/compute_indices.py` CONFIG per the dated `DECISIONS.md` entries — 13 SRI variables, 4 SCAI variables after exclusions)*
- `(?)` Hotspot analysis (Local Moran's I / Getis-Ord Gi\*) — include or skip.
- ~~`(?)` Travel-distance metric: haversine for v1, routed drive time later.~~ *(both shipped: straight-line miles + ORS drive time in `geographic_stroke_accessibility.csv`)*
- ~~`(?)` Output surface: static maps only, or an interactive dashboard (changes the host).~~ *(decided: client-side dashboard on Pages, scaffold at `docs/dashboard/` — see §6)*
