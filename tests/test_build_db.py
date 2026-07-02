"""Tests for src/build_db.py — the SQLite builder and its dynamically
assembled master view, which previously had no coverage at all."""
import sqlite3
import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "reference" / "ct_crosswalk"))

import build_db
import loaders


_SPINE = pd.DataFrame({
    "fips": ["09001", "34001", "36001"],
    "county": ["Fairfield County", "Atlantic County", "Albany County"],
    "state": ["CT", "NJ", "NY"],
})

_ACS = pd.DataFrame({
    "fips": ["09001", "34001", "36001"],
    "county": ["Fairfield", "Atlantic", "Albany"],
    "state": ["CT", "NJ", "NY"],
    "poverty_rate": [8.1, 11.2, 12.3],
})

_MORTALITY = pd.DataFrame({
    "fips": ["09001", "34001", "36001"],
    "acute_stroke_mortality_per_100k": [20.0, 25.0, 30.0],
})


@pytest.fixture
def db_env(tmp_path, monkeypatch):
    """Tmp data dir with spine + acs + mortality; DB written to tmp too."""
    monkeypatch.setattr(loaders, "DATA", tmp_path)
    monkeypatch.setattr(build_db, "DB_PATH", tmp_path / "stroke_burden.db")
    _SPINE.to_csv(tmp_path / "ny_nj_ct_fips.csv", index=False)
    _ACS.to_csv(tmp_path / "acs_data.csv", index=False)
    _MORTALITY.to_csv(tmp_path / "stroke_mortality.csv", index=False)
    return tmp_path


def _connect():
    return sqlite3.connect(build_db.DB_PATH)


def test_creates_tables_for_available_sources_only(db_env):
    build_db.build_db()
    con = _connect()
    tables = {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    con.close()
    assert {"counties", "acs", "mortality"} <= tables
    for absent in ("geographic", "cdc_places", "pop_density", "scai"):
        assert absent not in tables


def test_master_view_joins_correctly(db_env):
    build_db.build_db()
    con = _connect()
    master = pd.read_sql("SELECT * FROM master", con)
    con.close()
    assert len(master) == 3
    row = master.set_index("fips").loc["09001"]
    assert row["county"] == "Fairfield"  # suffix stripped by the spine loader
    assert row["poverty_rate"] == 8.1
    assert row["acute_stroke_mortality_per_100k"] == 20.0


def test_master_view_has_no_duplicate_columns(db_env):
    build_db.build_db()
    con = _connect()
    cols = [d[0] for d in con.execute("SELECT * FROM master LIMIT 1").description]
    con.close()
    assert len(cols) == len(set(cols)), f"duplicate columns in master view: {cols}"


def test_scai_wires_in_when_the_file_appears(db_env):
    scai = pd.DataFrame({"fips": ["09001", "34001", "36001"],
                         "stroke_centers_per_100k": [1.1, 2.2, 3.3]})
    scai.to_csv(db_env / "scai_data.csv", index=False)
    build_db.build_db()
    con = _connect()
    tables = {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    master = pd.read_sql("SELECT * FROM master", con)
    con.close()
    assert "scai" in tables
    assert "stroke_centers_per_100k" in master.columns


def test_rebuild_replaces_existing_db(db_env):
    build_db.build_db()
    build_db.build_db()  # second run must not fail or duplicate anything
    con = _connect()
    n = con.execute("SELECT COUNT(*) FROM master").fetchone()[0]
    con.close()
    assert n == 3
