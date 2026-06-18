# CT county <-> planning-region crosswalk

Read this before joining any Connecticut data into the pipeline.

## What this is

In 2022 the Census Bureau replaced Connecticut's **8 counties** with **9 planning
regions** as the official county-equivalent geography. The two systems use
different FIPS codes, and **most health data sources still ship CT in the old
county codes** (CDC mortality, PLACES, County Health Rankings, HIFLD, RUCC).
If our master table is in one system and an incoming source is in the other,
every CT row silently drops out of the join.

This folder is the translator between the two systems, plus a gate that stops
that silent drop from happening.

## The no-nesting gotcha (important)

The 8 old counties and the 9 planning regions **do not nest**. A single planning
region pulls towns from more than one old county, and vice versa. So you
**cannot** map county -> region (or region -> county) directly. The only common
denominator is the **town** (Connecticut has 169). All conversion goes through
towns: aggregate town-level data up to whichever system you need.

## FIPS Structure
| Geo level               | Number of digits | Structure                                                  |
|-------------------------|------------------|------------------------------------------------------------|
| State                   | 2 digits         | 09 for CT, 36 for NY, 34 for NJ                            |
| County/Planning Regions | 5 digits         | XX (State) + YYY (County/Planning Region)                  |
| Town                    | 10 digits        | XX (State) + YYY (County/Planning Region) + ZZZZZ (Town)   |
| Census Tract            | 11 digits        | XX (State) + YYY (County/Planning Region) + ZZZZZZ (Tract) |

### FIPS are strings, always

Every FIPS in here is a zero-padded string. The raw source had the leading zero
stripped off CT's `09` codes (they looked like 9-digit numbers); the build step
restores it. Never read or store a FIPS as an int anywhere downstream.

## Files

| File                                 | What it is                                                                                                                                                        |
|--------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `ct_town_crosswalk.csv`              | **The artifact. Join against this.** 169 towns, each with its old county (code + name) and its planning region (code + name). Every FIPS is a zero-padded string. |
| `ct-town-to-planning-region.raw.csv` | The untouched source pull, kept for provenance only.                                                                                                              |
| `2022tractcrosswalk.csv`             | The crosswalk file for mapping census tracts with counties                                                                                                         |                                                                                                       |
| `build_ct_crosswalk.py`              | Regenerates the clean CSV from the raw pull. Provenance, not runtime. Prints `169 towns, 8 counties, 9 regions`.                                                  |
| `validate_ct_codes.py`               | The runtime gate. See below.                                                                                                                                      |

### `ct_town_crosswalk.csv` columns

`town_name, town_fips_2020, county_fips, county_name, town_fips_2022, region_fips, region_name`

- `town_fips_2020` / `town_fips_2022` — 10-char town GEOIDs in the old / new systems.
- `county_fips` (5 char, e.g. `09013`) + `county_name` — the 8 legacy counties.
- `region_fips` (5 char, e.g. `09110`) + `region_name` — the 9 planning regions.

## The gate

```python
from validate_ct_codes import validate_ct_codes, CTCodeError

# Call at the TOP of a merge step, before the first CT-involving join.
validate_ct_codes(df, fips_col="fips")   # system defaults to "county_2020"
```

It checks every CT code (those starting with `09`) against the valid set for the
chosen `system` and raises `CTCodeError` listing any that don't fit — so a
mismatched code system makes the pipeline **stop loudly** instead of dropping CT.

`system` is one of `"county_2020"` (8 counties) or `"region_2022"` (9 regions).
The default is `"county_2020"`. **Which system is canonical is still on hold
pending Ngan**, so leave the default alone for now.

## Source

CT-Data-Collaborative town-to-planning-region crosswalk (MIT licensed), built
from Census TIGER county-subdivision and county-equivalent files:
<https://github.com/CT-Data-Collaborative/ct-town-to-planning-region>
