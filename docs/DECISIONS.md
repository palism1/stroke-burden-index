---
layout: default
title: Decisions log
---

# Decisions log

One entry per decision, newest first. This log distills team decisions (mostly
from Discord) into the repo so we stop re-litigating settled questions. For
how-to and mechanics see the [pipeline guide](./pipeline_guide.html).

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
