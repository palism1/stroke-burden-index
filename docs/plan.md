---
layout: default
title: Methodology & plan
nav_order: 3
---

# Stroke Burden Index — Project Plan

**Status: DATA GATHERING is the active phase; methodology below is the agreed plan, not yet executed.** The analytical approach (indices, geospatial analysis, models) is now drafted and aligned across the team. We do not run it until the county-level data is in hand and audited. Items marked `(?)` are still open.

**Collected so far (91 NY/NJ/CT counties):**
- ACS demographics: `data/acs_data.csv` — age 65+, poverty, insurance, education, income bins
- CDC WONDER stroke mortality: `data/stroke_mortality.csv` — acute and sequelae age-adjusted rates, 2018–2024 pooled
- Geographic accessibility: `data/geographic_accessibility_data/geographic_stroke_accessibility.csv` — drive time and distance to nearest basic and advanced stroke center per county, via OpenRouteService
- Stroke center coordinates: geocoded for all NY, NJ, CT centers (see `data/geographic_accessibility_data/`)
- CT county crosswalk: `reference/ct_crosswalk/` — town-level mapping to old counties and planning regions

**Still needed:**
- SCAI: hospitals per capita, hospital beds per capita, PCP per capita, neurologists per capita (HIFLD / HRSA)
- ~~SRI health variables: smoking, obesity, diabetes, physical inactivity, hypertension (CDC PLACES)~~ *(done — `data/cdcplaces_data.csv`)*
- ~~Population density (Census TIGER + ACS land area)~~ *(done — `data/pop_density.csv`)*

**Next steps (bookmarked 2026-07-07):**
1. ~~**SCAI data collection**~~ *(done — `scai_data.csv` landed 2026-07-05, pipeline auto-activated)*
2. ~~**Compute GAI / SRI / SCAI**~~ *(done — all three computed and persisted: `src/compute_indices.py` → `data/indices.csv`, CI-gated; scores in the db `indices` table and on the dashboard. GAI is provisional pending the basic-access definition — see `DECISIONS.md`.)*
3. ~~**Risk vs. Access matrix**~~ *(done 2026-07-07 — live scatter on the dashboard: X = SRI, Y = SCAI, 75th/25th-percentile quadrants, linked to county selection)*
4. **SBPI** — the last index. Blocked on method + weights (now tracked in `DECISIONS.md` open items, with Hunterdon beds, neurologists skew, and the GAI definition).
5. **Dashboard iteration** — mobile QA, UX-doc pass against the now-complete feature set.

---

## 0. The question

**Where do stroke risk and poor access to care overlap? Identifying high-priority stroke intervention areas in the US.**

### Questions to answer

- Which counties exhibit the highest stroke vulnerability? Why?
- Which counties have the poorest access to stroke care?
- Which factors (socioeconomic, health, geographic, etc.) most strongly predict stroke mortality?
- How can resources be prioritized to reduce stroke burden?
- **Combined:** Which US counties face the greatest "stroke burden" from the combination of stroke risk factors AND limited access to stroke care?

### Overview

The Stroke Burden Index project constructs three county-level indices that measure aspects of a county's stroke burden:

- **Stroke Risk Index (SRI):** Measures underlying stroke risk using demographic, socioeconomic, and health-related risk factors.
- **Stroke Care Access Index (SCAI):** Measures the availability of stroke care resources, including hospitals, hospital capacity, healthcare providers, and certified stroke centers.
- **Geographic Accessibility Index (GAI):** Measures the geographic accessibility of stroke care using travel time and distance to the nearest stroke centers.

Each index was developed independently using county-level data for New York, New Jersey, and Connecticut. Prior to index construction, exploratory data analysis (EDA) was performed to evaluate missing data, variable distributions, correlations, and the suitability of the selected variables. Index-specific preprocessing, such as variable transformations and direction alignment, was applied where appropriate before constructing each index using principal component analysis (PCA). The resulting indices are standardized to a common 0–100 scale to facilitate interpretation and comparison across counties. The methodology for each index is described in the following sections, while implementation details of the PCA workflow are documented separately in the Pipeline Guide.



## 1. Core idea: three components → one priority index

We build two indices plus a geographic score, then combine them into the headline **Stroke Burden Priority Index (SBPI)**.

- **Stroke Risk Index (SRI)** — likelihood a community experiences stroke-related health problems based on health risk factors, socioeconomic factors, and demographic factors.
- **Stroke Care Access Index (SCAI)** — availability of treatment resources, including stroke treatment and preventative treatment, such as having access to a primary care physician and/or neurologist.
- **Geographic Access Index (GAI)** — strictly geographic access to stroke care, including variables such as estimated drive time to the nearest stroke center and distance to the nearest stroke center.
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

