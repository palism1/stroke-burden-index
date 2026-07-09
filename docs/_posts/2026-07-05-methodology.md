---
layout: post
title: "Methodology"
date: 2026-07-05 12:00:00 -0400
image: methodology.svg
description: "How the indices work: the variables in each, why PCA, and how skew and direction are handled."
---

Every index follows the same recipe: **raw variables → fix skew (log
transforms) → align direction → standardize → PCA → a 0–100 score**.

- **Stroke Risk Index (SRI)** — 13 demographic, socioeconomic, and health
  variables (higher = more risk).
- **Stroke Care Access Index (SCAI)** — hospital beds, primary care physicians,
  neurologists, and insurance coverage (higher = better access).
- **Geographic Accessibility Index (GAI)** — drive time and distance to the
  nearest stroke centers (higher = better access).
- **Stroke Burden Priority Index (SBPI)** — the headline combination:
  50% risk + 30% access deficit + 20% distance deficit, plus a 4-level
  priority class.

*Draft skeleton — jane is writing this section (Discord 7/7). Full variable
detail belongs in the Data Source section; list per-index variables here.*


## Overview

The Stroke Burden Index project constructs three county-level indices that measure aspects of a county's stroke burden:

- **Stroke Risk Index (SRI):** Measures underlying stroke risk using demographic, socioeconomic, and health-related risk factors.
- **Stroke Care Access Index (SCAI):** Measures the availability of stroke care resources, including hospitals, hospital capacity, healthcare providers, and certified stroke centers.
- **Geographic Accessibility Index (GAI):** Measures the geographic accessibility of stroke care using travel time and distance to the nearest stroke centers.

Each index was developed independently using county-level data for New York, New Jersey, and Connecticut. Prior to index construction, exploratory data analysis (EDA) was performed to evaluate missing data, variable distributions, correlations, and the suitability of the selected variables. Index-specific preprocessing, such as variable transformations and direction alignment, was applied where appropriate before constructing each index using principal component analysis (PCA). The resulting indices are standardized to a common 0–100 scale to facilitate interpretation and comparison across counties. The methodology for each index is described in the following sections, while implementation details of the PCA workflow are documented separately in the Pipeline Guide.


## Why Principal Component Analysis (PCA)?

Each index in this project combines several related variables intended to measure a common underlying concept, such as stroke risk, healthcare access, or geographic accessibility. Because many of these variables are correlated, combining them directly could overweight information that is represented by multiple measures.

Principal Component Analysis (PCA) was selected as a data-driven approach for constructing the indices because it:

- Reduces multiple correlated variables into a smaller number of composite components.
- Minimizes redundancy among variables while retaining the greatest amount of information.
- Determines variable weights objectively from the data rather than assigning subjective weights.
- Produces a single continuous score that can be compared across counties.

For each index, the first principal component (PC1) was retained because it explained the largest proportion of variation among the selected variables. The resulting component scores were then normalized to a 0–100 scale to improve interpretability while preserving the relative ranking of counties.


## Data Preprocessing

Prior to index construction:

- County datasets were merged using five-digit FIPS codes.
- Missing values were identified and resolved during data integration.
- Variables were transformed where appropriate to reduce skewness.
- Variables were aligned so that higher values consistently represented greater risk or better access.
- Continuous variables were standardized before PCA.

## Interpreting the Indices

All indices are normalized to a 0–100 scale.

| Index | Higher score indicates |
|--------|------------------------|
| SRI | Greater stroke vulnerability |
| SCAI | Better healthcare access |
| GAI | Better geographic accessibility |
| SBPI | Greater overall stroke burden |

## Stroke Risk Index (SRI)

1. **Align direction** so higher value = worse vulnerability. Percent low income already points the harmful way (higher = worse), so it is left as-is. Flip "protective" variables:
   - education → `-(education)`
2. **Standardize** (scale) all variables.
3. **Compute** the index with **PCA** (use PC1).
4. **Interpret:** higher PC1 → higher vulnerability. The PC1 sign check is automatic — `index_pipeline.build_index` orients the index against the aligned variables, so there is no manual "flip the index if it came out backwards" step. See `docs/pipeline_guide.md`.
5. **Normalize to 0–100.** `0` = lowest risk, `100` = highest risk.

### Variables

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

### Exploratory Data Analysis

Prior to PCA, descriptive statistics, missing value assessment, histograms, and Pearson correlation analyses were performed for each candidate variable.

Population density exhibited a strong positive skew (skewness = 5.61) due to several densely populated urban counties. A `log1p` transformation reduced the skewness to 0.69 before PCA, while preserving the ordering of counties.

Our correlation analysis identified hypertension prevalence, smoking prevalence, obesity prevalence, diabetes prevalence, and the percentage of adults aged 65 years and older as the variables most strongly associated with county-level stroke mortality. Protective variables, including educational attainment, were reversed prior to PCA so that higher values consistently represented greater stroke vulnerability. 

