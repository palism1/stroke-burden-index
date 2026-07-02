"""
Schema contract checks for county-level data files.

Enforces the conventions in data/data_dictionary.md:
  - fips is a string column of zero-padded 5-digit codes
  - every fips belongs to the 91-county NY/NJ/CT spine, with no duplicates
  - column names are lowercase snake_case
  - one row per county (91), unless the file is explicitly exempt

Deliberately NOT checked: county/state string formats. Those have known,
documented inconsistencies that merge.py harmonizes at merge time — see the
"Known inconsistencies" table in the data dictionary.

Enforcement lives in tests/test_data_contracts.py (run by CI), not inside the
pipelines, so a failing contract blocks a PR without blocking local exploration.
"""

import re
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent
SPINE_PATH = REPO_ROOT / "data" / "ny_nj_ct_fips.csv"

_FIPS_RE = re.compile(r"^\d{5}$")
_SNAKE_CASE_RE = re.compile(r"^[a-z][a-z0-9_]*$")


class SchemaError(ValueError):
    """A data file violates the project's schema conventions."""


def load_spine_fips() -> set[str]:
    spine = pd.read_csv(SPINE_PATH, dtype={"fips": str})
    return set(spine["fips"])


def validate_schema(
    df: pd.DataFrame,
    name: str,
    *,
    expected_columns: list[str] | None = None,
    expect_rows: int | None = 91,
    spine_fips: set[str] | None = None,
) -> None:
    """Raise SchemaError describing every violation found in df.

    name             label used in error messages (usually the file path)
    expected_columns exact column set the file must have, in any order
    expect_rows      required row count; pass None for files that are not
                     one-row-per-county
    spine_fips       the valid fips set; loaded from the 91-county spine
                     file when omitted
    """
    problems: list[str] = []

    bad_names = [c for c in df.columns if not _SNAKE_CASE_RE.match(str(c))]
    if bad_names:
        problems.append(f"columns not lowercase snake_case: {bad_names}")

    if expected_columns is not None:
        missing = sorted(set(expected_columns) - set(df.columns))
        extra = sorted(set(df.columns) - set(expected_columns))
        if missing:
            problems.append(f"missing expected columns: {missing}")
        if extra:
            problems.append(f"unexpected columns: {extra}")

    if expect_rows is not None and len(df) != expect_rows:
        problems.append(f"expected {expect_rows} rows, got {len(df)}")

    if "fips" not in df.columns:
        problems.append("no fips column")
    else:
        fips = df["fips"]
        if not pd.api.types.is_string_dtype(fips):
            problems.append(
                f"fips must be read as string (dtype={{'fips': str}}), got {fips.dtype}"
            )
        else:
            malformed = sorted(fips[~fips.str.match(_FIPS_RE)].unique())
            if malformed:
                problems.append(f"fips values not zero-padded 5-digit: {malformed}")
            else:
                if spine_fips is None:
                    spine_fips = load_spine_fips()
                unknown = sorted(set(fips) - spine_fips)
                if unknown:
                    problems.append(f"fips not in the 91-county spine: {unknown}")
            dupes = sorted(fips[fips.duplicated()].unique())
            if dupes:
                problems.append(f"duplicate fips: {dupes}")

    if problems:
        raise SchemaError(f"{name}: " + "; ".join(problems))
