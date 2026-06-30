"""
Build a simplified, web-ready county boundary GeoJSON for NY/NJ/CT.

Source: Census TIGER/Line 2019 county shapefile. The 2019 vintage is used for
all three states (not just CT) so the whole file comes from one consistent
download — and 2019 is the last vintage before Connecticut switched from its
8 legacy counties (09001-09015) to 9 planning regions (09110-09190), so this
also sidesteps the same CT vintage trap documented in
reference/ct_crosswalk/ and src/add_fips_to_geocoded.py.

Output: reference/county_boundaries/ny_nj_ct_counties.geojson (committed —
static reference geometry, like ct_town_crosswalk.csv, not regenerated data).

Geometry is simplified to keep the file small for web maps. Simplification
can distort small counties or open gaps between neighbors that used to share
a border, so this script flags any county whose area changed beyond a
threshold or whose adjacency to a neighbor broke, and writes a folium HTML
map (data/interim/, gitignored) showing original vs. simplified outlines for
just the flagged counties — open it in a browser to spot-check.

USAGE
-----
    python src/build_county_boundaries.py
"""

from pathlib import Path
import sys
import zipfile

import geopandas as gpd
import pandas as pd
import requests

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "reference" / "ct_crosswalk"))
from validate_ct_codes import validate_ct_codes  # noqa: E402

DATA = REPO_ROOT / "data"
RAW = DATA / "raw" / "tiger"
OUT_DIR = REPO_ROOT / "reference" / "county_boundaries"
QA_MAP_PATH = DATA / "interim" / "county_boundary_qa.html"

_TIGER_URL = "https://www2.census.gov/geo/tiger/TIGER2019/COUNTY/tl_2019_us_county.zip"
_ZIP_NAME = "tl_2019_us_county.zip"
_SHP_NAME = "tl_2019_us_county.shp"

_STATEFP_TO_ABBR = {"36": "NY", "34": "NJ", "09": "CT"}

_EQUAL_AREA_CRS = "EPSG:5070"  # NAD83 / Conus Albers, meters — for area calc + simplify
_OUTPUT_CRS = "EPSG:4326"      # WGS84 — required by the GeoJSON spec

_SIMPLIFY_TOLERANCE_M = 200    # simplification tolerance in meters
_AREA_CHANGE_THRESHOLD_PCT = 2.0  # flag a county if simplification changes its area more than this
_ADJACENCY_GAP_THRESHOLD_M = 100  # flag a once-touching pair if simplification opens a gap bigger than this


def _fetch_tiger_shapefile() -> Path:
    """Download and cache the TIGER2019 county shapefile. Returns the .shp path."""
    RAW.mkdir(parents=True, exist_ok=True)
    shp_path = RAW / _SHP_NAME
    if shp_path.exists():
        return shp_path

    zip_path = RAW / _ZIP_NAME
    if not zip_path.exists():
        print(f"downloading {_TIGER_URL} ...")
        resp = requests.get(_TIGER_URL, timeout=120)
        resp.raise_for_status()
        zip_path.write_bytes(resp.content)

    with zipfile.ZipFile(zip_path) as zf:
        zf.extractall(RAW)

    return shp_path


def _load_counties(shp_path: Path) -> gpd.GeoDataFrame:
    """Load the TIGER shapefile and filter to NY/NJ/CT, with fips/county/state columns."""
    gdf = gpd.read_file(shp_path)
    gdf = gdf[gdf["STATEFP"].isin(_STATEFP_TO_ABBR)].copy()
    gdf["fips"] = gdf["STATEFP"] + gdf["COUNTYFP"]
    gdf["county"] = gdf["NAME"]
    gdf["state"] = gdf["STATEFP"].map(_STATEFP_TO_ABBR)
    gdf = gdf[["fips", "county", "state", "geometry"]].reset_index(drop=True)
    return gdf.to_crs(_OUTPUT_CRS)


def _validate_against_spine(gdf: gpd.GeoDataFrame) -> None:
    """Confirm the TIGER pull resolves to exactly the project's 91-county spine."""
    spine_fips = set(pd.read_csv(DATA / "ny_nj_ct_fips.csv", dtype={"fips": str})["fips"])
    tiger_fips = set(gdf["fips"])
    missing = spine_fips - tiger_fips
    extra = tiger_fips - spine_fips
    if missing or extra:
        raise ValueError(
            f"TIGER county pull does not match the project's 91-county spine. "
            f"Missing: {sorted(missing)}. Unexpected extra: {sorted(extra)}."
        )


def simplify_geometry(gdf: gpd.GeoDataFrame, tolerance_m: float = _SIMPLIFY_TOLERANCE_M) -> gpd.GeoDataFrame:
    """Simplify polygons in an equal-area CRS, then reproject back to WGS84."""
    projected = gdf.to_crs(_EQUAL_AREA_CRS)
    projected["geometry"] = projected.geometry.simplify(tolerance_m, preserve_topology=True)
    return projected.to_crs(_OUTPUT_CRS)


