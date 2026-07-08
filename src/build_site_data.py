"""
Export the merged county table to docs/data/ for the static dashboard.

Outputs (both committed — the dashboard is served by GitHub Pages):
  docs/data/counties.json            one record per county, keyed by fips,
                                     plus plain-language display metadata
  docs/data/ny_nj_ct_counties.geojson  copy of the reference boundary file
                                     (reference/ is not served by Pages)

Run after any data change:
    python src/build_site_data.py

CI regenerates both files and fails if the committed copies are stale.

New columns in master.csv (e.g. scai variables, index scores) flow through
automatically: known columns get the plain-language label below, unknown
ones get a title-cased fallback until a label is added to FIELD_LABELS.
"""

import json
import shutil
from pathlib import Path

import pandas as pd

from merge import build_master

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA = REPO_ROOT / "data"
SITE_DATA = REPO_ROOT / "docs" / "data"
BOUNDARIES_SRC = REPO_ROOT / "reference" / "county_boundaries" / "ny_nj_ct_counties.geojson"
INDICES_CSV = DATA / "indices.csv"

# Plain-language labels and units for the dashboard (UX doc: general-public
# users need plain language, and values should carry visible units).
# group: which details-panel section the field belongs to.
FIELD_LABELS = {
    "total_pop":                          {"label": "Population",                                   "unit": "",       "group": "community"},
    "pop_density":                        {"label": "Population density",                           "unit": "per sq mi", "group": "community"},
    "pcnt_65_plus":                       {"label": "Residents aged 65 and over",                   "unit": "%",      "group": "community"},
    "poverty_rate":                       {"label": "Residents below the poverty line",             "unit": "%",      "group": "community"},
    "pcnt_insured":                       {"label": "Residents with health insurance",              "unit": "%",      "group": "community"},
    "pcnt_bachelors":                     {"label": "Adults with a bachelor's degree",              "unit": "%",      "group": "community"},
    "pcnt_low_income":                    {"label": "Low-income households",                        "unit": "%",      "group": "community"},
    "pcnt_middle_class":                  {"label": "Middle-income households",                     "unit": "%",      "group": "community"},
    "pcnt_upper_class":                   {"label": "Upper-income households",                      "unit": "%",      "group": "community"},
    "acute_stroke_mortality_per_100k":    {"label": "Stroke deaths (acute)",                        "unit": "per 100k", "group": "burden"},
    "sequelae_stroke_mortality_per_100k": {"label": "Stroke deaths (after-effects)",                "unit": "per 100k", "group": "burden"},
    "stroke_prevalence":                  {"label": "Adults who have had a stroke",                 "unit": "%",      "group": "burden"},
    "hypertension_prevalence":            {"label": "Adults with high blood pressure",              "unit": "%",      "group": "burden"},
    "high_cholesterol_prevalence":        {"label": "Adults with high cholesterol",                 "unit": "%",      "group": "burden"},
    "diabetes_prevalence":                {"label": "Adults with diabetes",                         "unit": "%",      "group": "burden"},
    "obesity_prevalence":                 {"label": "Adults with obesity",                          "unit": "%",      "group": "burden"},
    "smoking_prevalence":                 {"label": "Adults who smoke",                             "unit": "%",      "group": "burden"},
    "binge_drinking_prevalence":          {"label": "Adults who binge drink",                       "unit": "%",      "group": "burden"},
    "physical_inactivity":                {"label": "Adults with no physical activity",             "unit": "%",      "group": "burden"},
    "drive_time_min":                     {"label": "Drive to nearest stroke center",               "unit": "min",    "group": "access"},
    "drive_time_advanced":                {"label": "Drive to nearest advanced stroke center",      "unit": "min",    "group": "access"},
    "nearest_stroke_distance":            {"label": "Distance to nearest stroke center",            "unit": "mi",     "group": "access"},
    "nearest_stroke_distance_advanced":   {"label": "Distance to nearest advanced stroke center",   "unit": "mi",     "group": "access"},
    # SCAI variables — appear automatically once scai_data.csv lands
    "hospitals_per_100k":                 {"label": "Hospitals",                                    "unit": "per 100k", "group": "access"},
    "hospital_beds_per_100k":             {"label": "Hospital beds",                                "unit": "per 100k", "group": "access"},
    "pcp_per_100k":                       {"label": "Primary care physicians",                      "unit": "per 100k", "group": "access"},
    "neurologists_per_100k":              {"label": "Neurologists",                                 "unit": "per 100k", "group": "access"},
    "stroke_centers_per_100k":            {"label": "Stroke centers",                               "unit": "per 100k", "group": "access"},
    # Index scores — 0-100, joined from data/indices.csv (see main()). The
    # scores are unitless, so unit is "" — that renders cleanest through the
    # dashboard's formatValue ("72.7", not "72.7 0-100") and fieldLabel (the
    # metric selector / legend title show just the label, no "(0-100)" suffix).
    # Directions are MIXED (SRI up = worse, SCAI/GAI up = better) and share one
    # sequential palette, so the label is the only text that can disambiguate:
    # each label states its direction inline.
    "sri":                                {"label": "Stroke Risk Index (SRI) — higher = more risk",         "unit": "", "group": "index"},
    "scai":                               {"label": "Stroke Care Access Index (SCAI) — higher = better access", "unit": "", "group": "index"},
    "gai":                                {"label": "Geographic Accessibility Index (GAI) — higher = better access", "unit": "", "group": "index"},
    "sbpi":                               {"label": "Stroke Burden Priority Index (SBPI) — higher = higher priority", "unit": "", "group": "index"},
    # Derived in memory only inside src/compute_indices.py (_load_master) —
    # never a real master.csv column, so they never appear as a dashboard
    # metric/field. Labels exist here solely so the recommendations engine's
    # driver_1..driver_3 (which may name one of these) can look up a
    # plain-language label the same way it does for every other driver.
    "pcnt_uninsured":                     {"label": "Residents without health insurance",           "unit": "%",  "group": "access"},
    "drive_time_any":                     {"label": "Drive to nearest stroke center (any tier)",    "unit": "min", "group": "access"},
    "nearest_stroke_distance_any":        {"label": "Distance to nearest stroke center (any tier)", "unit": "mi", "group": "access"},
}

