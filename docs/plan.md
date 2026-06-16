---
layout: default
title: Project plan
---

# Stroke Burden Index — Project Plan

**Status: PLANNING + DATA GATHERING ONLY.** Scope is deliberately loose. Every item marked `(?)` is open and will be tightened once we have the data in hand. Nothing below is locked. Do not optimize, model, or build analysis pipelines yet. The first concrete deliverable is data (see Section 2b).

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

## 1. Core idea: two indices plus a priority matrix

### Stroke Vulnerability Index (SVI)

Measures the likelihood that a community will experience stroke-related health problems.

> `(?)` **Naming collision.** CDC/ATSDR already publishes a "Social Vulnerability Index (SVI)" that will dominate any data search for "SVI." Consider renaming ours (e.g. `StrokeVI` or `SVulnI`) before we write anything up, to avoid confusion in citations and file names.

Candidate variables (to audit and trim):

- **Demographics:** % population over 65, population density
- **Socioeconomic:** poverty rate, median income, education level
- **Health:** smoking prevalence, obesity prevalence, diabetes prevalence, physical inactivity, etc. `(?)`

### Stroke Care Access Index (SCAI)

Measures availability of treatment resources.

Candidate variables (to audit and trim):

- **Healthcare access:** hospitals per capita, stroke centers per capita, PCP per capita, insurance coverage
- **Geographic access:** urban / suburban / rural classification `(?)`, travel distance to nearest stroke center

> The stroke-centers-with-coordinates file in Section 2b is the foundation for the geographic-access half of SCAI (stroke centers per capita, distance to nearest center).

### Priority matrix (Access x Vulnerability)

| Vulnerability \ Access | Good access | Poor access |
|---|---|---|
| **Low vulnerability** | Low priority | Monitor |
| **High vulnerability** | Prevention focus | Highest priority |
| **Very high vulnerability** | Resource allocation | Critical intervention zone |

### National ranking

Produce a county-level ranking by combined stroke burden. `(?)` exact ranking method TBD once both indices exist.

---

## 2. Data gathering (current phase)

### 2a. Candidate data sources (audit first, not locked)

Audit each before committing. Confirm current vintage, county-level granularity, and license. Follow the dogma: prefer one source that already bundles many variables over assembling many.

**Strong "buy not build" candidate to audit first:**

- **County Health Rankings & Roadmaps (RWJF / Univ. of Wisconsin)** — already aggregates poverty, smoking, obesity, diabetes, physical inactivity, PCP ratio, uninsured rate, and more at county level. If it covers enough of our SVI variables, it collapses a lot of the collection work. `(?)` confirm which of our variables it includes.

**Stroke outcomes:**

- Stroke mortality by county: CDC Interactive Atlas of Heart Disease and Stroke; CDC WONDER (mortality). `(?)` confirm which gives county-level age-adjusted stroke mortality rate.
- Stroke prevalence (not mortality): CDC PLACES.

**Risk-factor prevalence (county):**

- CDC PLACES (smoking, obesity, diabetes, physical inactivity, etc.).

**Demographics + socioeconomic (county):**

- US Census ACS 5-year (age 65+, poverty, median income, educational attainment).
- Population density: Census population + land area (TIGER/Line).

**Insurance coverage (county):**

- Census SAHIE (Small Area Health Insurance Estimates) or ACS. `(?)`

**Physicians / PCP per capita (county):**

- HRSA Area Health Resources Files (AHRF), or the PCP ratio already in County Health Rankings.

**Urban / rural classification (county):**

- USDA Rural-Urban Continuum Codes (RUCC), or NCHS Urban-Rural Classification. `(?)` pick one.

**Hospitals + coordinates:**

