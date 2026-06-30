"""Add county FIPS codes to a geocoded stroke center CSV.

The geocoded stroke center files (e.g. ny_all_stroke_centers_geocoded.csv) carry
a latitude/longitude for each center but no county FIPS. This script looks up the
county each point falls in using the free U.S. Census Geocoder API and writes a
new file with a `fips` column added. The original file is never modified.

USAGE
-----
    python src/add_fips_to_geocoded.py <input_csv> [output_csv]

    # output defaults to "<input>_with_fips.csv"
    python src/add_fips_to_geocoded.py data/geographic_accessibility_data/ny_all_stroke_centers_geocoded.csv

    # or name the output explicitly
    python src/add_fips_to_geocoded.py ny_centers.csv ny_centers_fips.csv

The input CSV must have `latitude` and `longitude` columns. Any other columns
(name, group/designation, address, ...) are passed through untouched.

WHAT IT ADDS
------------
A `fips` column: the 5-character, zero-padded county FIPS (2-char state +
3-char county), as a string. Rows whose lookup fails get an empty fips and a
printed warning; they are not dropped.

CONNECTICUT VINTAGE NOTE
------------------------
For CT coordinates the Census API's default vintage returns the new 2022
*planning region* codes (09110-09190). The rest of this project keys CT on the
old 8-county codes (09001-09015). So whenever a point resolves to state FIPS
"09", we re-query with vintage=419, which returns the old county codes. The
output is then run through reference/ct_crosswalk/validate_ct_codes.py, which
raises if any CT code is still in the wrong system. If validation fails, nothing
is written.

Requires: pandas, requests (already in requirements.txt).
"""

import sys
import time
from pathlib import Path

import pandas as pd
import requests

# Make the CT validation gate importable no matter the caller's cwd.
_REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_REPO_ROOT / "reference" / "ct_crosswalk"))
from validate_ct_codes import validate_ct_codes, CTCodeError  # noqa: E402

# Census Geocoder: coordinates -> geographies. layers=86 is the county layer.
# benchmark=4 (Public_AR_Current). vintage=4 is the current default vintage;
# vintage=419 returns CT's old (pre-2022) county codes.
_BASE_URL = "https://geocoding.geo.census.gov/geocoder/geographies/coordinates"
_DEFAULT_VINTAGE = "4"
_CT_VINTAGE = "419"  # old CT county codes (09001-09015), not planning regions
_SLEEP_SECONDS = 0.5  # be polite to the free API / avoid rate limiting
_MAX_RETRIES = 3      # attempts per row before giving up


def _query_county(lon, lat, vintage):
    """Return (state_fips, county_fips) for a point, or None on any failure.

    Retries up to _MAX_RETRIES times with exponential backoff so transient
    rate-limit or timeout errors don't leave rows blank.
    """
    params = {
        "x": lon,
        "y": lat,
        "benchmark": "4",
        "vintage": vintage,
        "layers": "86",
        "format": "json",
    }
    last_exc = None
    for attempt in range(_MAX_RETRIES):
        try:
            resp = requests.get(_BASE_URL, params=params, timeout=30)
            resp.raise_for_status()
            counties = resp.json()["result"]["geographies"]["Counties"]
            if not counties:
                return None
            county = counties[0]
            return county["STATE"], county["COUNTY"]
        except (requests.RequestException, KeyError, ValueError) as exc:
            last_exc = exc
            if attempt < _MAX_RETRIES - 1:
                wait = 2 ** attempt
                print(f"    retrying in {wait}s (attempt {attempt + 1}/{_MAX_RETRIES}): {exc}")
                time.sleep(wait)
    raise last_exc


def lookup_fips(lon, lat):
    """Look up the zero-padded 5-char county FIPS for a lon/lat.

    Returns the FIPS string, or "" if the lookup fails. CT points (state "09")
    are re-queried with vintage=419 so they come back as old county codes.
    """
    result = _query_county(lon, lat, _DEFAULT_VINTAGE)
    if result is None:
        return ""
    state, county = result

    # Connecticut: re-query for old county codes instead of planning regions.
    if state == "09":
        ct_result = _query_county(lon, lat, _CT_VINTAGE)
        if ct_result is not None:
            state, county = ct_result

    return f"{state.zfill(2)}{county.zfill(3)}"


def add_fips(input_csv, output_csv=None):
    """Read input_csv, add a `fips` column, validate CT, write output_csv."""
    input_path = Path(input_csv)
    if output_csv is None:
        output_path = input_path.with_name(f"{input_path.stem}_with_fips.csv")
    else:
        output_path = Path(output_csv)

    df = pd.read_csv(input_path)
    for col in ("latitude", "longitude"):
        if col not in df.columns:
            raise ValueError(f"input {input_path} is missing required column {col!r}")

    n = len(df)
    print(f"Looking up FIPS for {n} rows in {input_path} ...")

    fips_values = []
    failures = 0
    for i, row in df.iterrows():
        lat = row["latitude"]
        lon = row["longitude"]
        try:
            fips = lookup_fips(lon, lat)
        except (requests.RequestException, ValueError, KeyError) as exc:
            fips = ""
            print(f"  WARNING: row {i} ({lat}, {lon}) lookup failed: {exc}")

        if fips == "":
            failures += 1
            label = row["name"] if "name" in df.columns else f"row {i}"
            print(f"  WARNING: no FIPS for {label} ({lat}, {lon}); leaving empty")

        fips_values.append(fips)
        print(f"  [{i + 1}/{n}] {fips or 'EMPTY'}")
        time.sleep(_SLEEP_SECONDS)

    df["fips"] = fips_values

    # Validate CT codes before writing. Only check rows that actually got a FIPS,
    # since the gate requires every value to be a non-empty string.
    resolved = df[df["fips"] != ""]
    try:
        validate_ct_codes(resolved, fips_col="fips")
    except CTCodeError as exc:
        print(f"ERROR: CT validation failed, not writing output: {exc}")
        raise

    df.to_csv(output_path, index=False)
    print(f"Done. {n - failures}/{n} rows resolved. Wrote {output_path}")
    if failures:
        print(f"{failures} row(s) have an empty fips and need manual review.")
    return output_path


def main(argv):
    if len(argv) < 2 or len(argv) > 3:
        print(__doc__)
        print("error: expected 1 or 2 arguments")
        return 2
    input_csv = argv[1]
    output_csv = argv[2] if len(argv) == 3 else None
    add_fips(input_csv, output_csv)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
