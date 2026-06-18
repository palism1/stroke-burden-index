---
layout: default
title: Stroke Burden Index
---

# Stroke Burden Index

**Where do stroke risk and poor access to care overlap?**

This project identifies high-priority stroke intervention areas in the US by combining county-level indices into a single **Stroke Burden Priority Index (SBPI)**:

- **Stroke Vulnerability Index (SVI)** — likelihood a community experiences stroke-related health problems (demographics, socioeconomic, health risk factors).
- **Stroke Care Access Index (SCAI)** — availability of treatment resources (hospitals / stroke centers per capita, PCP per capita, insurance).
- **Geographic Access Score** — travel distance to the nearest stroke center.
- **Stroke Burden Priority Index (SBPI)** — combines the above to rank counties by overall burden; counties high in vulnerability *and* low in access are the **critical intervention zones** (the "stroke care deserts").

Each index is built the same way: **raw → align direction → standardize → PCA → normalize (0–100)**. A geospatial layer maps stroke centers, distance-to-care, and burden hotspots across the NY-NJ-CT region.

## Read

- [Full project plan](./plan.html)

## Status

Data gathering. The analytical methodology (indices, geospatial analysis, models) is drafted and agreed; it runs once the county-level data is audited.

First concrete deliverable: a verified table of US stroke centers with coordinates (HIFLD + state designation lists, joined; only unmatched centers get geocoded). A Connecticut county ↔ planning-region crosswalk and validation gate are already in the repo to keep CT from dropping out of joins.

EDA, indices, maps, and any dashboard come next.