### Why Principal Component Analysis (PCA)?

Each index in this project combines several related variables intended to measure a common underlying concept, such as stroke risk, healthcare access, or geographic accessibility. Because many of these variables are correlated, combining them directly could overweight information that is represented by multiple measures.

Principal Component Analysis (PCA) was selected as a data-driven approach for constructing the indices because it:

- Reduces multiple correlated variables into a smaller number of composite components.
- Minimizes redundancy among variables while retaining the greatest amount of information.
- Determines variable weights objectively from the data rather than assigning subjective weights.
- Produces a single continuous score that can be compared across counties.

For each index, the first principal component (PC1) was retained because it explained the largest proportion of variation among the selected variables. The resulting component scores were then normalized to a 0–100 scale to improve interpretability while preserving the relative ranking of counties.


### Data Preprocessing

Prior to index construction:

- County datasets were merged using five-digit FIPS codes.
- Missing values were identified and resolved during data integration.
- Variables were transformed where appropriate to reduce skewness.
- Variables were aligned so that higher values consistently represented greater risk or better access.
- Continuous variables were standardized before PCA.

### Interpreting the Indices

All indices are normalized to a 0–100 scale.

| Index | Higher score indicates |
|--------|------------------------|
| SRI | Greater stroke vulnerability |
| SCAI | Better healthcare access |
| GAI | Better geographic accessibility |
| SBPI | Greater overall stroke burden |

### 2a. Stroke Risk Index (SRI)

1. **Align direction** so higher value = worse vulnerability. Percent low income already points the harmful way (higher = worse), so it is left as-is. Flip "protective" variables:
   - education → `-(education)`
2. **Standardize** (scale) all variables.
3. **Compute** the index with **PCA** (use PC1).
4. **Interpret:** higher PC1 → higher vulnerability. The PC1 sign check is automatic — `index_pipeline.build_index` orients the index against the aligned variables, so there is no manual "flip the index if it came out backwards" step. See `docs/pipeline_guide.md`.
5. **Normalize to 0–100.** `0` = lowest risk, `100` = highest risk.

#### Variables

The Stroke Risk Index (SRI) combines demographic, socioeconomic, and health-related variables associated with stroke vulnerability.

| Variable | Description |
|----------|-------------|
| `pcnt_65_plus` | Population aged 65 years and older (%) |
| `poverty_rate` | Population below the poverty line (%) |
| `pcnt_insured` | Population with health insurance (%) |
| `pcnt_bachelors` | Population with a bachelor's degree (%) |
| `pop_density` | Population density |
| `smoking_prevalence` | Adult smoking prevalence (%) |
| `obesity_prevalence` | Adult obesity prevalence (%) |
| `diabetes_prevalence` | Adult diabetes prevalence (%) |
| `hypertension_prevalence` | Adult hypertension prevalence (%) |
| `physical_inactivity` | Adult physical inactivity (%) |
| `stroke_prevalence` | Adult stroke prevalence (%) |

#### Exploratory Data Analysis

Prior to PCA, descriptive statistics, missing value assessment, histograms, and Pearson correlation analyses were performed for each candidate variable.

Population density exhibited a strong positive skew (skewness = 5.61) due to several densely populated urban counties. A `log1p` transformation reduced the skewness to 0.69 before PCA, while preserving the ordering of counties.

Our correlation analysis identified hypertension prevalence, smoking prevalence, obesity prevalence, diabetes prevalence, and the percentage of adults aged 65 years and older as the variables most strongly associated with county-level stroke mortality. Protective variables, including educational attainment, were reversed prior to PCA so that higher values consistently represented greater stroke vulnerability. 

#### PCA Results

The standardized variables were combined using PCA, with the first principal component retained as the Stroke Risk Index. Variable loadings and the explained variance ratio were evaluated to ensure that the selected variables captured a common measure of stroke vulnerability before the resulting scores were normalized to a 0–100 scale. From our PCA analysis, we found that the first principal component explained about 52.2% of the total variance among the selected stroke risk variables. This indicates that the demographic, socioeconomic, and health-related variables share a common underlying pattern of stroke vulnerability while still capturing multiple distinct dimensions of risk. Retaining the first principal component provides a reasonable summary of overall stroke risk without discarding the additional variation contributed by individual risk factors. This is reasonable, as these factors are related, but not perfectly correlated. 

### 2b. Stroke Care Access Index (SCAI)

1. **Align direction** so higher value = better access. Reverse the rurality variable if it is used.
2. **Standardize** (scale) all variables.
3. **Compute** the index with **PCA**.
4. **Check direction** (flip the sign if PC1 points the wrong way).
5. **Normalize to 0–100.** `0` = worst access, `100` = best access.

