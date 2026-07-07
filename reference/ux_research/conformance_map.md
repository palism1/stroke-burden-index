# UX research doc → implementation conformance map

Maps every recommendation in `ux_research_doc.pdf` (15 pp) to its
implementation status as of 2026-07-07. Update when the gaps close.

## Personas & success criteria (doc §2–4)

- **Marisol (county public-health director):** "which counties have the
  greatest burden / lack access / what initiatives make sense — and WHY."
  Success: leaves knowing *"County X should receive our next mobile stroke
  screening event."*
- **Eddie (general public, 65, New Haven):** "is my county high risk, how does
  it compare to neighbors, how far is care, what contributes, what prevention
  resources exist." Plain language required.

## Implemented ✓ (all in docs/dashboard/)

| Doc recommendation | Where |
|---|---|
| Search bar top of page, county-name search ("users know names, not locations") | search + typeahead |
| Map upper-left as primary focal point, details adjacent right (mockup p.9, F/Z scanning) | dashboard layout matches the mockup |
| Supporting viz (Risk vs. Access Matrix) secondary, below primary content | matrix section below map/details |
| Zooming feature (p.7: keep map clutter-free, add zoom) | wheel/drag/buttons + zoom-to-selection |
| Linked highlighting across views (change blindness, p.7) | map ↔ search ↔ matrix dot share one selection |
| Sequential single-hue **orange** palette ("urgency without emergency"), light→dark | choropleth palette |
| Pair color with labels/legends/symbols, never hue alone; contrast between levels; grayscale-distinguishable | labeled legend, county outlines, no-data grey + "Not available" text |
| Plain-language explanations for general users | details panel copy, index labels carry direction |
| Minimize clutter; group county info (burden, risk factors, distance, population) | details panel grouped sections (burden / access / community / index) |
| County details incl. population + distance to nearest emergency care | fields present in details panel |

## Gaps — the unimplemented delta

1. **Recommendations** (biggest gap — in BOTH user journeys and the sitemap:
   County Details → Recommendations). Nothing today tells Marisol *what
   initiative makes sense* or Eddie *what prevention resources exist*.
   V1 sketch: rule-generated plain-language bullets per county from data we
   already have — top risk drivers + access summary + quadrant-based
   suggestion (e.g. "risk here is driven mainly by smoking and diabetes
   prevalence; the nearest advanced stroke center is 45+ min — candidates:
   mobile screening events, telestroke partnerships"). Content rules need
   team/methodology sign-off before building.
2. **"WHY high priority" / factor contributions** (Marisol's journey). Details
   panel shows raw values but not what *drives* a county's SRI. V1: top-3
   contributing variables from loadings × county z-scores, stated in plain
   language; or percentile context per metric ("higher than 80% of counties").
3. **Neighbor comparison** (Eddie: "how does my county compare with
   neighboring counties?"). V1: state-median comparison in the details panel;
   V2: adjacent-county mini-comparison.

## Site-level implications (Jekyll theme work)

The doc is dashboard-scoped but its principles extend to the site: plain
language, F-pattern (important content early), grouping, WCAG contrast,
labels-not-color, minimal interface elements. That last principle argues for a
documentation-style theme (e.g. just-the-docs) over a portfolio theme with
heavy JS/transitions. The orange identity can carry into the site accent color.
