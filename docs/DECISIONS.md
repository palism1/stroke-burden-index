---
layout: default
title: Decisions log
---

# Decisions log

One entry per decision, newest first. This log distills team decisions (mostly
from Discord) into the repo so we stop re-litigating settled questions. For
how-to and mechanics see the [pipeline guide](./pipeline_guide.html).

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
- The SCAI index calculation includes it, with no flip needed (higher insured =
  better access).
- It stays physically in `data/acs_data.csv` and is pulled from the master table
  at calc time. It must NOT be added to `data/scai_data/scai_data.csv`: the
  schema contract pins that file to 6 columns, and a duplicate column would also
  break the SQLite master view.

## 2026-07-05 — GAI uses log1p transforms on all four drive-time/distance variables

Decided by: Jane Condon. Three of the four variables exceed the team skew rule
(`|skew| > 2`) and get reshaped per the rule, even though PC1 explained variance
drops slightly (0.82 raw → 0.77 log1p). Rule over metric: heavy tails should not
dominate PC1.

## Open — hospitals_per_100k and stroke_centers_per_100k in the SCAI index

Raised by: Jane Condon (Discord, updates channel, 2026-07-05). Both are
weakly/negatively correlated with the other SCAI variables (small-county
denominators inflate them; urban counties have fewer-but-bigger hospitals). PC1
explained variance is ~0.45 with them, ~0.72 without (before `pcnt_insured` was
added). Current proposal: keep both in the EDA, drop both from the index. NOT YET
DECIDED — needs team sign-off.

## Open — pcnt_insured treatment inside SCAI

Raised by: repo review 2026-07-06. `pcnt_insured` is nearly uncorrelated with the
five supply-side SCAI variables (max `|r| = 0.14`), its PC1 loading is ~0.10, and
adding it LOWERS SCAI explained variance (0.448 → 0.376 on the full set; 0.717 →
0.540 on the trimmed set). It is also heavily left-skewed (skew −2.84, flagged by
`result.high_skew`), so "no transformation needed" does not hold under the team's
own skew rule; a left-skewed variable would need e.g. `log1p(100 − pcnt_insured)`
then flip. Options: transform it, keep it untransformed and accept the noise, or
report insurance separately instead of inside either index. NOT YET DECIDED.
