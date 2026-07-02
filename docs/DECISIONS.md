<!-- =========================================================================
FILE MAP
  path:  docs/DECISIONS.md
  role:  Decision log — what was chosen, why, and when. Seeded 2026-07-02
         from git history and code comments; append new entries at the
         bottom as decisions are made.
  tags:  CHANGE ME — append-only; add an entry per decision, a few lines
         each, never transcripts.
         DO NOT TOUCH existing entries except to mark them superseded.
  note:  docs/ is a live GitHub Pages site, so this file is published.
========================================================================== -->

# Decision log

One entry per decision: **what** was decided, **why**, and **when**. Entries are
chronological. If a decision is reversed, add a new entry and mark the old one
superseded — don't rewrite history.

---

**2026-06-17 — Connecticut keyed on the legacy 8 counties, not the 2022 planning regions.**
A commit switched the FIPS spine to planning-region codes (09110–09190) and was
reverted the same day. Most health sources (CDC WONDER, PLACES, HIFLD, RUCC)
still ship CT in the old county codes (09001–09015), so the old system drops
fewer rows. The *canonical* system is formally on hold pending Ngan — the gate's
`DEFAULT_SYSTEM = "county_2020"` stands in for the decision until then.

**2026-06-18 — All CT county↔region conversion goes through towns.**
The 8 old counties and 9 planning regions do not nest, so no direct
county↔region mapping exists. The vendored CT-Data-Collaborative crosswalk
(`reference/ct_crosswalk/ct_town_crosswalk.csv`, 169 towns) is the only sanctioned
conversion path: aggregate town-level data up to whichever system is needed.

**2026-06-18 — Runtime validation gate instead of trusting joins.**
`validate_ct_codes()` is called before any FIPS join and raises `CTCodeError` on
CT codes in the wrong system, because a mismatched system makes CT rows drop
*silently* in a left join. Fail loudly beats fail quietly.

**2026-06-18 — FIPS are zero-padded strings, everywhere, always.**
An int FIPS has already lost its leading zero (CT's "09" codes are the casualty).
The raw crosswalk pull shipped with zeros stripped and had to be repaired; the
gate rejects any non-string FIPS. Reaffirmed 2026-06-25 when the accessibility
CSV lost its leading zeros and had to be fixed again (commit 5d08c24).

**2026-06-18 — SBPI weighting recorded but NOT reconciled.**
The plan's formula is `0.5·SVI + 0.3·(access deficit) + 0.2·(distance deficit)`,
but the prose target was 50/25/25. Only agreed constraint: vulnerability always
carries the most weight. Open question in `docs/plan.md`; resolve before write-up.

**by 2026-06-21 — CDC WONDER mortality pooled over 2018–2024.**
Single-year county stroke mortality is suppressed for many smaller counties, so
rates are pooled across years for stability. The collected files use 2018–2024
(acute and sequelae, age-adjusted).

**2026-06-25 — Essex and Hamilton NY drive times imputed at 45 mph.**
OpenRouteService could not route to these remote Adirondack counties.
`drive_time_min` was imputed as straight-line distance / 45 mph; missing
`drive_time_advanced` imputes the same way. The no-missing-values test was
relaxed to match.

**2026-06-25 — Merge-time cleaning, not source-file edits.**
Known inconsistencies (county names with " County" suffix, full state names)
are harmonized inside `src/merge.py` / `src/build_db.py` at load time; committed
source CSVs are left as collected. Join on `fips`, never on `county` or `state`.

**2026-06-29 — Census Geocoder CT points re-queried at vintage=419.**
The API's default vintage returns planning-region codes for CT coordinates. Any
point resolving to state "09" is re-queried with `vintage=419` to get legacy
county codes, then the output is run through the validation gate before writing.

**2026-06-30 — County boundaries from TIGER 2019, simplified with QA flags.**
2019 is the last vintage before CT's county→region switch, so one consistent
download sidesteps the vintage trap for all three states. Geometry is simplified
for web maps; counties whose area shifts >2% or whose adjacency breaks are
flagged to an HTML QA map rather than silently accepted.
