# ============================================================================
# FILE MAP
#   path:    reference/ct_crosswalk/build_ct_crosswalk.py
#   role:    PROVENANCE — regenerates the clean crosswalk from the raw pull.
#            NOT imported by the pipeline at runtime. Run by hand only.
#   reads:   reference/ct_crosswalk/ct-town-to-planning-region.raw.csv
#   writes:  reference/ct_crosswalk/ct_town_crosswalk.csv
#   verify:  prints "169 towns, 8 counties, 9 regions"; all asserts must pass.
# ============================================================================
#
# Every FIPS is treated as a ZERO-PADDED STRING. The raw source dropped the
# leading zero on Connecticut's "09" codes (they look like 9-digit numbers),
# so the first job here is to restore that zero. Never read a FIPS as an int.
#
from pathlib import Path
import pandas as pd

HERE = Path(__file__).resolve().parent
RAW = HERE / "ct-town-to-planning-region.raw.csv"   # DO NOT TOUCH (vendored source pull)
OUT = HERE / "ct_town_crosswalk.csv"                # generated artifact

# CT's 8 legacy counties. Small, stable, well-known -> safe to hardcode.
# Cross-checked against data/ny_nj_ct_fips.csv on main.
COUNTY_NAMES = {  # TWEAK only if the legacy county names/codes ever change
    "09001": "Fairfield County",
    "09003": "Hartford County",
    "09005": "Litchfield County",
    "09007": "Middlesex County",
    "09009": "New Haven County",
    "09011": "New London County",
    "09013": "Tolland County",
    "09015": "Windham County",
}


def build():
    # encoding utf-8-sig strips the BOM the raw file ships with.
    raw = pd.read_csv(RAW, dtype=str, encoding="utf-8-sig").fillna("")

    df = pd.DataFrame()
    df["town_name"] = raw["town_name"].str.strip()
    # Restore zero padding: CT town GEOIDs are 10 chars, county-equiv codes 5.
    df["town_fips_2020"] = raw["town_fips_2020"].str.strip().str.zfill(10)
    df["town_fips_2022"] = raw["town_fips_2022"].str.strip().str.zfill(10)
    df["county_fips"] = df["town_fips_2020"].str[:5]
    df["county_name"] = df["county_fips"].map(COUNTY_NAMES)
    df["region_fips"] = raw["ce_fips_2022"].str.strip().str.zfill(5)
    df["region_name"] = raw["ce_name_2022"].str.strip()

    # ---- gate: fail loudly if the source shape ever drifts -------------------
    assert len(df) == 169, f"expected 169 towns, got {len(df)}"
    assert df["county_fips"].nunique() == 8, f"expected 8 counties, got {df['county_fips'].nunique()}"
    assert df["region_fips"].nunique() == 9, f"expected 9 regions, got {df['region_fips'].nunique()}"
    assert df["county_name"].notna().all(), "unknown county FIPS found in source"
    for col, width in [("town_fips_2020", 10), ("town_fips_2022", 10),
                       ("county_fips", 5), ("region_fips", 5)]:
        assert (df[col].str.len() == width).all(), f"{col} not all {width} chars"
        assert df[col].str.isdigit().all(), f"{col} has non-digit characters"

    df = df[["town_name", "town_fips_2020", "county_fips", "county_name",
             "town_fips_2022", "region_fips", "region_name"]]
    df.to_csv(OUT, index=False)
    print(f"{len(df)} towns, {df['county_fips'].nunique()} counties, "
          f"{df['region_fips'].nunique()} regions")


if __name__ == "__main__":
    build()
