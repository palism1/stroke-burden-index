---
layout: post
title: "Project Outcome Summary"
date: 2026-07-07 12:00:00 -0400
image: outcome.svg
description: "12 stroke care deserts, all rural upstate NY — what the indices found, in plain language."
---

Combining stroke risk with access to care across 91 counties surfaces a clear
pattern: **12 counties are stroke care deserts** — high risk *and* poor access —
and every one of them is rural upstate New York, led by Hamilton County
(risk 91/100, access 0.04/100). Under the combined Stroke Burden Priority
Index, the highest-burden counties are Hamilton, Delaware, and Chenango.

The [interactive dashboard]({{ site.baseurl }}/dashboard/) shows the full
picture — including the Risk vs. Access matrix where these counties cluster in
the critical-intervention quadrant.

*Draft skeleton — this section will grow into the full analysis summary with
figures and plots (Discord 7/7). Drop finished .md content and images
(`docs/images/`) here.*

# Project Outcomes

## Overview

Briefly summarize what the project produced and how the indices can be used.

---

## County-Level Stroke Burden Database (Optional Section ?)

Describe the final integrated database.

Include:

- 91 counties
- NY, NJ, CT
- One record per county
- Variables from all data sources
- Master database used throughout the project


---

## Stroke Risk Index (SRI)

Describe:

- What it measures
- Key findings
- Counties with highest/lowest scores
- Distribution of scores

- Top 10 counties

---

## Stroke Care Access Index (SCAI)

Describe:

- What it measures
- General patterns
- Counties with highest/lowest access
- Interpretation

- Top 10 counties

---

## Geographic Accessibility Index (GAI)

Describe:

- What it measures
- Geographic patterns
- Urban vs rural differences
- Interpretation

Figures: 

<h2>Accessibility to Basic Stroke Centers</h2>

<p align="center">
  <img src="../images/basic_accessibility.png"
    style="width:50%; height:auto;">
</p>

<p align="center">
<i>Figure 1. County-level drive time to the nearest certified Basic Stroke Center. Counties are categorized into four travel-time intervals, illustrating regional differences in access to basic stroke care.</i>
</p>

Basic stroke centers are distributed throughout the region, resulting in relatively short travel times for most counties. The highest accessibility is concentrated around major metropolitan areas, while some rural counties in northern New York remain more than 60 minutes from the nearest facility. Overall, the map suggests that access to basic stroke care is relatively widespread, though notable geographic disparities remain in rural regions.

<h2>Accessibility to Advanced Stroke Centers</h2>

<p align="center">
  <img src="../images/advanced_accessibility.png" 
    style="width:50%; height:auto;">
</p>

<p align="center">
<i>Figure 2. County-level drive time to the nearest certified Advanced Stroke Center. Advanced stroke centers are concentrated in metropolitan regions, resulting in substantially longer travel times for many rural counties.</i>
</p>

Compared to basic stroke centers, advanced centers are substantially less common and are concentrated in densely populated metropolitan regions, particularly around New York City and portions of Connecticut. Large portions of northern and western New York fall into the 60+ minute travel category, indicating limited access to specialized stroke care. These differences highlight the importance of distinguishing between basic and advanced stroke services when evaluating geographic accessibility.

<h2>Stroke Center Distribution</h2>

<p align="center">
  <img src="../images/stroke_centers_map_full.png"  
    style="width:50%; height:auto;">
</p>

<p align="center">
<i>Figure 3. Locations of certified Basic Stroke Centers (circles) and Advanced Stroke Centers (triangles) overlaid on county accessibility categories.</i>
</p>

This map overlays both Basic Stroke Centers (circles) and Advanced Stroke Centers (triangles) on county accessibility categories. The figure demonstrates the geographic concentration of advanced stroke care around major urban centers while illustrating the broader distribution of basic stroke centers. Together, these patterns reveal substantial spatial disparities in access to specialized stroke treatment, particularly in rural counties.

---

## Stroke Burden Priority Index (SBPI)

Describe:

- Combination of SRI, SCAI, and GAI
- Final county rankings
- Priority counties
- Public health interpretation

Possible figures:

- Final SBPI map
- Top 10 priority counties
- Ranking table

### Top 20 Highest Priority Counties

<h2>Highest Priority Counties</h2>

<p align="center">
  <img src="../images/sbpi_priority_counties.png"
    style="width:50%; height:auto;">
</p>

<p align="center">
<i>Figure 10. Twenty counties with the highest Stroke Burden Priority Index (SBPI), representing locations where elevated stroke risk coincides with reduced healthcare accessibility.</i>
</p>

The lollipop chart above ranks the twenty counties with the highest Stroke Burden Priority Index scores. Nearly all of the highest-priority counties are located in rural upstate New York, where elevated stroke risk coincides with reduced healthcare resources and longer travel times to stroke centers. Counties such as Hamilton, Delaware, Chenango, and Essex consistently emerge as the highest-priority locations for potential intervention. This ranking provides a practical framework for identifying counties where investments in stroke prevention, healthcare resources, or geographic accessibility may have the greatest impact.

---

## Complete Index Analysis

Include all major data visualizations from index analysis here.


## Key Findings

Summarize the major conclusions.

---

## Applications

Describe how the indices can be used.

Examples:

- Public health planning
- Resource allocation
- Hospital planning
- Policy evaluation
- Future research

---

## Future Work

Potential extensions (explaining what we would do if we were to expand on this).

Ideas:

- Expand nationally
- Incorporate EMS response times
- Add temporal trends
- Include social vulnerability measures
- Update annually

