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
    assert pd.api.types.is_string_dtype(master["fips"]), "fips column should be string dtype"


def test_master_fips_are_5_chars():
    master = build_master()
    bad = master[master["fips"].str.len() != 5]["fips"].tolist()
    assert not bad, f"FIPS codes with wrong length: {bad}"


def test_master_no_missing_values():
    master = build_master()
    missing = master.isnull().sum()
    missing = missing[missing > 0]
    assert missing.empty, f"unexpected missing values in: {dict(missing)}"


# SCAI loader (file not collected yet — both paths must work)

SCAI_COLUMNS = [
    "hospitals_per_100k",
    "hospital_beds_per_100k",
    "pcp_per_100k",
    "neurologists_per_100k",
    "stroke_centers_per_100k",
]


def _mirror_data_dir(tmp_path):
    """Symlink every real data file into a tmp data dir so DATA can be redirected."""
    import merge

    mirror = tmp_path / "data"
    mirror.mkdir()
    for entry in merge.DATA.iterdir():
        if entry.name != "scai_data":
            (mirror / entry.name).symlink_to(entry)
    return mirror


def test_master_skips_scai_when_file_absent(tmp_path, monkeypatch, capsys):
    import merge

    monkeypatch.setattr(merge, "DATA", _mirror_data_dir(tmp_path))
    master = build_master()
    assert len(master) == 91
    assert not any(c in master.columns for c in SCAI_COLUMNS)
    assert "skipped (file not found): scai" in capsys.readouterr().out


def test_build_master_never_writes_the_real_master(tmp_path, monkeypatch):
    # Regression: build_master() used to write master.csv as a side effect.
    # With DATA monkeypatched to the symlink mirror, that write followed the
    # master.csv symlink and clobbered the real file with fixture data —
    # every local pytest run silently corrupted data/master.csv.
    import merge

    real_master = merge.DATA / "master.csv"
    before = real_master.read_bytes() if real_master.exists() else None

    monkeypatch.setattr(merge, "DATA", _mirror_data_dir(tmp_path))
    build_master()

    after = real_master.read_bytes() if real_master.exists() else None
    assert before == after, "build_master() must not write data/master.csv"


def test_master_picks_up_scai_when_file_lands(tmp_path, monkeypatch):
    import merge

    mirror = _mirror_data_dir(tmp_path)
    spine = pd.read_csv(mirror / "ny_nj_ct_fips.csv", dtype={"fips": str})
    scai = pd.DataFrame({"fips": spine["fips"]})
    for col in SCAI_COLUMNS:
        scai[col] = 1.0
    (mirror / "scai_data").mkdir()
    scai.to_csv(mirror / "scai_data" / "scai_data.csv", index=False)

    monkeypatch.setattr(merge, "DATA", mirror)
    master = build_master()
    assert len(master) == 91
    for col in SCAI_COLUMNS:
        assert col in master.columns, f"expected SCAI column {col} in master"
        assert master[col].notna().all()
