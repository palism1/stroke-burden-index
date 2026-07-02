<!-- =========================================================================
FILE MAP
  path:  CLAUDE.md
  role:  MAP for agents and new sessions — repo purpose, pipeline stage
         order, pointers into docs/. NOT a manual: details live in docs/.
  tags:  TWEAK the stage list when a pipeline step is added or renamed.
         CHANGE ME if the doc pointers below move.
         DO NOT TOUCH the iron rules without a new docs/DECISIONS.md entry.
  keep:  under ~30 rendered lines.
========================================================================== -->

# Stroke Burden Index — map

County-level **Stroke Burden Priority Index (SBPI)** for the 91 NY/NJ/CT counties:
vulnerability (SVI) + care access (SCAI) + geographic access (GAI) → one combined
priority ranking. Data gathering is the active phase; index math is planned in
`docs/plan.md` but not yet coded.

## Pipeline stages, in order

1. **Collect** — notebooks in `data/*/` write tidy per-source CSVs to `data/` root.
2. **Geocode FIPS** — `src/add_fips_to_geocoded.py` adds county FIPS to stroke centers (CT re-queried at `vintage=419`).
3. **Gate** — `reference/ct_crosswalk/validate_ct_codes.py` blocks wrong-system CT codes before any FIPS join.
4. **Merge** — `src/merge.py` joins all sources on `fips` → `data/master.csv` (gitignored).
5. **Database** — `src/build_db.py` → `data/stroke_burden.db` with a `master` view (gitignored).
6. **Boundaries** — `src/build_county_boundaries.py` → `reference/county_boundaries/*.geojson`.

Tests: `python -m pytest tests/ -q` — CI runs them on every push.

## Where things are decided and documented

- `docs/DECISIONS.md` — past choices + why: crosswalk rules, FIPS edge cases, index weighting.
- `docs/DATA_NOTES.md` — data quirks: string FIPS, CT vintage trap, imputed values.
- `docs/plan.md` — methodology and open questions; `data/data_dictionary.md` — column naming rules.
- `reference/ct_crosswalk/README.md` — CT county↔planning-region no-nesting rules.

**Iron rules:** FIPS are zero-padded strings, never ints; join on `fips`, never `state`; CT uses the legacy 8 county codes (09001–09015).
