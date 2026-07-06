## Data Dictionary

Documents all variables across the project's county-level data files. Use this as the reference when naming columns in any new data you bring in.

---

## Naming conventions

Follow these for any new files or variables added to the project.

- **Column names:** lowercase snake_case, no spaces, no special characters except underscores. Example: `pcp_per_100k`, not `PCP Per 100k` or `pcp-per-100k`.
- **State:** two-letter abbreviation, uppercase. `NY`, `NJ`, `CT`. Not `New York`.
- **County:** name only, no "County" suffix. `Albany`, not `Albany County`.
- **FIPS:** always a zero-padded 5-character string. `"09001"`, never the integer `9001`.
- **Percentages:** store as a number (e.g. `12.4`), not as a string with `%`. Column name should make the unit clear (`poverty_rate`, `pcnt_insured`).
- **Per capita rates:** use `_per_100k` suffix for rates per 100,000 population.

---

## Known inconsistencies to resolve at merge time

These exist in already-committed files and will need to be harmonized before the final merge. Do not change these files now — just be aware when writing join logic.

| File | Column | Current value format | Target format |
|---|---|---|---|
| `acs_data.csv` | `county` | `"Albany County"` (includes suffix) | `"Albany"` |
| `stroke_mortality.csv` | `county` | `"Albany County"` (includes suffix) | `"Albany"` |
| `geographic_stroke_accessibility.csv` | `state` | `"New York"` (full name) | `"NY"` |
| `geographic_stroke_accessibility.csv` | `county` | `"Albany"` (no suffix) | `"Albany"` (already correct) |
| `acs_data.csv` | `pcnt_65_plus` | already renamed, no action needed | `pcnt_65_plus` |

**Bottom line:** always join on `fips`, never on `county` or `state` name strings. FIPS is consistent across all files.

---

## Current variables

### `data/acs_data.csv`
Source: U.S. Census Bureau ACS 5-year estimates, 2023. One row per county (91 total: 62 NY, 21 NJ, 8 CT).

| Column | Type | Description |
|---|---|---|
| `fips` | string | 5-digit county FIPS code, zero-padded |
| `county` | string | County name with "County" suffix (e.g. "Albany County") |
| `state` | string | Two-letter state abbreviation |
| `total_pop` | integer | Total county population |
| `pcnt_65_plus` | float | % of population aged 65 and over |
| `poverty_rate` | float | % of population below poverty line |
| `pcnt_insured` | float | % of population with health insurance coverage |
| `pcnt_bachelors` | float | % of adults with a bachelor's degree or higher |
| `pcnt_low_income` | float | % of households classified as low income (under ~$45k) |
| `pcnt_middle_class` | float | % of households classified as middle class (~$45k–$200k) |
| `pcnt_upper_class` | float | % of households classified as upper income (over ~$200k) |

Note: income is split into bins because median income cannot be mathematically aggregated across geographies.

---

### `data/stroke_mortality.csv`
Source: CDC WONDER Underlying Cause of Death, 2018–2024, Single Race. Pooled across years to reduce suppression in small counties. One row per county (91 total).

| Column | Type | Description |
|---|---|---|
| `fips` | string | 5-digit county FIPS code, zero-padded |
| `county` | string | County name with "County" suffix |
| `state` | string | Two-letter state abbreviation |
| `acute_stroke_mortality_per_100k` | float | Age-adjusted mortality rate per 100,000 for acute stroke (ICD-10 I60–I66) |
| `sequelae_stroke_mortality_per_100k` | float | Age-adjusted mortality rate per 100,000 for stroke sequelae (ICD-10 I69) |

---

### `data/geographic_accessibility_data/geographic_stroke_accessibility.csv`
Source: Computed from county population centers (Census 2020) and geocoded stroke center locations using geopy (distance) and OpenRouteService (drive time). One row per county (91 total).

| Column | Type | Description |
|---|---|---|
| `fips` | string | 5-digit county FIPS code, zero-padded |
| `county` | string | County name without "County" suffix (e.g. "Albany") |
| `state` | string | Full state name (e.g. "New York") — **inconsistent with other files, use fips to join** |
| `drive_time_min` | float | Estimated drive time in minutes to nearest basic stroke center (primary or acute). Essex NY and Hamilton NY are imputed at 45 mph. |
| `drive_time_advanced` | float | Estimated drive time in minutes to nearest advanced stroke center (comprehensive or thrombectomy-capable). Essex NY and Hamilton NY are imputed at 45 mph. |
| `nearest_stroke_distance` | float | Straight-line distance in miles to nearest basic stroke center |
| `nearest_stroke_distance_advanced` | float | Straight-line distance in miles to nearest advanced stroke center |

These 4 columns are the inputs to the Geographic Accessibility Index (GAI). The GAI is calculated via PCA across all 4 variables and normalized to 0-100. Higher = better access (closer). See the analysis notebooks in `notebooks/` for the index calculation.

---

### `data/cdcplaces_data.csv`
Source: CDC PLACES 2025 release, county level. One row per county (91 total: 62 NY, 21 NJ, 8 CT). These are the health risk-factor variables for the Stroke Risk Index (SRI).

| Column | Type | Description |
|---|---|---|
| `fips` | string | 5-digit county FIPS code, zero-padded |
| `county` | string | County name |
| `state` | string | Two-letter state abbreviation |
| `binge_drinking_prevalence` | float | % of adults who binge drink |
| `smoking_prevalence` | float | % of adults who currently smoke |
| `physical_inactivity` | float | % of adults with no leisure-time physical activity |
| `hypertension_prevalence` | float | % of adults with hypertension |
| `high_cholesterol_prevalence` | float | % of adults with high cholesterol |
| `diabetes_prevalence` | float | % of adults with diagnosed diabetes |
| `obesity_prevalence` | float | % of adults with obesity (BMI ≥ 30) |
| `stroke_prevalence` | float | % of adults ever told they had a stroke |

---

### `data/pop_density.csv`
Source: Census population + TIGER/Line land area. One row per county (91 total).

| Column | Type | Description |
|---|---|---|
| `fips` | string | 5-digit county FIPS code, zero-padded |
| `county` | string | County name |
| `state` | string | Two-letter state abbreviation |
| `pop_density` | float | Population per square mile |

---

### `data/scai_data/scai_data.csv`
Source: healthcare-access counts (hospitals, beds, providers, stroke centers) per county, per-capita against a vintage-matched ACS population denominator. See `data/scai_data/README.md` for the collection notebook and denominator rules. One row per county (91 total). These are the healthcare-access variables for the Stroke Care Access Index (SCAI).

| Column | Type | Description |
|---|---|---|
| `fips` | string | 5-digit county FIPS code, zero-padded |
| `hospitals_per_100k` | float | General hospitals per 100,000 population |
| `hospital_beds_per_100k` | float | Hospital beds per 100,000 population |
| `pcp_per_100k` | float | Primary care physicians per 100,000 population |
| `neurologists_per_100k` | float | Neurologists per 100,000 population |
| `stroke_centers_per_100k` | float | Stroke centers per 100,000 population |

Note: `pcnt_insured` (ACS, in `data/acs_data.csv`) joins these five variables at SCAI index-calculation time but is **not** a column of this file — it comes in via the master merge.
