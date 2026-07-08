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

The American Community Survey (ACS) provides county-level demographic and socioeconomic characteristics that are strongly associated with stroke risk and healthcare access. These variables primarily contribute to the Stroke Risk Index (SRI).

| Variable | Description | Why Included |
|----------|-------------|--------------|
| `total_pop` | Total county population estimate. | Used to calculate per-capita healthcare resource measures and population-adjusted rates. |
| `pcnt_65_plus` | Percentage of residents aged 65 years and older. | Stroke incidence and mortality increase substantially with age, making older populations more vulnerable. |
| `poverty_rate` | Percentage of the population living below the federal poverty line. | Poverty is associated with reduced access to healthcare, poorer health outcomes, and increased stroke risk. |
| `pcnt_insured` | Percentage of residents with health insurance coverage. | Insurance improves access to preventative care, primary care, and specialist services. |
| `pcnt_uninsured` | Percentage of residents without health insurance (derived from insurance coverage). | Used in the SCAI because uninsured populations often experience reduced access to healthcare services. |
| `pcnt_bachelors` | Percentage of adults with at least a bachelor's degree. | Educational attainment is associated with healthier lifestyles, better healthcare utilization, and lower stroke risk. |
| `pcnt_low_income` | Percentage of residents classified as low income. | Represents socioeconomic disadvantage beyond the federal poverty threshold. |
| `pcnt_middle_class` | Percentage of residents in the middle-income category. | Used during exploratory analysis to characterize county socioeconomic composition. |
| `pcnt_upper_class` | Percentage of residents in the upper-income category. | Represents socioeconomic advantage and was evaluated during variable selection. |

These variables represent important social determinants of health associated with stroke risk.

---

# CDC PLACES

**Source:** Centers for Disease Control and Prevention (CDC) PLACES

CDC PLACES provides county-level estimates of chronic disease prevalence and health behaviors known to influence stroke risk.

| Variable | Description | Why Included |
|----------|-------------|--------------|
| `smoking_prevalence` | Percentage of adults who currently smoke cigarettes. | Smoking is a major modifiable risk factor for stroke and cardiovascular disease. |
| `obesity_prevalence` | Percentage of adults classified as obese. | Obesity contributes to hypertension, diabetes, and cardiovascular disease. |
| `diabetes_prevalence` | Percentage of adults diagnosed with diabetes. | Diabetes substantially increases the risk of ischemic stroke. |
| `hypertension_prevalence` | Percentage of adults diagnosed with hypertension. | High blood pressure is the strongest modifiable risk factor for stroke. |
| `high_cholesterol_prevalence` | Percentage of adults with high cholesterol. | Elevated cholesterol contributes to atherosclerosis and ischemic stroke. |
| `physical_inactivity` | Percentage of adults reporting no leisure-time physical activity. | Physical inactivity increases cardiovascular disease and stroke risk. |
| `binge_drinking_prevalence` | Percentage of adults reporting binge drinking behavior. | Excessive alcohol consumption is associated with increased stroke risk. |
| `stroke_prevalence` | Percentage of adults who have previously experienced a stroke. | Indicates the existing burden of cerebrovascular disease within a county. |

These measures capture modifiable stroke risk factors at the population level.

---

# CDC WONDER

**Source:** CDC WONDER Multiple Cause of Death Database

Age-adjusted stroke mortality rates were obtained from CDC WONDER using pooled mortality data from **2018–2024**.

Two stroke mortality measures were included:

| Variable | Description | Why Included |
|----------|-------------|--------------|
| `acute_stroke_mortality_per_100k` | Age-adjusted mortality rate for acute stroke (per 100,000 population). | Used during exploratory analysis to evaluate relationships between candidate variables and observed stroke mortality. |
| `sequelae_stroke_mortality_per_100k` | Age-adjusted mortality rate for long-term stroke complications (per 100,000 population). | Provides an additional measure of stroke-related mortality for comparison and validation. |

Although stroke mortality was not included directly in the Stroke Risk Index, it was used throughout exploratory data analysis to evaluate relationships between candidate predictors and observed stroke outcomes.

