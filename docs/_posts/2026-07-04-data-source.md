---
layout: post
title: "Data Source"
date: 2026-07-04 12:00:00 -0400
image: data-source.svg
description: "Every dataset behind the project — CDC, Census, CMS, HRSA, and state stroke registries."
---

County-level data for all 91 NY/NJ/CT counties, from public sources:

- **CDC WONDER** — stroke mortality (2018–2024 pooled)
- **CDC PLACES** — health prevalence (smoking, obesity, diabetes, hypertension…)
- **US Census ACS** — demographics and socioeconomics
- **CMS Hospital Cost Reports & HRSA** — hospital beds, physicians, neurologists
- **State health departments (NY/NJ/CT)** — designated stroke centers
- **OpenRouteService** — drive times from each county's population center

*Draft skeleton — jane is writing this section (Discord 7/7): describe each
variable in detail here; the methodology section just lists them per index.*


# Data Sources

## Overview

The Stroke Burden Index integrates multiple publicly available datasets to construct a county-level database for New York, New Jersey, and Connecticut (91 counties). Each dataset contributes a different aspect of stroke burden, including demographics, socioeconomic characteristics, health risk factors, healthcare resource availability, geographic accessibility, and stroke mortality.

All datasets were standardized to five-digit county FIPS codes before being merged into a single master database. County-level variables were cleaned, validated, and transformed where necessary to ensure consistency across data sources.

---

# American Community Survey (ACS)

**Source:** U.S. Census Bureau, American Community Survey (ACS) 5-Year Estimates

The ACS provides county-level demographic and socioeconomic characteristics used in the Stroke Risk Index (SRI), including:

- Population aged 65 years and older
- Poverty rate
- Educational attainment
- Health insurance coverage
- Household income categories
- Total population

These variables represent important social determinants of health associated with stroke risk.

---

# CDC PLACES

**Source:** Centers for Disease Control and Prevention (CDC) PLACES

CDC PLACES provides county-level estimates of health behaviors and chronic disease prevalence. Variables incorporated into the Stroke Risk Index include:

- Smoking prevalence
- Obesity prevalence
- Diabetes prevalence
- Hypertension prevalence
- High cholesterol prevalence
- Physical inactivity
- Binge drinking prevalence
- Stroke prevalence

These measures capture modifiable stroke risk factors at the population level.

---

# CDC WONDER

**Source:** CDC WONDER Multiple Cause of Death Database

Age-adjusted stroke mortality rates were obtained from CDC WONDER using pooled mortality data from **2018–2024**.

Two mortality measures were included:

- Acute stroke mortality
- Sequelae of stroke mortality

Although stroke mortality was not included directly in the Stroke Risk Index, it was used throughout exploratory data analysis to evaluate relationships between candidate predictors and observed stroke outcomes.

---

# Population Density

Population density was calculated by combining county population estimates with county land area obtained from the U.S. Census Bureau.

Because population density exhibited substantial positive skew resulting from several highly urban counties, a logarithmic (`log1p`) transformation was applied before inclusion in the Stroke Risk Index.

---

# Healthcare Resource Data

Multiple public healthcare datasets were combined to construct county-level measures of healthcare availability for the Stroke Care Access Index (SCAI).

Variables include:

- Hospital beds per 100,000 population
- Primary care physicians per 100,000 population
- Neurologists per 100,000 population
- Hospitals per 100,000 population
- Certified stroke centers per 100,000 population

Hospital locations were aggregated to the county level using standardized five-digit FIPS codes. Provider counts and hospital resources were converted to population-adjusted rates using county population estimates from the American Community Survey.

Exploratory analysis was used to evaluate redundancy among healthcare resource variables prior to constructing the final index.

---

# Geographic Accessibility

Geographic accessibility measures were generated using county population centers and the locations of certified stroke centers.

The final accessibility dataset includes:

- Drive time to the nearest stroke center
- Drive time to the nearest advanced stroke center
- Distance to the nearest stroke center
- Distance to the nearest advanced stroke center

Driving times were calculated using the OpenRouteService routing engine, while straight-line distances were calculated using county centroid and stroke center coordinates. These variables form the Geographic Accessibility Index (GAI).

---

# Geographic Reference Data

County boundaries and FIPS codes were standardized using U.S. Census geographic reference files.

Because Connecticut transitioned from historical counties to planning regions, a Connecticut county crosswalk was used to preserve compatibility across datasets that continue to report data using historical county definitions.

---

# Data Integration

All datasets were merged using standardized five-digit county FIPS codes.

Data integration included:

- Validation of county identifiers
- Standardization of variable names
- Conversion of provider counts to rates per 100,000 population
- Verification of county-level joins
- Resolution of Connecticut county crosswalks
- Missing value assessment and correction

The final integrated database contains one observation for each of the **91 counties** across New York, New Jersey, and Connecticut and serves as the input for construction of the Stroke Risk Index (SRI), Stroke Care Access Index (SCAI), and Geographic Accessibility Index (GAI).
