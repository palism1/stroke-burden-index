---
layout: default
title: Decisions log
---

# Decisions log

One entry per decision, newest first. This log distills team decisions (mostly
from Discord) into the repo so we stop re-litigating settled questions. For
how-to and mechanics see the [pipeline guide](./pipeline_guide.html).

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

## Open — neurologists_per_100k exceeds the skew rule inside SCAI

Raised by: repo review 2026-07-06, surfaced by the notebook's new
`scai_result.high_skew` check after the SCAI variable set was trimmed.
`neurologists_per_100k` has skew **3.21** (> 2.0) and no transform, so it sits
in the same position `pcnt_insured` did under the team's PCA rule. Applying
`log1p` to it barely moves the metric (EVR 0.539 → 0.541, loadings stable), so
this is a rule-consistency call, not a numbers call — the GAI precedent
("rule over metric") says transform it. NOT YET DECIDED — needs team sign-off.
When decided: one-line change in `src/compute_indices.py` CONFIG + regenerate.

## Open — Hunterdon NJ hospital_beds_per_100k = 0 is a data gap, not a value

Raised by: PR #22/#24 review, 2026-07-05. Hunterdon has a hospital, but its
CMS cost report was missing and the NA was zero-filled — and
`hospital_beds_per_100k` survived the SCAI trim, so the fake 0 is inside the
live index: Hunterdon currently reads as the worst bed access in the tristate.
Options: (a) pull the real bed count from the cost report, (b) impute (e.g.
state median) and document, (c) keep 0 deliberately. Owner: Jane Condon
(`scai_data.csv` is contract-pinned; the fix edits that file, CI handles the
rest). NOT YET DECIDED.

## Open — GAI's "nearest basic center" definition (persisted as provisional)

Raised by: geographic data lineage review (F2), 2026-07-02. The basic-tier
columns count primary/acute-designated centers only; an advanced center (which
also treats stroke) is closer in 19 of 91 counties, so basic drive time is
overstated there. GAI was computed and persisted with the current
designation-specific definition — treat the committed `gai` column as
**provisional** until the team either (a) blesses designation-specific
explicitly, or (b) switches to nearest-any-tier (columnwise min of the two
tiers; no re-querying, minutes to recompute). The matrix does not use GAI, so
this doesn't affect the dashboard's quadrants. NOT YET DECIDED.

## Open — SBPI method and weights (blocks the headline index)

From docs/plan.md, migrated here 2026-07-07 so this log is the single list of
open questions. Two calls, both needed before SBPI can exist:

- **Method:** continuous weighted score (Option 1), quadrant classification
  (Option 2), or both (dashboard can show both; extra cost is small).
- **Weights (Option 1):** the plan says 50/25/25 in one place and 50/30/20 in
  another — which is canonical? (Weights can also be a config with a published
  sensitivity check.)

When decided: SBPI lands in `src/compute_indices.py` + `data/indices.csv`
(schema grows an `sbpi` column — the dashboard field registry already has its
label waiting). NOT YET DECIDED.