- HIFLD Hospitals open dataset. National, includes NAME, ADDRESS, CITY, STATE, COUNTY, TYPE, TRAUMA, BEDS, LATITUDE, LONGITUDE. Available as CSV / GeoJSON and via a live GeoServices/WFS API. Coordinates are already done here, so we geocode nothing for hospitals that match.
  - Dataset: <https://hifld-geoplatform.opendata.arcgis.com/datasets/geoplatform::hospitals/about>
  - Weekly-updated mirror (CSV/GeoJSON): <https://github.com/rearc-data/hospitals-hifld>

**Stroke-center designation (which hospitals count as stroke centers):**

- Tristate (NY/NJ/CT) authoritative lists:
  - NY: NYSDOH Stroke Designation Program + searchable directory at <https://profiles.health.ny.gov>
  - NJ: state-designated stroke centers by county (PDF, addresses) at <https://nj.gov/health>
  - CT: DPH certified stroke centers (hospital attestation list) at <https://portal.ct.gov/dph/emergency-medical-services/ems/certified-stroke-centers>
- National single-source options:
  - EMNet **findERnow** (Mass General) compiles all certified/designated stroke centers nationally and links each to its CMS Provider ID; available to researchers on request (emnet@partners.org). The CMS Provider ID is the cleanest join key.
  - The Joint Commission Quality Check directory (also DNV, ACHC/HFAP as other certifying bodies).

**Travel distance to nearest stroke center (derive, not download):**

- v1: haversine distance from county centroid to nearest stroke-center coordinate.
- Later `(?)`: real drive time via a routing engine (OSRM / OpenRouteService).

> **Audit step before any of the above:** confirm what fraction of the stroke-center list actually matches HIFLD cleanly. That single number decides whether geocoding leftovers is a footnote or the main event. This is the first thing to test (see 2b).

### 2b. First concrete deliverable: verified stroke-centers-with-coordinates file

This is the data subproject we already scoped. It is a **join, not a geocode**: HIFLD has coordinates for every hospital but does not flag stroke designation; the designation lists flag stroke centers but mostly give addresses, not coordinates. So we join the two and only geocode whatever fails to match.

`(?)` **Scope of this file: tristate proof-of-concept first, or national?**

- Tristate is fast and uses the three authoritative state lists.
- National is the project's real target. National coordinates come free from HIFLD, but national designation does not scale via per-state PDFs, so the national version leans on EMNet findERnow or Joint Commission for the designation list.
- Decision deferred. Pipeline below is written to handle either.

**Pipeline (v1):**

1. **Audit.** Pull HIFLD hospitals filtered to the target region. Count rows, inspect fields, note the SOURCE/vintage. Do not transform yet.
2. **Pull the stroke-center list.** Tristate: NY + NJ + CT state lists. National: EMNet findERnow file (CMS Provider ID) or Joint Commission directory. `(?)` which source.
3. **Join.** Match the designation list to HIFLD on hospital NAME + ADDRESS (fuzzy match), or on CMS Provider ID if we went the EMNet route.
4. **Verify.** Report the match rate. Any stroke center that fails the join (renamed facility, new hospital) gets its address geocoded with the **US Census Geocoder** (free, no API key, batch up to ~10k addresses). Google/Mapbox are alternatives but bring keys, billing, and usage terms we do not need.
5. **Output (do both, since "file or terminal, whichever is easiest" leaves room):**
   - Write `stroke_centers.csv` and `stroke_centers.geojson` with: name, address, designation tier, latitude, longitude, source, match_method (hifld_match / census_geocode / unmatched).
   - Print a terminal summary: counts by tier and state, plus the list of any unmatched centers for manual review.

**Tooling order (dogma):** Python stdlib + `pandas` + `requests` first. Add `geopandas` only if needed to emit GeoJSON or do spatial joins. No framework. No heavy GIS stack unless the data forces it.

**Deliverable:** a clean, verified stroke-center coordinate table that later feeds SCAI (stroke centers per capita, distance to nearest center) and any map or dashboard.

---

## 3. Tasks (loose, will firm up after data gathering)

### Data engineering `(?)`

- Data collection
- Data cleaning
- Data integration (one tidy county-level table keyed by FIPS)

