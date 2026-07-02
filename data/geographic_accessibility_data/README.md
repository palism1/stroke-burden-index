## Geographic Accessibility Data

This folder contains geocoded stroke center locations and county-level accessibility outputs for NY, NJ, and CT.

For the full documentation and code, see the HTML export of the notebook: `Geographic_Accessibility_Data_Gathering.ipynb`.

### Outputs

- `geographic_stroke_accessibility.csv` — main output. One row per county (91 total). Columns: `fips`, `county`, `state`, `drive_time_min` (minutes to nearest basic center), `drive_time_advanced` (minutes to nearest advanced center), `nearest_stroke_distance` (miles to nearest basic center), `nearest_stroke_distance_advanced` (miles to nearest advanced center). Note: the `state` column uses full names ("New York", "New Jersey", "Connecticut") while other data files use abbreviations ("NY", "NJ", "CT"). Always join on `fips`, not on `state`.
  - Essex County NY and Hamilton County NY have imputed `drive_time_min` and `drive_time_advanced` values. OpenRouteService failed to route to these remote Adirondack counties, so both drive times were estimated from straight-line distance at 45 mph (`distance / 45 * 60`). The file has no empty cells — no imputation is needed by consumers.

### Geocoded stroke center files

- `ny_all_stroke_centers_geocoded.csv` — all NY stroke centers (primary, thrombectomy-capable, comprehensive) with lat/lon. 5 entries have empty coordinates.
- `nj_all_stroke_centers_geocoded.csv` — all NJ stroke centers with lat/lon. 11 entries have empty coordinates; 3 of the missing are Comprehensive centers that were manually patched inside the notebook for the distance calculation.
- `ny_primary_stroke_centers_geocoded.csv` — NY primary (basic) stroke centers only. No missing coordinates.
- `nj_primary_stroke_centers_geocoded.csv` — NJ primary stroke centers only. No missing coordinates. **Note:** in the geographic accessibility notebook, `nj_primary` was used for basic stroke centers and `nj_all` was filtered to comprehensive centers only for advanced stroke centers. Do not stack these two files to count unique stroke centers — primary centers appear in both files and would be double-counted.
- `ct_basic_geocoded.csv` — CT basic stroke centers. No missing coordinates.
- `ct_advanced_geocoded.csv` — CT advanced stroke centers. No missing coordinates.

### CT geocoding warning

The Census Geocoder API now returns Connecticut **planning region** codes (09110–09190) by default for CT coordinates, not the old county codes (09001–09015) used everywhere else in this project.

When reverse-geocoding any CT latitude/longitude using the Census API, always pass `vintage=419`:

```
https://geocoding.geo.census.gov/geocoder/geographies/coordinates
  ?x={lon}&y={lat}&benchmark=4&vintage=419&layers=86&format=json
```

Using the default `vintage=4` will silently return wrong FIPS codes for CT and those rows will not join to any other dataset.
