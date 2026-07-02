<!-- =========================================================================
FILE MAP
  path:  docs/DATA_NOTES.md
  role:  Data quirks and traps — things that will silently corrupt a join
         or a count if you don't know them. Read before touching any CSV.
  tags:  CHANGE ME — add a note whenever a new quirk is discovered.
         DO NOT TOUCH the FIPS/string rule or the CT vintage warning;
         they encode fixes for bugs that actually happened.
  note:  docs/ is a live GitHub Pages site, so this file is published.
========================================================================== -->

# Data notes

Quirks that will silently break joins, counts, or maps. The "why" behind each
lives in `docs/DECISIONS.md`.

## FIPS handling (DO NOT TOUCH)

- Every FIPS is a **zero-padded 5-char string** (`"09001"`, never `9001`). Always
  read with `dtype={"fips": str}`. An int FIPS has already lost its leading zero —
  this bug shipped twice (raw crosswalk pull; accessibility CSV, fixed 2026-06-25).
- **Join on `fips`, never on `county` or `state`** — those columns are inconsistent
  across files (see below).
- CT uses the **legacy 8 county codes** (09001–09015), not the 2022 planning
  regions (09110–09190). Run `validate_ct_codes()` before any CT-involving join.
- The 8 counties and 9 regions **do not nest**; convert only via the 169-town
  crosswalk in `reference/ct_crosswalk/`.

## CT reverse-geocoding trap

The Census Geocoder's default vintage returns **planning-region** codes for CT
coordinates. Always pass `vintage=419` for CT points (state FIPS "09"), or the
resulting rows will not join to anything. `src/add_fips_to_geocoded.py` does
this automatically.

## Known inconsistencies in committed files (cleaned at merge time)

- `acs_data.csv`, `stroke_mortality.csv`: `county` carries a " County" suffix.
- `geographic_stroke_accessibility.csv`: `state` uses full names ("New York").
- `acs_data.csv`: column `pcnt_65+` is renamed to `pcnt_65_plus` in the DB build.
- Full table: `data/data_dictionary.md`. Do not "fix" the source files — the
  shared loaders in `src/loaders.py` handle it.

## Imputed and missing values

- **Essex NY and Hamilton NY**: `drive_time_min` is imputed (straight-line
  distance at 45 mph — OpenRouteService could not route). `drive_time_advanced`
  is missing for both; impute with `nearest_stroke_distance_advanced / 45 * 60`.
- `ny_all_stroke_centers_geocoded.csv`: 5 rows without coordinates.
- `nj_all_stroke_centers_geocoded.csv`: 11 rows without coordinates (3
  Comprehensive centers were manually patched inside the notebook).

## Double-count warning (TWEAK if the file layout changes)

Do **not** stack `nj_primary_stroke_centers_geocoded.csv` with
`nj_all_stroke_centers_geocoded.csv` to count centers — primary centers appear
in both. The notebook uses `nj_primary` for basic centers and filters `nj_all`
to comprehensive-only for advanced centers.

## Gitignored artifacts

`data/master.csv`, `data/stroke_burden.db`, and `data/raw/`, `data/interim/`
are generated locally (`python src/merge.py`, `python src/build_db.py`) and
never committed.
