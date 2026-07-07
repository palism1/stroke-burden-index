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