### EDA

- Descriptive statistics
- Visualizations
- Investigate:
  - Counties with highest stroke mortality
  - Relationships among risk factors
  - Regional differences `(?)`

### Build the Stroke Vulnerability Index

- Variable selection (identify risk factors)
- Standardize data
- PCA `(?)`
- Component interpretation
- Construct the index
- **Deliverables:** PCA results, vulnerability scores, ranking table

### Build the Stroke Care Access Index + spatial analysis

- Access metrics: hospitals per capita, physicians per capita, stroke centers per capita
- Geographic analysis: map stroke mortality, access measures, and vulnerability scores
- Construct the index
- Clustering `(?)`: K-means, county typology analysis
- **Deliverables:** maps, cluster analysis, access index

### Predict stroke mortality (ML)

- Models: linear regression, random forest, XGBoost, etc. `(?)`
- Evaluate with RMSE, MAE, R^2, etc.; compare models to pick the most appropriate
- Interpret with SHAP / feature importance
- Dashboard `(?)`
- **Deliverables:** model comparison, SHAP analysis, dashboard `(?)`

### Policy recommendations

- Translate findings into resource-prioritization recommendations using the priority matrix.

---

## 4. Output / delivery surface `(?)`

We might build a site or a dashboard. Decision deferred until the data and scope firm up. Options, boring first:

- **v1 (now):** a GitHub Pages site that renders this plan and, as we go, hosts EDA figures and static maps. See Section 5.
- **Later:** a static dashboard (pre-rendered Plotly / Observable / plain HTML) can live on the same Pages site.
- **Heavier `(?)`:** an interactive dashboard (Streamlit / Dash) does NOT run on GitHub Pages, which is static-only. That would need a separate host (e.g. Streamlit Community Cloud). Flag this before committing to "interactive," because it changes the deploy story.

---

## 5. Instructions for Claude Code

Two tasks for Code right now: stand up the repo + GitHub Page (5b), and build the stroke-center pipeline from 2b (5c). Both follow the standing constraints in 5d.

### 5a. Suggested repo layout (starting point, not rigid)

```
stroke-burden-index/
  README.md            # short overview, links to the plan and the live page
  docs/                # GitHub Pages source
    index.md           # landing page (can be a copy of this plan)
    _config.yml        # theme only, no build step
  data/
    raw/               # gitignored, never committed
    interim/
    processed/
  notebooks/
  src/
  outputs/
    figures/
    maps/
  .gitignore           # ignores data/raw, secrets, large files
```

### 5b. GitHub Page task

```
GOAL
Stand up a GitHub Pages site for this project that renders the project plan and
will later host static EDA figures and maps. v1 is intentionally minimal:
GitHub's built-in Jekyll renders Markdown to HTML with a built-in theme. No
static-site-generator framework (no MkDocs / Hugo / Docusaurus) at this stage.

FILES IN SCOPE
- /docs/index.md           (the landing page; start from stroke_burden_index_plan.md)
- /docs/_config.yml        (pick a built-in theme, e.g. a minimal one; nothing more)
- /README.md               (short overview + a link placeholder for the live URL)
- /.gitignore              (ignore data/raw/, *.env, *.key, large data files)

CONSTRAINTS
- Read-only audit first: report the current repo state before writing anything.
- Boring solution only. Built-in Jekyll theme, zero build pipeline.
- Do NOT commit any data, secrets, API keys, or tokens. No keys anywhere in the
  repo, especially not at root.
- Prepare everything locally. Then STOP. Do not push to the remote and do not
  enable Pages in repo settings on your own. Publishing this site is a public
  action, so hand it back to <Mikko> to confirm and run the push + enable Pages.
- If a local preview is possible without extra installs, offer the command; do
  not install a toolchain just to preview.

VERIFICATION
- Show the proposed file tree and the full contents of each new/changed file.
- Confirm .gitignore actually excludes data/raw/ and secret patterns.
- State the exact manual steps <Mikko> will take to publish (push, then
  Settings > Pages > source = main branch /docs folder), and the expected URL.

PLAN FIRST
- Before writing files, post a short plain-English plan of what you will create
  and wait for go-ahead.
```