### PCA Results

The standardized variables were combined using PCA, with the first principal component retained as the Stroke Risk Index. Variable loadings and the explained variance ratio were evaluated to ensure that the selected variables captured a common measure of stroke vulnerability before the resulting scores were normalized to a 0–100 scale. From our PCA analysis, we found that the first principal component explained about 52.2% of the total variance among the selected stroke risk variables. This indicates that the demographic, socioeconomic, and health-related variables share a common underlying pattern of stroke vulnerability while still capturing multiple distinct dimensions of risk. Retaining the first principal component provides a reasonable summary of overall stroke risk without discarding the additional variation contributed by individual risk factors. This is reasonable, as these factors are related, but not perfectly correlated. 

## Stroke Care Access Index (SCAI)

1. **Align direction** so higher value = better access. Reverse the rurality variable if it is used.
2. **Standardize** (scale) all variables.
3. **Compute** the index with **PCA**.
4. **Check direction** (flip the sign if PC1 points the wrong way).
5. **Normalize to 0–100.** `0` = worst access, `100` = best access.

### Variables

The Stroke Care Access Index (SCAI) measures the availability of healthcare resources related to stroke prevention and treatment.

The final index includes:

| Variable | Description |
|----------|-------------|
| `hospital_beds_per_100k` | Hospital beds per 100,000 population |
| `pcp_per_100k` | Primary care physicians per 100,000 population |
| `neurologists_per_100k` | Neurologists per 100,000 population |
| `pcnt_uninsured` | Percent uninsured |

Candidate variables including hospitals per 100,000 population and stroke centers per 100,000 population were evaluated during exploratory analysis before the final variable set was selected. However, we found these two variables to be a biased and inaccurate measure of access to care. Why? Some rural counties may have one basic community hospital, where stroke-related care is extremely limited. However, their small population may cause the hospitals per 100k rate to become over-inflated. On the other hand, urban counties, such as New York and Queens, have a lower hospitals per 100k rate due to their large population, as they have larger, more advanced hospitals with a significantly larger number of beds and physicians. Due to this, hospitals per 100k actually had a positive correlation with stroke mortality rate. Similar logic applies to stroke centers per 100k. Thus, hospital beds per 100k appeared to be a much better indicator of access to medical care. Due to these reasons, we chose to leave these two variables out of the index, but still include them in the exploratory data analysis for informational purposes.


### Exploratory Data Analysis

Descriptive statistics, missing value assessment, distribution plots, skewness calculations, and both Pearson and Spearman correlation analyses were performed for all candidate healthcare access variables.

Several important relationships emerged during EDA. Hospital bed availability, primary care physician density, and neurologist density were positively correlated, indicating that these variables measured similar aspects of healthcare resource availability. Hospitals per 100,000 population and stroke centers per 100,000 population overlapped for 29 counties, primarily in smaller counties where every hospital is designated as a stroke center. Despite this overlap, correlation analysis showed that hospitals per 100,000 population captured a different aspect of healthcare access than provider availability.

The analysis also identified counties with no neurologists despite having certified stroke centers, suggesting that specialist availability varies independently from hospital designation. These findings informed the final selection of variables included in the PCA.


### PCA Results

The first principal component (PC1) was retained as the Stroke Care Access Index. Primary care physician density, neurologist density, and hospital bed availability exhibited the largest positive loadings on the first principal component, indicating that they contributed most strongly to variation in healthcare access across counties. Percent uninsured had a comparatively small loading after direction alignment. Final index scores were normalized to a 0–100 scale, where higher values indicate greater access to stroke care. From our PCA analysis, we found that the first principal component explained 53.9% of the total variance among the healthcare access variables. This suggests that the selected measures capture a common dimension of healthcare access while also reflecting different aspects of resource availability, including provider density, hospital capacity, and insurance coverage. The first principal component therefore provides an appropriate summary measure of stroke care access across counties. 



## Geographic Accessibility Index (GAI)

### Variables

The Geographic Accessibility Index (GAI) measures physical accessibility to stroke care using travel time and travel distance to the nearest certified stroke centers.

| Variable | Description |
|----------|-------------|
| `drive_time_min` | Drive time to the nearest basic stroke center |
| `drive_time_advanced` | Drive time to the nearest advanced stroke center |
| `nearest_stroke_distance` | Distance to the nearest basic stroke center |
| `nearest_stroke_distance_advanced` | Distance to the nearest advanced stroke center |

- All 4 run through the standard pipeline: **align direction** so higher = better access (flip the variables, since lower drive time / distance = better access) → **standardize** → **PCA** → **normalize to 0–100**.
- `0` = worst access (far), `100` = best access (close), same orientation as SCAI.

### Exploratory Data Analysis

The geographic accessibility dataset was evaluated using descriptive statistics, missing value assessment, histograms, boxplots, state-level comparisons, correlation matrices, and county rankings.

