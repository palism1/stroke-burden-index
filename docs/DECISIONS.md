---
layout: page
title: Decisions log
nav_order: 5
---

# Decisions log

One entry per decision, newest first. This log distills team decisions (mostly
from Discord) into the repo so we stop re-litigating settled questions. For
how-to and mechanics see the [pipeline guide](./pipeline_guide.html).

## 2026-07-07 — the four open calls, decided in one Discord round

Decided by: Ngan Vu + Jane Condon (Discord, 2026-07-07, ~12:00-12:31); details
per item. All implemented in `src/compute_indices.py` the same day; EVR pins
updated (SRI 0.5224 unchanged, SCAI 0.539 → **0.549**, GAI 0.771 → **0.822**).

1. **neurologists_per_100k gets log1p** inside SCAI (rule consistency with the
   GAI precedent; both Janes voted yes).
2. **Hunterdon beds: real count pulled.** Better than expected — Hunterdon
   Medical Center (CCN 310005) was in the committed cost report all along; the
   notebook's join had missed it. 184 beds ÷ the same population denominator
   her pipeline used (130,313) → `hospital_beds_per_100k = 141.1985`, patched
   into `data/scai_data/scai_data.csv`. Note for the SCAI notebook: fix the
   join that dropped CCN 310005 before the next data refresh.
3. **GAI uses nearest-ANY-tier centers** (option b): the basic-tier slots are
   now `min(basic, advanced)` per county — derived in memory as
   `drive_time_any` / `nearest_stroke_distance_any`; source CSVs unchanged.
   The gai column is no longer provisional. EVR rose to 0.822 and Manhattan
   (comprehensive center ~2.5 min away) replaced Kings as the best-access
   county — both effects of the definition getting more physically real.
4. **SBPI exists: both methods, weights 50/30/20.**
   `sbpi = 0.5*SRI + 0.3*(100-SCAI) + 0.2*(100-GAI)` computed from the rounded
   published component scores (reproducible from indices.csv alone), plus
   `sbpi_class` 1-4 per plan.md's quadrant table with exact thresholds
   (75th pct SRI; 25th/50th pct SCAI; 25th pct GAI — rules in the script).
   Class counts: 55 low / 16 moderate / 10 high / 10 critical. Both columns in
   indices.csv + the db `indices` table; the sbpi score is on the dashboard,
   the class deliberately is not (the selector is built for continuous values).

## 2026-07-07 — per-county recommendations engine: direction approved

Decided by: Ngan Vu (spec) + Jane Condon (agree), Discord 2026-07-07 12:27.
V1 spec: classify each county into a quadrant from its SRI/SCAI/GAI scores,
pull its top-3 percentile risk drivers, and auto-generate a tailored action
plan. Implementation pending (dashboard details panel); wording rules open —
whoever wants to own the copy, speak up.

## 2026-07-07 — index scores are persisted: data/indices.csv is canonical

Decided by: jane + Ngan Vu (Discord, issues channel, 2026-07-06: save the
values to a csv / also add the indices to the database). Implemented 2026-07-07:

- `src/compute_indices.py` is the **canonical producer** of the committed
  scores. Its CONFIG block mirrors this decisions log entry-by-entry; it writes
  `data/indices.csv` (fips, sri, scai, gai; 0–100, 4 decimals). CI recomputes
  the file on every push and fails if the committed copy is stale — the scores
  can never silently drift from the data.
- The database gets an `indices` table (not folded into the master view: the
  scores derive *from* master, so the DAG stays acyclic — join on fips).
- The dashboard serves all three scores and the Risk-vs-Access matrix is live
  (X = SRI, Y = SCAI, quadrant lines at the 75th/25th percentiles).
- `notebooks/Calculating Indices.ipynb` remains the exploratory home; the
  script reproduces its committed outputs exactly (an EVR regression test pins
  them). When a decision here changes: edit the script's CONFIG, rerun, commit
  the regenerated CSV + counties.json in the same PR.
- Codified from the notebook while porting: SRI applies **log1p to
  pop_density** (right-skewed, per the team skew rule). It was in the notebook
  but not previously written down here.

## 2026-07-06 — hospitals_per_100k and stroke_centers_per_100k dropped from the SCAI index

Decided by: team vote (Mikko, Jane Condon, Ngan Vu, Cathleen — Discord, updates
channel, 2026-07-06). Both stay in the EDA and in `data/scai_data/scai_data.csv`
(the file contract is unchanged), but neither enters the SCAI index calculation.
Rationale: small-county denominators inflate them, `hospitals_per_100k` loaded
*negative* (−0.18) in the index, and PC1 explained variance rises from ~0.45 to
~0.72 without them (supply vars only). Implemented in
`notebooks/Calculating Indices.ipynb`.

## 2026-07-06 — pcnt_insured stays in SCAI, recast as the uninsured rate with log1p + flip

Decided by: Ngan Vu, seconded by Cathleen and Mikko (Discord, updates channel,
2026-07-06). `pcnt_insured` is left-skewed (−2.84), so the log transform is
applied to its invert, the uninsured rate: `pcnt_uninsured = 100 − pcnt_insured`,
then `log1p`, then `flip` (higher uninsured = worse access; post-transform skew
−1.31, under the team rule). Implemented in `notebooks/Calculating Indices.ipynb`.

Outcome after implementing (with hospitals/stroke_centers also dropped, per the
decision above): SCAI PC1 explained variance is **0.539** (was 0.376). Note the
transform did not rescue the variable's relevance — its PC1 loading is 0.076,
still near zero, and EVR is essentially identical to keeping it untransformed on
the trimmed set (0.540). It remains statistically noise inside SCAI; revisit
option (c) (report insurance as a standalone context variable) if that bothers
anyone downstream.

## 2026-07-05 — SVI renamed to SRI (Stroke Risk Index)

Decided by: Ngan Vu (Discord, updates channel). The vulnerability index is now
the Stroke Risk Index (SRI); this resolves the long-standing naming collision
with the CDC/ATSDR Social Vulnerability Index. Implemented in the notebooks
(`SRI EDA.ipynb`, `Calculating Indices.ipynb`); the docs/site/code-comment sweep
was done 2026-07-06 on this branch.

## 2026-07-05 — pcnt_insured belongs to SCAI, not SRI

Decided by: Jane Condon + Ngan Vu (Discord, issues channel, 2026-07-06). The
docs/site had listed it under SCAI while the plan/pipeline docs said SRI — the
SCAI placement won. Consequences:

- SRI EDA and SRI calculation exclude `pcnt_insured`.
- The SCAI index calculation includes it. ("No flip needed" was part of the
  original decision but is superseded by the 2026-07-06 recast-as-uninsured
  decision above: the recast variable IS flipped.)
- It stays physically in `data/acs_data.csv` and is pulled from the master table
  at calc time. It must NOT be added to `data/scai_data/scai_data.csv`: the
  schema contract pins that file to 6 columns, and a duplicate column would also
  break the SQLite master view.

## 2026-07-05 — GAI uses log1p transforms on all four drive-time/distance variables

Decided by: Jane Condon. Three of the four variables exceed the team skew rule
(`|skew| > 2`) and get reshaped per the rule, even though PC1 explained variance
drops slightly (0.82 raw → 0.77 log1p). Rule over metric: heavy tails should not
dominate PC1.