#### Variables

The Stroke Care Access Index (SCAI) measures the availability of healthcare resources related to stroke prevention and treatment.

The final index includes:

| Variable | Description |
|----------|-------------|
| `hospital_beds_per_100k` | Hospital beds per 100,000 population |
| `pcp_per_100k` | Primary care physicians per 100,000 population |
| `neurologists_per_100k` | Neurologists per 100,000 population |
| `pcnt_uninsured` | Percent uninsured |

Candidate variables including hospitals per 100,000 population and stroke centers per 100,000 population were evaluated during exploratory analysis before the final variable set was selected. However, we found these two variables to be a biased and inaccurate measure of access to care. Why? Some rural counties may have one basic community hospital, where stroke-related care is extremely limited. However, their small population may cause the hospitals per 100k rate to become over-inflated. On the other hand, urban counties, such as New York and Queens, have a lower hospitals per 100k rate due to their large population, as they have larger, more advanced hospitals with a significantly larger number of beds and physicians. Due to this, hospitals per 100k actually had a positive correlation with stroke mortality rate. Similar logic applies to stroke centers per 100k. Thus, hospital beds per 100k appeared to be a much better indicator of access to medical care. Due to these reasons, we chose to leave these two variables out of the index, but still include them in the exploratory data analysis for informational purposes.


#### Exploratory Data Analysis

Descriptive statistics, missing value assessment, distribution plots, skewness calculations, and both Pearson and Spearman correlation analyses were performed for all candidate healthcare access variables.

Several important relationships emerged during EDA. Hospital bed availability, primary care physician density, and neurologist density were positively correlated, indicating that these variables measured similar aspects of healthcare resource availability. Hospitals per 100,000 population and stroke centers per 100,000 population overlapped for 29 counties, primarily in smaller counties where every hospital is designated as a stroke center. Despite this overlap, correlation analysis showed that hospitals per 100,000 population captured a different aspect of healthcare access than provider availability.

The analysis also identified counties with no neurologists despite having certified stroke centers, suggesting that specialist availability varies independently from hospital designation. These findings informed the final selection of variables included in the PCA.


#### PCA Results

The first principal component (PC1) was retained as the Stroke Care Access Index. Primary care physician density, neurologist density, and hospital bed availability exhibited the largest positive loadings on the first principal component, indicating that they contributed most strongly to variation in healthcare access across counties. Percent uninsured had a comparatively small loading after direction alignment. Final index scores were normalized to a 0–100 scale, where higher values indicate greater access to stroke care. From our PCA analysis, we found that the first principal component explained 53.9% of the total variance among the healthcare access variables. This suggests that the selected measures capture a common dimension of healthcare access while also reflecting different aspects of resource availability, including provider density, hospital capacity, and insurance coverage. The first principal component therefore provides an appropriate summary measure of stroke care access across counties. 



### 2c. Geographic Accessibility Index (GAI)

#### Variables

The Geographic Accessibility Index (GAI) measures physical accessibility to stroke care using travel time and travel distance to the nearest certified stroke centers.

| Variable | Description |
|----------|-------------|
| `drive_time_min` | Drive time to the nearest basic stroke center |
| `drive_time_advanced` | Drive time to the nearest advanced stroke center |
| `nearest_stroke_distance` | Distance to the nearest basic stroke center |
| `nearest_stroke_distance_advanced` | Distance to the nearest advanced stroke center |

- All 4 run through the standard pipeline: **align direction** so higher = better access (flip the variables, since lower drive time / distance = better access) → **standardize** → **PCA** → **normalize to 0–100**.
- `0` = worst access (far), `100` = best access (close), same orientation as SCAI.

#### Exploratory Data Analysis

The geographic accessibility dataset was evaluated using descriptive statistics, missing value assessment, histograms, boxplots, state-level comparisons, correlation matrices, and county rankings.

Summary statistics show a median drive time of approximately 17 minutes to the nearest basic stroke center, although accessibility varied substantially across counties.

Distribution plots demonstrated that travel time and travel distance variables were positively skewed, reflecting a small number of counties with substantially poorer geographic access than the remainder of the study region. Correlation analysis showed strong relationships between straight-line distance and estimated driving time for both basic and advanced stroke centers, indicating that these variables measured a common underlying accessibility construct.

Additional analyses comparing geographic accessibility with acute stroke mortality revealed only weak positive associations, suggesting that geographic accessibility alone does not fully explain variation in county-level stroke mortality and should be interpreted alongside healthcare resource availability and underlying stroke risk.

