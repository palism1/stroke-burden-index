---
layout: default
title: Stroke Burden Index
---

# Stroke Burden Index

**Where do stroke risk and poor access to care overlap? Identifying high-priority stroke intervention areas in the US.**

---

## Questions we're answering

- Which counties exhibit the highest stroke vulnerability, and why?
- Which counties have the poorest access to stroke care?
- Which factors (socioeconomic, health, geographic) most strongly predict stroke mortality?
- How can resources be prioritized to reduce stroke burden?

**Combined:** Which U.S. counties face the greatest stroke burden due to a combination of stroke risk factors and limited access to stroke care?

---

## Main idea

We build three components and combine them into a single headline index.

| Index | What it measures |
|---|---|
| **Stroke Vulnerability Index (SVI)** | Likelihood a community will experience stroke-related health problems |
| **Stroke Care Access Index (SCAI)** | Availability of treatment resources |
| **Geographic Accessibility Index (GAI)** | Drive time and distance to the nearest stroke center |
| **Stroke Burden Priority Index (SBPI)** | Combined ranking of overall stroke burden |

Every index follows the same pipeline: **raw → align direction → standardize → PCA → normalize (0–100)**.

---

## Stroke Vulnerability Index (SVI)

**Variables:**

Demographics: % population over 65, population density

Socioeconomic: poverty rate, percent low income, education level

Health: smoking prevalence, obesity prevalence, diabetes prevalence, physical inactivity, hypertension prevalence, high cholesterol prevalence, binge drinking prevalence, stroke prevalence

**Direction:** higher value = worse vulnerability. Percent low income already points the harmful way (higher = worse), so it is not flipped. Protective variables (education) are flipped before standardizing.

---

## Stroke Care Access Index (SCAI)

**Variables:**

- Hospitals per capita
- Stroke centers per capita (basic and advanced)
- Primary care physicians per capita
- Insurance coverage
- Neurologists per capita

**Stroke center tiers:** Acute + Primary = Basic care. Thrombectomy-capable + Comprehensive = Advanced care.

**Direction:** higher value = better access.

---

## Geographic Accessibility Index (GAI)

Built from 4 variables: drive time to nearest basic stroke center, drive time to nearest advanced stroke center, distance to nearest basic stroke center, distance to nearest advanced stroke center.

All 4 run through the standard pipeline: align direction (flip so higher = better access) → standardize → PCA → normalize to 0–100.

`0` = worst access (far), `100` = best access (close).

---

## Stroke Burden Priority Index (SBPI)

**Option 1 — weighted index:**

```
SBPI = 0.5 × SVI + 0.25 × (Access Deficit) + 0.25 × (Distance Deficit)
```

Where Access Deficit = 100 − SCAI and Distance Deficit = 100 − GAI. Vulnerability carries the most weight; weights are tunable.

**Option 2 — quadrant classification:**

| Priority | Criteria | Score |
|---|---|---|
| Critical | Top 25% SVI + bottom 25% SCAI + top 25% distance | 4 |
| High | Top 25% SVI + bottom 50% SCAI | 3 |
| Moderate | One elevated risk factor | 2 |
| Low | Good access + low vulnerability | 1 |

**Priority matrix:**

| | Good access | Poor access |
|---|---|---|
| **Low vulnerability** | Low priority | Monitor |
| **High vulnerability** | Prevention focus | Highest priority |
| **Very high vulnerability** | Resource allocation | Critical intervention zone |

Counties in the high vulnerability + poor access corner are the **stroke care deserts** — the core target of this project.

---

## Geospatial analysis

Focused on NY, NJ, and CT. We want to know: are there geographic barriers to stroke care in the region, and do those barriers correspond to higher stroke burden?

1. Map stroke centers as points over county boundaries
2. Calculate drive time and distance from each county's population center to the nearest basic and advanced stroke center
3. Choropleth map of counties colored by travel time band (0–15 min, 15–30 min, 30–60 min, 60+ min)
4. Top 5 and bottom 5 counties per state by accessibility
5. Scatter: distance to stroke center vs. stroke mortality rate
6. Scatter: distance vs. SVI — are vulnerable populations also geographically isolated?
7. Accessibility × Vulnerability matrix (X = SVI, Y = accessibility; split at 75th/25th percentile into quadrants)
8. Hotspot analysis (optional): Local Moran's I or Getis-Ord Gi* to identify statistically significant clusters

---

## Visualization

One master interactive choropleth map (Plotly or Datawrapper) colored by SBPI score. Hovering over a county shows SVI, SCAI, and estimated travel time to nearest stroke center.

---

## Tasks

1. **Data engineering** — collection, cleaning, integration into one county-level table keyed by FIPS
2. **EDA** — descriptive statistics, visualizations, relationships among risk factors, regional differences
3. **SVI** — variable selection, PCA, vulnerability scores, ranking table
4. **SCAI + spatial analysis** — access metrics, geographic analysis, index, clustering
5. **Predict stroke mortality (ML)** — linear regression, random forest, XGBoost; evaluate with RMSE / MAE / R²; interpret with SHAP
6. **Policy recommendations** — translate findings into resource-prioritization recommendations

---

## Data sources

- [CDC WONDER](https://wonder.cdc.gov/) — stroke mortality by county
- [County Health Rankings](https://www.countyhealthrankings.org/health-data) — socioeconomic and health variables
- [HRSA Area Health Resources Files](https://data.hrsa.gov/topics/health-workforce/nchwa/ahrf) — physician workforce by county
- [USDA Rural-Urban Continuum Codes](https://www.ers.usda.gov/data-products/rural-urban-continuum-codes) — urban/rural classification
- [NYSDOH Stroke Centers](https://profiles.health.ny.gov) — NY designated stroke centers
- [CT DPH Stroke Centers](https://portal.ct.gov/dph/emergency-medical-services/ems/certified-stroke-centers) — CT certified stroke centers
- [NJ Stroke Centers](https://nj.gov/health) — NJ state-designated stroke centers

---

## Status

Data gathering is the active phase. ACS demographic data, CDC WONDER mortality, CDC PLACES health prevalence, population density, and geographic accessibility (drive time and distance to nearest basic and advanced stroke center for all 91 NY/NJ/CT counties) are collected. SCAI variables (hospitals per capita, physicians per capita, stroke centers per capita) are in progress.

[Interactive county dashboard (work in progress)](./dashboard/) · [Full methodology and open questions](./plan.html)
