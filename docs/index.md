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
| **Geographic Access Score** | Travel distance to the nearest stroke center |
| **Stroke Burden Priority Index (SBPI)** | Combined ranking of overall stroke burden |

Every index follows the same pipeline: **raw → align direction → standardize → PCA → normalize (0–100)**.

---

## Stroke Vulnerability Index (SVI)

**Variables:**

Demographics: % population over 65, population density

Socioeconomic: poverty rate, median income, education level

Health: smoking prevalence, obesity prevalence, diabetes prevalence, physical inactivity, hypertension prevalence

**Direction:** higher value = worse vulnerability. Protective variables (income, education) are flipped before standardizing.

---

## Stroke Care Access Index (SCAI)

**Variables:**

- Hospitals per capita
- Stroke centers per capita
- Primary care physicians per capita
- Insurance coverage
- Neurologists per capita

**Direction:** higher value = better access.

---

## Geographic Access Score

Travel distance (and estimated drive time) from each county's population center to the nearest stroke center, normalized to 0–100. Higher = better access (closer).

---

## Stroke Burden Priority Index (SBPI)

**Option 1 — weighted index:**

```
SBPI = 0.5 × SVI + 0.3 × (Access Deficit) + 0.2 × (Distance Deficit)
```

Where Access Deficit = 100 − SCAI and Distance Deficit = 100 − Distance Score. Vulnerability carries the most weight.

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
2. Calculate drive time and distance from each county's population center to the nearest stroke center
3. Choropleth map of counties colored by distance band (0–10 mi, 10–25 mi, 25–50 mi, 50+ mi)
4. Top 5 and bottom 5 counties per state by accessibility
5. Scatter: distance to stroke center vs. stroke mortality rate
6. Scatter: distance vs. SVI — are vulnerable populations also geographically isolated?
7. Accessibility × Vulnerability matrix (quadrant plot)
8. Hotspot analysis (optional): Local Moran's I or Getis-Ord Gi* to identify statistically significant clusters

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

---

## Status

Data gathering is the active phase. ACS demographic data, CDC WONDER mortality, and geographic accessibility data (drive time and distance to nearest stroke center for all 91 NY/NJ/CT counties) are collected. SCAI variables (hospitals per capita, physicians per capita) and SVI health variables (CDC PLACES) are in progress.

[Full methodology and open questions](./plan.html)