Summary statistics show a median drive time of approximately 17 minutes to the nearest basic stroke center, although accessibility varied substantially across counties.

Distribution plots demonstrated that travel time and travel distance variables were positively skewed, reflecting a small number of counties with substantially poorer geographic access than the remainder of the study region. Correlation analysis showed strong relationships between straight-line distance and estimated driving time for both basic and advanced stroke centers, indicating that these variables measured a common underlying accessibility construct.

Additional analyses comparing geographic accessibility with acute stroke mortality revealed only weak positive associations, suggesting that geographic accessibility alone does not fully explain variation in county-level stroke mortality and should be interpreted alongside healthcare resource availability and underlying stroke risk.

Because shorter travel times and shorter travel distances represent better accessibility, all four variables were reversed prior to PCA so that higher values consistently represented better geographic access.


### PCA Results

The transformed and standardized accessibility variables were combined using principal component analysis. All four travel variables contributed nearly equally to the first principal component, indicating that each measure captured similar information regarding geographic accessibility. The resulting scores were normalized to a 0–100 scale, where higher values indicate better geographic access to stroke care. From our PCA analysis, we found that the first principal component explained 77.0% of the total variance among the geographic accessibility variables. This indicates that travel time and travel distance to stroke centers measure a strong common underlying dimension of geographic accessibility. The high proportion of explained variance demonstrates that a single principal component effectively summarizes differences in geographic access to stroke care across counties.


---




## Stroke Burden Priority Index (SBPI)

### Purpose

The Stroke Burden Priority Index (SBPI) was developed to integrate the three component indices into a single measure of overall stroke burden. While the Stroke Risk Index (SRI), Stroke Care Access Index (SCAI), and Geographic Accessibility Index (GAI) each capture a different dimension of stroke burden, the SBPI provides a comprehensive ranking of counties by simultaneously considering population risk, healthcare resource availability, and geographic access to stroke care.

The SBPI was calculated as a weighted combination of the three standardized indices:

\[
\text{SBPI} = 0.50(\text{SRI}) + 0.30(100-\text{SCAI}) + 0.20(100-\text{GAI})
\]

This approach assigns a 50% weight to stroke risk, 30% weight to healthcare resource availability, and 20% weight to geographic accessibility, producing a single composite score that identifies counties with the greatest overall need for public health intervention. Index weights were decided by the strength of their association with the stroke mortality rate. Greater weight was assigned to the Stroke Risk Index (50%) because underlying population risk was considered the primary driver of stroke burden. The remaining weights emphasized healthcare resource availability (30%) and geographic accessibility (20%), ensuring that counties with limited access to stroke care received higher priority while maintaining population risk as the dominant component.

### Interpretation

Higher SBPI scores indicate counties where elevated stroke risk coincides with limited healthcare resources and poor geographic accessibility. Lower scores represent counties with lower stroke risk and stronger access to stroke care. The SBPI serves as the final prioritization metric used to identify counties where targeted investments in prevention, healthcare infrastructure, and emergency stroke services may have the greatest impact.

---


## Geospatial Analysis

Geospatial analyses were performed to examine the spatial distribution of stroke care resources and evaluate geographic accessibility across New York, New Jersey, and Connecticut. County boundaries, stroke center locations, and county population centers were combined to quantify spatial access to stroke care and identify areas with limited access to specialized services.

County boundaries were obtained from the 2020 U.S. Census TIGER/Line shapefiles to maintain consistency with historical Connecticut county definitions used throughout the project.

---

### Mapping Stroke Centers

Certified stroke centers were mapped to visualize the geographic distribution of stroke care resources throughout the study region. Two categories of facilities were considered:

- **Basic Stroke Centers**, including Primary Stroke Centers (PSC) and Acute Care Stroke Centers (ACSC)
- **Advanced Stroke Centers**, including Thrombectomy-Capable Stroke Centers (TSC) and Comprehensive Stroke Centers (CSC)

Basic stroke centers represent the minimum level of certified stroke care capable of rapidly diagnosing and treating acute stroke, including the administration of thrombolytic therapy. Advanced stroke centers provide higher levels of specialized care, including mechanical thrombectomy, neurosurgical services, and comprehensive management of complex stroke cases.

Mapping these facilities provided an initial assessment of healthcare resource distribution prior to calculating travel times and distances. The maps demonstrated that basic stroke centers are distributed throughout much of the tri-state region, while advanced stroke centers are fewer in number and are concentrated primarily within major metropolitan areas, including New York City, northern New Jersey, Hartford, and New Haven. In contrast, many rural counties in northern New York and northwestern Connecticut are located substantially farther from advanced stroke care.

These spatial patterns motivated the subsequent development of the Geographic Accessibility Index (GAI), which quantifies county-level accessibility using estimated travel times and distances to both basic and advanced stroke centers.

