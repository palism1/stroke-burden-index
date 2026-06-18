# ============================================================================
# FILE MAP
#   path:    reference/ct_crosswalk/validate_ct_codes.py
#   role:    RUNTIME GATE. Import validate_ct_codes() and call it at the TOP of
#            any step that joins on FIPS, BEFORE the first CT-involving join.
#   reads:   reference/ct_crosswalk/ct_town_crosswalk.csv  (for the valid sets)
#   raises:  CTCodeError listing any CT codes that don't fit the chosen system.
#   note:    DEFAULT_SYSTEM is the canonical-code decision, which is ON HOLD
#            pending Ngan. Leave it at "county_2020" and call the gate with
#            system left at default.
# ============================================================================
from pathlib import Path
import pandas as pd

# Repo-relative to this file, so it resolves no matter the caller's cwd.
CROSSWALK_PATH = Path(__file__).resolve().parent / "ct_town_crosswalk.csv"  # TWEAK if the file moves

DEFAULT_SYSTEM = "county_2020"  # DO NOT TOUCH — canonical system on hold pending Ngan

_SYSTEM_COLUMN = {
    "county_2020": "county_fips",   # CT's 8 legacy counties      (09001-09015)
    "region_2022": "region_fips",   # CT's 9 planning regions     (09110-09190)
}


class CTCodeError(ValueError):
    """A table carries Connecticut FIPS codes that don't match the expected system."""


def _valid_ct_codes(system):
    if system not in _SYSTEM_COLUMN:
        raise ValueError(f"unknown system {system!r}; expected one of {sorted(_SYSTEM_COLUMN)}")
    codes = pd.read_csv(CROSSWALK_PATH, dtype=str)[_SYSTEM_COLUMN[system]]
    return set(codes)


def validate_ct_codes(df, fips_col, system=DEFAULT_SYSTEM):
    """Stop a join from silently dropping Connecticut.

    Checks every CT FIPS (codes starting with '09') in df[fips_col] against the
    valid set for `system`. Returns df unchanged if clean; raises CTCodeError
    (listing the offenders) if not. Also fails loudly if any code isn't a
    string, because an int FIPS has already lost its leading zero.
    """
    col = df[fips_col]

    non_string = [v for v in col.tolist() if not isinstance(v, str)]
    if non_string:
        raise CTCodeError(
            f"{fips_col!r} has non-string FIPS (leading zeros already lost): {non_string[:10]}"
        )

    ct_codes = {v for v in col.tolist() if v.startswith("09")}
    valid = _valid_ct_codes(system)
    bad = sorted(ct_codes - valid)
    if bad:
        raise CTCodeError(
            f"CT FIPS codes not valid for system={system!r}: {bad}. "
            f"(Did the data arrive in the other code system?)"
        )
    return df
