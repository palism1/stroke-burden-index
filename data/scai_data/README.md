# SCAI Data (Stroke Care Access Index)

This folder is the home for all SCAI data collection. SCAI captures **healthcare
access** variables: the availability of stroke-relevant treatment resources per
capita in each county (hospitals, hospital beds, primary care physicians,
neurologists, and stroke centers).

**Put every SCAI file in this folder, not the repo root.** Earlier drafts landed
at the repo root by accident. The collection notebook, intermediate downloads,
and the final CSV all belong here.

### Root cleanup (2026-07-02) — where files went

The root-level working copies were removed or moved. If a notebook read them by
bare filename, update its paths per this mapping (exact duplicates were deleted;
the canonical copy is listed):

| Was at repo root | Now |
|---|---|
| `SCAI_Data_Gathering.ipynb`, `healthPerCapita.py`, `hospitals_per_100k_nj_ny.csv` | `data/scai_data/` (moved) |
| `hospitals_per_100k_all.csv`, `pcp_per_100k_all.csv` | `data/scai_data/` (root duplicate deleted) |
| `County_Health_Rankings_{CT,NJ,NY}.xlsx` | `data/raw/county_health_rankings/` (moved) |
| `Hospital_General_Information.csv`, `co-est2025-alldata.csv`, `ct_towns_pop2023.csv`, `ny_nj_ct_fips.csv` | `data/` (root duplicate deleted) |
| `ct_basic_geocoded.csv`, `ct_advanced_geocoded.csv` | `data/geographic_accessibility_data/` (root duplicate deleted) |
| `ct_stroke_centers_geocoded.csv` | `data/geographic_accessibility_data/` (moved) |
| `ct_town_crosswalk.csv` | `reference/ct_crosswalk/` (root duplicate deleted) |

## Expected files

| File | Description |
|---|---|
| `scai_data.csv` | Final output, one row per county (91 total: 62 NY, 21 NJ, 8 CT). |
| `SCAI_Data_Gathering` notebook | The notebook that collects, cleans, and produces `scai_data.csv`. |

## Expected columns in `scai_data.csv`

From the project data dictionary:

| Column | Type | Description |
|---|---|---|
| `fips` | string | 5-digit county FIPS code, zero-padded (e.g. `"09001"`, never the integer `9001`). |
| `hospitals_per_100k` | float | General hospitals per 100,000 population. |
| `hospital_beds_per_100k` | float | Hospital beds per 100,000 population. |
| `pcp_per_100k` | float | Primary care physicians per 100,000 population. |
| `neurologists_per_100k` | float | Neurologists per 100,000 population. |
| `stroke_centers_per_100k` | float | Stroke centers per 100,000 population. |

Follow the project naming conventions (see `data/data_dictionary.md`): lowercase
snake_case columns, FIPS as a zero-padded 5-character string, and the
`_per_100k` suffix for per-100,000 rates.

## Population denominators

If the hospital or provider counts come from **2023**, use the **2023 ACS 1-year
estimate** for the population denominator (not the 5-year estimate). The 5-year
estimate is a rolling average across 2019-2023 and does not line up with a
single-year 2023 numerator. Match the vintage of the denominator to the vintage
of the numerator.