### 5c. Stroke-center pipeline task (from Section 2b)

```
GOAL
Produce a verified table of hospitals that are stroke centers, with latitude and
longitude, output as CSV + GeoJSON and a terminal summary. This is a join
(designation list -> HIFLD coordinates), not a geocode; only unmatched centers
get geocoded via the free US Census Geocoder.

FILES IN SCOPE
- /src/build_stroke_centers.py   (the pipeline)
- /data/raw/                     (downloaded source files; gitignored)
- /outputs/                      (stroke_centers.csv, stroke_centers.geojson)

CONSTRAINTS
- Audit before building: first pull HIFLD for the target region, print row counts
  and field names, and report the match rate against the designation list BEFORE
  doing any geocoding. That match rate decides how much geocoding is needed.
- Region scope is OPEN: <tristate NY/NJ/CT proof-of-concept> OR <national>.
  Ask which before pulling the designation list, since the source differs
  (state lists for tristate; EMNet findERnow or Joint Commission for national).
- Tooling order: Python stdlib + pandas + requests first. Add geopandas only if
  needed for GeoJSON output or spatial joins. No framework.
- US Census Geocoder only for leftovers (free, no API key, batch). Do not wire in
  Google/Mapbox or any keyed service.
- Treat the workspace as read-only by default. Do not delete anything. Write only
  to /outputs and /data/raw.
- No API keys committed or stored in readable repo locations.

VERIFICATION
- Print: total stroke centers, counts by tier and by state, match rate against
  HIFLD, and the list of any unmatched centers.
- Output schema must include: name, address, tier, latitude, longitude, source,
  match_method (hifld_match | census_geocode | unmatched).
- Spot-check a few known centers against their published addresses.

PLAN FIRST
- Post the plain-English approach and the chosen region scope, then wait for
  go-ahead before writing code.
```

### 5d. Standing constraints for Code (apply to every task)

- **Plan in plain English first.** What, why, how, before any code.
- **Provide actual working code, not skeletons**, but remind <Mikko> to read it through and understand it. Flag tricky or non-obvious parts.
- **Code headers:** include a FILE MAP header (major sections with line ranges + purpose) and inline tag comments: `// TWEAK:` safe adjustments, `// CHANGE ME:` required before running, `// DO NOT TOUCH:` load-bearing logic with a reason.
- **Safety:** read-only by default. Require an explicit "yes, delete [specific thing]" before any write/delete that is destructive. Use dry-run, soft deletes, backups, and staging before prod. Never place API keys at root or anywhere readable.
- **Anti-over-engineering:** audit existing tools first, then stdlib/CLI, then library, then framework, then build. Define v1 explicitly and keep a two-week shipping horizon. Ask "can I buy this instead?" before coding.
- **Publishing/public actions** (pushing to a public repo, enabling Pages, deploying): prepare, then stop and hand back to <Mikko> to confirm.

---

## Open questions to resolve once we have data

- `(?)` Rename SVI to avoid the CDC Social Vulnerability Index collision.
- `(?)` Stroke-center file scope: tristate proof-of-concept or national.
- `(?)` Which single source for national stroke-center designation (EMNet vs Joint Commission).
- `(?)` Does County Health Rankings cover enough SVI variables to skip multi-source assembly.
- `(?)` Final SVI / SCAI variable lists (trim after seeing data quality and coverage).
- `(?)` Whether to do PCA for SVI and K-means for the typology, or simpler approaches.
- `(?)` Ranking/combination method for the final national stroke-burden ranking.
- `(?)` Output surface: static maps only, or an interactive dashboard (changes the host).
- `(?)` Travel-distance metric: haversine for v1, routed drive time later.
