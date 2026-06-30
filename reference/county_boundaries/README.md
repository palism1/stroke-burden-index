## County boundaries

`ny_nj_ct_counties.geojson` — simplified county polygons for all 91 NY/NJ/CT counties, keyed on `fips`. Static reference geometry, committed like `reference/ct_crosswalk/ct_town_crosswalk.csv`, not regenerated as part of the data pipeline.

### Schema

| Column | Description |
|---|---|
| `fips` | 5-character zero-padded county FIPS, same convention as every other file in this project |
| `county` | county name, no "County" suffix |
| `state` | 2-letter abbreviation (NY, NJ, CT) |
| `geometry` | simplified polygon, WGS84 (EPSG:4326), per the GeoJSON spec |

### Usage

```python
import geopandas as gpd
counties = gpd.read_file("reference/county_boundaries/ny_nj_ct_counties.geojson")
merged = counties.merge(df, on="fips")
```

Or hand the file path directly to a non-geopandas tool — Plotly's `px.choropleth_map` and similar accept a GeoJSON file or URL natively.

### Connecticut vintage note

Source is the Census TIGER/Line **2019** county shapefile, used for all three states. 2019 is the last vintage before Connecticut switched from its 8 legacy counties (09001–09015) to 9 planning regions (09110–09190) in 2022, so it lines up with the old-county system this project standardizes on (see `reference/ct_crosswalk/validate_ct_codes.py`). NY and NJ boundaries are stable across vintages, so using 2019 for all three keeps the whole file to one consistent download instead of stitching two vintages together.

### Regenerating

```bash
python src/build_county_boundaries.py
```

Downloads the TIGER shapefile (cached in `data/raw/tiger/`, gitignored), filters to NY/NJ/CT, validates the result against `data/ny_nj_ct_fips.csv` and the CT FIPS gate, simplifies the geometry for web use, and overwrites the GeoJSON above. Nobody needs to run this to *use* the file — only to rebuild it.

Simplification can occasionally distort a small county or open a gap between two counties that used to share a border. The script checks for both (area change beyond 2%, or a gap wider than 100m between previously-touching neighbors) and, if anything trips, writes a local overlay map to `data/interim/county_boundary_qa.html` (original outline vs. simplified outline, zoomed to the flagged counties only) — open it in a browser to confirm before committing a rebuilt file. On the current build, nothing was flagged.