Because shorter travel times and shorter travel distances represent better accessibility, all four variables were reversed prior to PCA so that higher values consistently represented better geographic access.


#### PCA Results

The transformed and standardized accessibility variables were combined using principal component analysis. All four travel variables contributed nearly equally to the first principal component, indicating that each measure captured similar information regarding geographic accessibility. The resulting scores were normalized to a 0–100 scale, where higher values indicate better geographic access to stroke care. From our PCA analysis, we found that the first principal component explained 77.0% of the total variance among the geographic accessibility variables. This indicates that travel time and travel distance to stroke centers measure a strong common underlying dimension of geographic accessibility. The high proportion of explained variance demonstrates that a single principal component effectively summarizes differences in geographic access to stroke care across counties.
  

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

> `(?)` **Weights need reconciling.** The formula above uses **50 / 30 / 20**, but the prose target was **50% vulnerability / 25% access / 25% distance** (50 / 25 / 25). Pick one before write-up — the numbers don't currently match.

**Option 2 — quadrant-based SBPI.** Instead of a continuous score, classify each county 1–4:

| Class | Rule | Score |
|---|---|---|
| **Critical priority** | Top 25% SRI **and** bottom 25% SCAI **and** top 25% distance | 4 |
| **High priority** | Top 25% SRI **and** bottom 50% SCAI | 3 |
| **Moderate priority** | One elevated risk factor (top 25% SRI, *or* bottom 25% SCAI, *or* top 25% distance) | 2 |
| **Low priority** | Good access **and** low vulnerability | 1 |

### National ranking

Produce a county-level ranking by SBPI. `(?)` Final ranking/combination method (Option 1 vs Option 2, or both) TBD once both indices exist.


### Summary of Final Indices

The table below summarizes the construction and performance of the three composite indices developed for this project.

| Index | Variables Included | PC1 Variance Explained | Interpretation |
|-------|---------------------|-----------------------:|----------------|
| **Stroke Risk Index (SRI)** | Population density, age 65+, poverty, low-income population, educational attainment, smoking, obesity, diabetes, hypertension, high cholesterol, physical inactivity, binge drinking, stroke prevalence | **52.2%** | Measures county-level stroke vulnerability based on demographic, socioeconomic, and health-related risk factors. Higher scores indicate greater stroke risk. |
| **Stroke Care Access Index (SCAI)** | Hospital beds per 100,000, primary care physicians per 100,000, neurologists per 100,000, uninsured population | **53.9%** | Measures the availability of healthcare resources related to stroke prevention and treatment. Higher scores indicate better access to stroke care. |
| **Geographic Accessibility Index (GAI)** | Drive time to the nearest stroke center, drive time to the nearest advanced stroke center, distance to the nearest stroke center, distance to the nearest advanced stroke center | **77.0%** | Measures the geographic accessibility of stroke care. Higher scores indicate better geographic access. |

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

- `(?)` Basic-access definition: `drive_time_min` / `nearest_stroke_distance` measure the nearest *primary/acute-designated* center only, but an advanced center (which also treats stroke) is closer in 19 of 91 counties. Redefine as nearest any-tier center (columnwise `min` — no re-querying needed) or keep and document as designation-specific. See [the lineage review](./geo_lineage_review.html), finding F2.
- `(?)` Reconcile SBPI weights: formula is 50/30/20, prose target was 50/25/25.
- `(?)` SBPI method: continuous weighted (Option 1), quadrant classification (Option 2), or both.
- `(?)` Canonical CT code system (old counties vs planning regions) — pending decision.
- ~~`(?)` Pooled-mortality year window for CDC WONDER.~~ *(locked: 2018–2024, matches the committed data)*
- ~~`(?)` Rename SVI to avoid the CDC Social Vulnerability Index collision.~~ *(resolved 2026-07-05: renamed to SRI, Stroke Risk Index)*
- `(?)` Stroke-center file scope: tristate proof-of-concept or national.
- `(?)` National stroke-center designation source: EMNet vs Joint Commission.
- `(?)` Does County Health Rankings cover enough SRI variables to skip multi-source assembly.
- `(?)` Final SRI / SCAI variable lists (trim after seeing data quality).
- `(?)` Hotspot analysis (Local Moran's I / Getis-Ord Gi\*) — include or skip.
- ~~`(?)` Travel-distance metric: haversine for v1, routed drive time later.~~ *(both shipped: straight-line miles + ORS drive time in `geographic_stroke_accessibility.csv`)*
- ~~`(?)` Output surface: static maps only, or an interactive dashboard (changes the host).~~ *(decided: client-side dashboard on Pages, scaffold at `docs/dashboard/` — see §6)*
