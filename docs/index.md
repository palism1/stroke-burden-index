---
layout: default
title: Home
nav_order: 1
---

# Stroke Burden Index

**Where do stroke risk and poor access to care overlap? Identifying
high-priority stroke intervention areas across New York, New Jersey, and
Connecticut.**

[Open the interactive dashboard](./dashboard/){: .btn .btn-primary }
[Read the methodology](./plan.html){: .btn }

---

## Explore the project

| Section | What's there |
|---|---|
| **[Dashboard](./dashboard/)** | Interactive county map, plain-language county details, and the Risk vs. Access matrix — find your county or the region's highest-priority ones |
| **[Methodology & plan](./plan.html)** | How the indices are designed, the full analytical plan, and open questions |
| **[Pipeline guide](./pipeline_guide.html)** | How the data pipeline works and how to reproduce every number |
| **[Decisions log](./DECISIONS.html)** | Every settled methodology decision, dated — and the ones still open |
| **[Data lineage review](./geo_lineage_review.html)** | Where the geographic accessibility data comes from and how it was verified |
| **[Data & sources](./data_sources.html)** | Every dataset we use and where it comes from |

---

## Questions we're answering

- Which counties exhibit the highest stroke vulnerability, and why?
- Which counties have the poorest access to stroke care?
- Which factors (socioeconomic, health, geographic) most strongly predict stroke mortality?
- How can resources be prioritized to reduce stroke burden?

**Combined:** Which counties face the greatest stroke burden due to a
combination of stroke risk factors and limited access to stroke care?

---

## Main idea

We build three component indices and combine them into a single headline index.

| Index | What it measures |
|---|---|
| **Stroke Risk Index (SRI)** | Likelihood a community will experience stroke-related health problems |
| **Stroke Care Access Index (SCAI)** | Availability of treatment resources |
| **Geographic Accessibility Index (GAI)** | Drive time and distance to the nearest stroke center |
| **Stroke Burden Priority Index (SBPI)** | Combined ranking of overall stroke burden *(in design — see the [decisions log](./DECISIONS.html))* |

Every index follows the same pipeline: **raw → transform (fix skew) → align
direction → standardize → PCA → normalize (0–100)**. Details and per-index
variable lists are in the [methodology](./plan.html); the exact settled
configuration is in the [decisions log](./DECISIONS.html).

Counties that combine high vulnerability with poor access are the **stroke
care deserts** — the core target of this project. The dashboard's
[Risk vs. Access matrix](./dashboard/) shows them live.

---

## Status

**The indices are computed and live.** All county data for the 91 NY/NJ/CT
counties is collected and CI-verified; SRI, SCAI, and GAI are calculated by a
reproducible pipeline (`src/compute_indices.py`) and served on the
[dashboard](./dashboard/), including the Risk vs. Access matrix. Remaining
work: the combined SBPI (method and weights under discussion), per-county
recommendations, and continued refinement — see the
[decisions log](./DECISIONS.html) for exactly what's open.