def area_change_pct(orig: gpd.GeoDataFrame, simplified: gpd.GeoDataFrame) -> pd.Series:
    """Per-county % change in area (simplified vs. original), computed in an equal-area CRS."""
    orig_area = orig.to_crs(_EQUAL_AREA_CRS).set_index("fips").geometry.area
    simp_area = simplified.to_crs(_EQUAL_AREA_CRS).set_index("fips").geometry.area
    return ((simp_area - orig_area).abs() / orig_area * 100).rename("area_change_pct")


def adjacency_breaks(orig: gpd.GeoDataFrame, simplified: gpd.GeoDataFrame, gap_threshold_m: float = _ADJACENCY_GAP_THRESHOLD_M) -> set:
    """FIPS codes involved in a neighbor pair where simplification opened a visible gap.

    Independent per-polygon simplification (even with preserve_topology=True) does not
    keep shared borders pixel-identical, so a strict "still touching" check flags nearly
    every pair on sub-meter noise. Instead, measure the actual gap distance between
    once-touching neighbors after simplification and only flag pairs whose gap exceeds
    a threshold big enough to matter on a map.
    """
    proj_orig = orig.to_crs(_EQUAL_AREA_CRS)
    joined = gpd.sjoin(proj_orig, proj_orig, how="inner", predicate="touches")
    orig_pairs = {
        frozenset((a, b))
        for a, b in zip(joined["fips_left"], joined["fips_right"])
        if a != b
    }

    proj_simp = simplified.to_crs(_EQUAL_AREA_CRS).set_index("fips")
    flagged = set()
    for pair in orig_pairs:
        a, b = tuple(pair)
        gap = proj_simp.loc[a, "geometry"].distance(proj_simp.loc[b, "geometry"])
        if gap > gap_threshold_m:
            flagged.update((a, b))
    return flagged


def flag_counties(orig: gpd.GeoDataFrame, simplified: gpd.GeoDataFrame) -> set:
    """FIPS codes that need a visual spot-check: too much area change, broken adjacency,
    or invalid geometry after simplification."""
    flagged = set()

    pct = area_change_pct(orig, simplified)
    flagged.update(pct[pct > _AREA_CHANGE_THRESHOLD_PCT].index)

    flagged.update(adjacency_breaks(orig, simplified))

    invalid = simplified[~simplified.geometry.is_valid]["fips"]
    flagged.update(invalid)

    return flagged


def write_qa_map(orig: gpd.GeoDataFrame, simplified: gpd.GeoDataFrame, flagged_fips: set, out_path: Path) -> None:
    """Folium HTML map overlaying original (blue) vs. simplified (orange) outlines
    for the flagged counties only. Local file, no upload — open it in a browser."""
    import folium

    if not flagged_fips:
        print("no counties flagged — skipping QA map")
        return

    subset_orig = orig[orig["fips"].isin(flagged_fips)]
    subset_simp = simplified[simplified["fips"].isin(flagged_fips)]

    bounds = subset_orig.total_bounds  # minx, miny, maxx, maxy
    center = [(bounds[1] + bounds[3]) / 2, (bounds[0] + bounds[2]) / 2]

    m = folium.Map(location=center, zoom_start=9)
    folium.GeoJson(
        subset_orig, name="original", style_function=lambda f: {"color": "blue", "weight": 2, "fillOpacity": 0}
    ).add_to(m)
    folium.GeoJson(
        subset_simp, name="simplified", style_function=lambda f: {"color": "orange", "weight": 2, "fillOpacity": 0}
    ).add_to(m)
    folium.LayerControl().add_to(m)
    m.fit_bounds([[bounds[1], bounds[0]], [bounds[3], bounds[2]]])

    out_path.parent.mkdir(parents=True, exist_ok=True)
    m.save(str(out_path))
    print(f"flagged {len(flagged_fips)} counties: {sorted(flagged_fips)}")
    print(f"wrote QA map to {out_path.relative_to(REPO_ROOT)} — open it in a browser to spot-check")


def build_boundaries() -> Path:
    shp_path = _fetch_tiger_shapefile()
    orig = _load_counties(shp_path)
    _validate_against_spine(orig)
    validate_ct_codes(orig, fips_col="fips")

    simplified = simplify_geometry(orig)
    flagged = flag_counties(orig, simplified)
    write_qa_map(orig, simplified, flagged, QA_MAP_PATH)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUT_DIR / "ny_nj_ct_counties.geojson"
    simplified.to_file(out_path, driver="GeoJSON")
    print(f"wrote {out_path.relative_to(REPO_ROOT)}  ({len(simplified)} counties)")
    return out_path


if __name__ == "__main__":
    build_boundaries()