---

# Population Density

Population density was calculated by combining county population estimates with county land area obtained from the U.S. Census Bureau.

Because population density exhibited substantial positive skew resulting from several highly urban counties, a logarithmic (`log1p`) transformation was applied before inclusion in the Stroke Risk Index.

| Variable | Description | Why Included |
|----------|-------------|--------------|
| `pop_density` | Population per square mile. | Population density reflects differences between urban and rural environments, influencing healthcare access, healthcare infrastructure, and population health. A log transformation was applied prior to PCA because of substantial right skew. |

---

# Healthcare Resource Data

**Sources:**

- **Centers for Medicare & Medicaid Services (CMS) Hospital General Information** – General hospital locations and facility information
- **Centers for Medicare & Medicaid Services (CMS) Hospital Cost Reports** – Licensed hospital bed counts
- **Health Resources and Services Administration (HRSA) Area Health Resources Files (AHRF)** – County-level primary care physician and neurologist counts
- **State Stroke Center Registries (New York, New Jersey, and Connecticut)** – Certified stroke center locations and designations
- **American Community Survey (ACS)** – County population estimates used to calculate population-adjusted rates

| Variable | Description | Why Included |
|----------|-------------|--------------|
| `hospitals_per_100k` | General hospitals per 100,000 population. | Represents the overall availability of hospital facilities within a county. |
| `hospital_beds_per_100k` | Licensed hospital beds per 100,000 population. | Measures inpatient healthcare capacity and the ability to accommodate patients requiring hospitalization. |
| `pcp_per_100k` | Primary care physicians per 100,000 population. | Primary care physicians play an important role in stroke prevention through management of chronic conditions and risk factors. |
| `neurologists_per_100k` | Neurologists per 100,000 population. | Neurologists provide specialized diagnosis and treatment for stroke and other neurological disorders. |
| `stroke_centers_per_100k` | Certified stroke centers per 100,000 population. | Represents the availability of specialized facilities capable of providing evidence-based acute stroke care. |

Hospital locations were aggregated to the county level using standardized five-digit FIPS codes. Provider counts and hospital resources were converted to population-adjusted rates using county population estimates from the American Community Survey.

Exploratory analysis was used to evaluate redundancy among healthcare resource variables prior to constructing the final index.

---

# Geographic Accessibility Data

Geographic accessibility measures were generated using county population centers and the locations of certified stroke centers.

County boundaries and FIPS codes were standardized using U.S. Census geographic reference files.

Because Connecticut transitioned from historical counties to planning regions, a Connecticut county crosswalk was used to preserve compatibility across datasets that continue to report data using historical county definitions.

| Variable | Description | Why Included |
|----------|-------------|--------------|
| `drive_time_min` | Estimated driving time to the nearest certified stroke center. | Represents the time required for residents to access emergency stroke care. |
| `drive_time_advanced` | Estimated driving time to the nearest advanced stroke center. | Measures accessibility to facilities providing advanced stroke interventions. |
| `nearest_stroke_distance` | Straight-line distance to the nearest certified stroke center. | Provides a simple measure of geographic proximity independent of the road network. |
| `nearest_stroke_distance_advanced` | Straight-line distance to the nearest advanced stroke center. | Measures proximity to advanced stroke treatment facilities. |

Driving times were calculated using the OpenRouteService routing engine, while straight-line distances were calculated using county centroid and stroke center coordinates. These variables form the Geographic Accessibility Index (GAI).

---

# Variable Usage by Index

| Variable Group | SRI | SCAI | GAI |
|---------------|:---:|:----:|:---:|
| Demographics | ✓ | | |
| Socioeconomic | ✓ | ✓ | |
| Health behaviors | ✓ | | |
| Hospital resources | | ✓ | |
| Healthcare providers | | ✓ | |
| Stroke centers | | ✓ | ✓ |
| Travel time | | | ✓ |
| Travel distance | | | ✓ |
| Stroke mortality | EDA only | EDA only | EDA only |

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
