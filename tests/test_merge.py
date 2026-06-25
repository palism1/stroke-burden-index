import sys
from pathlib import Path
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "reference" / "ct_crosswalk"))

from merge import _strip_county_suffix, build_master


# _strip_county_suffix

def test_strips_county_suffix():
    s = pd.Series(["Albany County", "Bergen County"])
    assert list(_strip_county_suffix(s)) == ["Albany", "Bergen"]


def test_strip_leaves_no_suffix_unchanged():
    s = pd.Series(["Albany", "Bergen"])
    assert list(_strip_county_suffix(s)) == ["Albany", "Bergen"]


def test_strips_st_lawrence():
    s = pd.Series(["St. Lawrence County"])
    assert list(_strip_county_suffix(s)) == ["St. Lawrence"]


def test_strips_new_york_county():
    s = pd.Series(["New York County"])
    assert list(_strip_county_suffix(s)) == ["New York"]


def test_does_not_strip_mid_word_county():
    # "County" appearing mid-string should not be touched
    s = pd.Series(["County Road"])
    assert list(_strip_county_suffix(s)) == ["County Road"]


# build_master integration

def test_master_has_91_rows():
    master = build_master()
    assert len(master) == 91, f"expected 91 rows, got {len(master)}"


def test_master_no_duplicate_fips():
    master = build_master()
    assert not master["fips"].duplicated().any(), "duplicate FIPS codes in master"


def test_master_fips_are_strings():
    master = build_master()
    assert master["fips"].dtype == object, "fips column should be string (object dtype)"


def test_master_fips_are_5_chars():
    master = build_master()
    bad = master[master["fips"].str.len() != 5]["fips"].tolist()
    assert not bad, f"FIPS codes with wrong length: {bad}"


def test_master_no_missing_values():
    master = build_master()
    missing = master.isnull().sum()
    missing = missing[missing > 0]
    assert missing.empty, f"unexpected missing values in: {dict(missing)}"
