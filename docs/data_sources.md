---
layout: page
title: Data & sources
nav_order: 7
status: living
last_updated: 2026-07-07
---

# Data & sources

Every dataset in the project, where it comes from, and where the authoritative
column-level documentation lives.

## Sources

- [CDC WONDER](https://wonder.cdc.gov/) — stroke mortality by county
  (acute + sequelae, age-adjusted, 2018–2024 pooled)
- [US Census ACS](https://www.census.gov/programs-surveys/acs) — demographics
  and socioeconomics (age 65+, poverty, income bins, education, insurance)
- [CDC PLACES](https://www.cdc.gov/places/) — health prevalence variables
  (smoking, obesity, diabetes, physical inactivity, hypertension, high
  cholesterol, binge drinking, stroke prevalence)
- [County Health Rankings](https://www.countyhealthrankings.org/health-data) —
  socioeconomic and health variables (SCAI inputs)
- [CMS Hospital Provider Cost Reports](https://www.cms.gov/data-research/statistics-trends-reports/cost-reports) —
  hospital beds
- [HRSA Area Health Resources Files](https://data.hrsa.gov/topics/health-workforce/nchwa/ahrf) —
  physician and neurologist workforce by county
- [NYSDOH Stroke Centers](https://profiles.health.ny.gov) — NY designated
  stroke centers
- [CT DPH Stroke Centers](https://portal.ct.gov/dph/emergency-medical-services/ems/certified-stroke-centers) —
  CT certified stroke centers
- [NJ Stroke Centers](https://nj.gov/health) — NJ state-designated stroke
  centers
- [US Census CenPop 2020](https://www.census.gov/geographies/reference-files/time-series/geo/centers-population.html) —
  county population centroids (drive-time origins)
- [OpenRouteService](https://openrouteservice.org/) — drive times from each
  county's population center to the nearest basic and advanced stroke center

## Column-level documentation

The authoritative data dictionary — every column in every committed CSV, with
types, units, and caveats — is maintained next to the data itself:
[`data/data_dictionary.md` on GitHub](https://github.com/palism1/stroke-burden-index/blob/main/data/data_dictionary.md).
(A rendered copy on this site is planned; linking rather than copying keeps a
single source of truth.)

How the files flow — raw sources → merge → master table → indices → this
site — is documented in the [pipeline guide](./pipeline_guide.html). The
provenance review of the geographic data specifically is in the
[data lineage review](./geo_lineage_review.html).