# Per-county recommendations engine (docs/DECISIONS.md 2026-07-07): the
# per-sbpi_class framework Ngan Vu drafted and shared 2026-07-08, transcribed
# verbatim. "action" for class 2 is a base sentence — _build_recommendations
# appends a bottleneck-specific clause naming whichever of sri_flag/scai_flag/
# gai_flag actually tripped, since Moderate can be reached via any one of the
# three (or, in an edge case _add_sbpi allows, two of three) deficit layers.
RECOMMENDATION_FRAMEWORK = {
    4: {
        "class_label": "Critical Priority",
        "title": "Critical Priority Zone (Stroke Care Desert)",
        "rule": "Top 25% stroke risk, bottom 25% care access, and top 25% distance to care.",
        "action": (
            "Prioritize capital allocation for deploying mobile stroke screening "
            "clinics, expanding regional telehealth networks, and optimizing "
            "emergency EMS routing."
        ),
    },
    3: {
        "class_label": "High Priority",
        "title": "High Priority / Prevention Focus",
        "rule": (
            "Top 25% stroke risk and bottom 50% care access, with acceptable "
            "geographic transit proximity."
        ),
        "action": (
            "Focus resources on clinical workforce recruitment, public "
            "preventative health campaigns, and expanding outpatient primary "
            "care networks to manage baseline risks."
        ),
    },
    2: {
        "class_label": "Moderate Priority",
        "title": "Moderate Priority / Infrastructure Monitor",
        "rule": (
            "One or more elevated deficit layers: elevated stroke risk, low "
            "clinical capacity, or poor transit geometry."
        ),
        "action": "Perform isolated infrastructure updates targeted at the specific bottleneck.",
    },
    1: {
        "class_label": "Low Priority",
        "title": "Low Priority / System Maintained",
        "rule": "High local care access, close proximity to stroke centers, and low population risk.",
        "action": (
            "Maintain current resource allocations while actively tracking "
            "long-term data trends to watch for emerging demographic shifts."
        ),
    },
}

# Moderate-class bottleneck clauses, appended in this order when the
# corresponding flag is true (a county can trip more than one without being
# Critical/High — see docs/DECISIONS.md sbpi_class rules).
MODERATE_BOTTLENECK_CLAUSES = [
    ("sri_flag", "Elevated population risk is a bottleneck here — prioritize preventive health outreach."),
    ("scai_flag", "Clinical capacity is a bottleneck here — recruit workforce or expand outpatient primary care access."),
    ("gai_flag", "Transit distance is a bottleneck here — coordinate regional hospital network routing agreements."),
]

GROUP_TITLES = {
    "burden": "Stroke burden and risk factors",
    "access": "Getting to care",
    "community": "About the community",
    "index": "Index scores",
}


def _fallback_label(column: str) -> str:
    return column.replace("_", " ").capitalize()


