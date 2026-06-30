import sys
from pathlib import Path

import geopandas as gpd
import pytest
from shapely.geometry import Polygon, box

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from build_county_boundaries import (
    simplify_geometry,
    area_change_pct,
    adjacency_breaks,
    flag_counties,
    _OUTPUT_CRS,
)

# Two unit squares sharing an edge, positioned in the NY area so EPSG:5070
# (CONUS equal-area) reprojection behaves sanely.
_SQUARE_A = box(-74.0, 42.0, -73.0, 43.0)
_SQUARE_B = box(-73.0, 42.0, -72.0, 43.0)  # shares the x=-73 edge with A

# A higher-vertex-count polygon for testing that simplify() actually reduces points.
_JAGGED = Polygon(
    [(-74.0 + 0.01 * i, 42.0 + (0.01 if i % 2 == 0 else 0)) for i in range(50)]
)


def _gdf(rows):
    return gpd.GeoDataFrame(rows, crs=_OUTPUT_CRS)


# simplify_geometry

def test_simplify_geometry_preserves_row_count_and_crs():
    gdf = _gdf([{"fips": "36001", "county": "A", "state": "NY", "geometry": _JAGGED}])
    simplified = simplify_geometry(gdf, tolerance_m=500)
    assert len(simplified) == 1
    assert simplified.crs.to_string() == _OUTPUT_CRS


def test_simplify_geometry_reduces_vertices_for_jagged_shape():
    gdf = _gdf([{"fips": "36001", "county": "A", "state": "NY", "geometry": _JAGGED}])
    simplified = simplify_geometry(gdf, tolerance_m=2000)
    orig_vertices = len(_JAGGED.exterior.coords)
    simp_vertices = len(simplified.geometry.iloc[0].exterior.coords)
    assert simp_vertices < orig_vertices


# area_change_pct

def test_area_change_pct_zero_for_identical_geometry():
    orig = _gdf([{"fips": "36001", "county": "A", "state": "NY", "geometry": _SQUARE_A}])
    same = orig.copy()
    pct = area_change_pct(orig, same)
    assert pct.loc["36001"] == pytest.approx(0.0, abs=1e-6)


def test_area_change_pct_detects_shrinkage():
    orig = _gdf([{"fips": "36001", "county": "A", "state": "NY", "geometry": _SQUARE_A}])
    shrunk = _gdf([{"fips": "36001", "county": "A", "state": "NY", "geometry": _SQUARE_A.buffer(-0.1)}])
    pct = area_change_pct(orig, shrunk)
    assert pct.loc["36001"] > 5  # buffering inward by 0.1 deg meaningfully shrinks a 1x1 deg square


# adjacency_breaks

def test_adjacency_breaks_none_for_identical_geometry():
    orig = _gdf([
        {"fips": "36001", "county": "A", "state": "NY", "geometry": _SQUARE_A},
        {"fips": "36003", "county": "B", "state": "NY", "geometry": _SQUARE_B},
    ])
    same = orig.copy()
    assert adjacency_breaks(orig, same) == set()


def test_adjacency_breaks_detects_opened_gap():
    orig = _gdf([
        {"fips": "36001", "county": "A", "state": "NY", "geometry": _SQUARE_A},
        {"fips": "36003", "county": "B", "state": "NY", "geometry": _SQUARE_B},
    ])
    # shift B far away so the shared edge with A opens into a large gap
    shifted_b = box(-71.0, 42.0, -70.0, 43.0)
    moved = _gdf([
        {"fips": "36001", "county": "A", "state": "NY", "geometry": _SQUARE_A},
        {"fips": "36003", "county": "B", "state": "NY", "geometry": shifted_b},
    ])
    broken = adjacency_breaks(orig, moved, gap_threshold_m=100)
    assert broken == {"36001", "36003"}


def test_adjacency_breaks_ignores_gap_under_threshold():
    orig = _gdf([
        {"fips": "36001", "county": "A", "state": "NY", "geometry": _SQUARE_A},
        {"fips": "36003", "county": "B", "state": "NY", "geometry": _SQUARE_B},
    ])
    # a tiny shift (sub-meter scale gap) should not trip a generous threshold
    nudged_b = Polygon([(x + 0.0000001, y) for x, y in _SQUARE_B.exterior.coords])
    nudged = _gdf([
        {"fips": "36001", "county": "A", "state": "NY", "geometry": _SQUARE_A},
        {"fips": "36003", "county": "B", "state": "NY", "geometry": nudged_b},
    ])
    assert adjacency_breaks(orig, nudged, gap_threshold_m=100) == set()


# flag_counties

def test_flag_counties_clean_case_flags_nothing():
    orig = _gdf([
        {"fips": "36001", "county": "A", "state": "NY", "geometry": _SQUARE_A},
        {"fips": "36003", "county": "B", "state": "NY", "geometry": _SQUARE_B},
    ])
    same = orig.copy()
    assert flag_counties(orig, same) == set()


def test_flag_counties_flags_area_shrinkage():
    orig = _gdf([{"fips": "36001", "county": "A", "state": "NY", "geometry": _SQUARE_A}])
    shrunk = _gdf([{"fips": "36001", "county": "A", "state": "NY", "geometry": _SQUARE_A.buffer(-0.1)}])
    assert "36001" in flag_counties(orig, shrunk)