def _join_indices(master: pd.DataFrame) -> pd.DataFrame:
    """Left-join the computed index scores (sri, scai, gai) onto master.

    The scores live in data/indices.csv (canonical source: src/compute_indices.py),
    which is NOT part of build_master() — the data DAG is deliberately acyclic and
    the indices derive FROM master. We fold them in here, at export time, so the
    dashboard's index fields populate. Missing file -> master unchanged (the
    dashboard's matrix simply stays in its placeholder state until scores exist).

    Read with the same float_precision="round_trip" + fips-as-string convention
    the rest of the pipeline uses, so the emitted JSON is byte-stable across
    machines (matches merge._read; keeps CI's staleness gate from flaking).
    """
    if not INDICES_CSV.exists():
        return master
    indices = pd.read_csv(INDICES_CSV, dtype={"fips": str}, float_precision="round_trip")
    # sbpi_class (1-4 priority class) stays out of the dashboard export: the
    # metric selector/choropleth are built for continuous values, and the
    # matrix already derives quadrants client-side. The class lives in
    # indices.csv and the db's indices table for analysis use.
    # driver_* (top-3 risk-driver variable name + percentile, src/compute_indices.py
    # _add_drivers) and sri_flag/scai_flag/gai_flag are excluded the same way:
    # none of them is a continuous metric fit for the generic field/metric
    # selector. They flow into the dashboard separately via the "recommendations"
    # payload key (_build_recommendations), not the flat per-county fields.
    driver_columns = [f"driver_{i}{suffix}" for i in range(1, 4) for suffix in ("", "_pctile")]
    layer_flag_columns = ["sri_flag", "scai_flag", "gai_flag"]
    indices = indices.drop(columns=["sbpi_class", *layer_flag_columns, *driver_columns], errors="ignore")
    return master.merge(indices, on="fips", how="left")


def _driver_label(variable: str) -> str:
    return FIELD_LABELS.get(variable, {"label": _fallback_label(variable)})["label"]


def _moderate_action(row) -> str:
    clauses = [text for flag, text in MODERATE_BOTTLENECK_CLAUSES if row[flag]]
    base = RECOMMENDATION_FRAMEWORK[2]["action"]
    return " ".join([base, *clauses])


def _build_recommendations() -> dict:
    """Per-county recommendation: class + plain-language framework + top-3 drivers.

    Reads data/indices.csv directly (same file _join_indices reads) rather
    than the already-joined master, since the fields it needs (sbpi_class,
    the layer flags, driver_*) are deliberately excluded from that join.
    Missing file -> {} (mirrors _join_indices' missing-file behavior).
    """
    if not INDICES_CSV.exists():
        return {}
    indices = pd.read_csv(INDICES_CSV, dtype={"fips": str}, float_precision="round_trip")

    recommendations = {}
    for row in indices.itertuples():
        cls = row.sbpi_class
        framework = RECOMMENDATION_FRAMEWORK[cls]
        drivers = [
            {
                "variable": getattr(row, f"driver_{i}"),
                "label": _driver_label(getattr(row, f"driver_{i}")),
                "percentile": getattr(row, f"driver_{i}_pctile"),
            }
            for i in (1, 2, 3)
        ]
        action = _moderate_action(row._asdict()) if cls == 2 else framework["action"]
        recommendations[row.fips] = {
            "class": cls,
            "class_label": framework["class_label"],
            "title": framework["title"],
            "rule": framework["rule"],
            "action": action,
            "drivers": drivers,
        }
    return recommendations


def export_site_data(master: pd.DataFrame, recommendations: dict | None = None) -> dict:
    """Turn the master table into the JSON structure the dashboard consumes."""
    value_columns = [c for c in master.columns if c not in ("fips", "county", "state")]

    fields = {}
    for col in value_columns:
        meta = FIELD_LABELS.get(col, {"label": _fallback_label(col), "unit": "", "group": "community"})
        fields[col] = meta

    counties = {}
    for row in master.to_dict(orient="records"):
        record = {"county": row["county"], "state": row["state"]}
        for col in value_columns:
            value = row[col]
            if pd.isna(value):
                record[col] = None
            elif isinstance(value, float):
                record[col] = round(value, 2)
            else:
                record[col] = value
        counties[row["fips"]] = record

    return {
        "fields": fields,
        "groups": GROUP_TITLES,
        "counties": counties,
        "recommendations": recommendations or {},
    }


def main() -> None:
    master = _join_indices(build_master())
    payload = export_site_data(master, _build_recommendations())

    SITE_DATA.mkdir(parents=True, exist_ok=True)
    out = SITE_DATA / "counties.json"
    out.write_text(json.dumps(payload, indent=1) + "\n")

    boundaries_out = SITE_DATA / BOUNDARIES_SRC.name
    shutil.copyfile(BOUNDARIES_SRC, boundaries_out)

    print(f"wrote {out.relative_to(REPO_ROOT)}  ({len(payload['counties'])} counties, "
          f"{len(payload['fields'])} fields)")
    print(f"wrote {boundaries_out.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
