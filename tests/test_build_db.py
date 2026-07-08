"""Tests for src/build_db.py — the SQLite builder and its dynamically
assembled master view, which previously had no dedicated coverage.

Adapted from the agent-legibility branch (its version targeted a loaders.py
refactor that never merged). The test intents survive; the fixtures target
build_db's actual structure: required sources fail loudly when missing,
late-arriving sources gate with None, and the indices table stays OUT of the
master view (acyclic data DAG).
"""
import sqlite3
import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import build_db


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
    "county": ["Fairfield", "Atlantic", "Albany"],
    "state": ["CT", "NJ", "NY"],
    "acute_stroke_mortality_per_100k": [20.0, 25.0, 30.0],
})

_GEOGRAPHIC = pd.DataFrame({
    "fips": ["09001", "34001", "36001"],
    "county": ["Fairfield", "Atlantic", "Albany"],
    "state": ["Connecticut", "New Jersey", "New York"],  # full names on purpose
    "drive_time_min": [12.5, 9.0, 15.0],
})


@pytest.fixture
def db_env(tmp_path, monkeypatch):
    """Tmp data dir with every REQUIRED source; DB written to tmp too."""
    monkeypatch.setattr(build_db, "DATA", tmp_path)
    monkeypatch.setattr(build_db, "DB_PATH", tmp_path / "stroke_burden.db")
    _SPINE.to_csv(tmp_path / "ny_nj_ct_fips.csv", index=False)
    _ACS.to_csv(tmp_path / "acs_data.csv", index=False)
    _MORTALITY.to_csv(tmp_path / "stroke_mortality.csv", index=False)
    geo_dir = tmp_path / "geographic_accessibility_data"
    geo_dir.mkdir()
    _GEOGRAPHIC.to_csv(geo_dir / "geographic_stroke_accessibility.csv", index=False)
    return tmp_path


def _connect():
    return sqlite3.connect(build_db.DB_PATH)


def _tables():
    con = _connect()
    tables = {r[0] for r in con.execute(
        "SELECT name FROM sqlite_master WHERE type='table'")}
    con.close()
    return tables


def test_creates_tables_for_available_sources_only(db_env):
    build_db.build_db()
    tables = _tables()
    assert {"counties", "acs", "mortality", "geographic"} <= tables
    for absent in ("cdc_places", "pop_density", "scai", "indices"):
        assert absent not in tables


def test_master_view_joins_correctly(db_env):
    build_db.build_db()
    con = _connect()
    master = pd.read_sql("SELECT * FROM master", con)
    con.close()
    assert len(master) == 3
    row = master.set_index("fips").loc["09001"]
    assert row["county"] == "Fairfield"  # "County" suffix stripped by the spine loader
    assert row["poverty_rate"] == 8.1
    assert row["acute_stroke_mortality_per_100k"] == 20.0
    assert row["drive_time_min"] == 12.5


def test_master_view_has_no_duplicate_columns(db_env):
    build_db.build_db()
    con = _connect()
    cols = [d[0] for d in con.execute("SELECT * FROM master LIMIT 1").description]
    con.close()
    assert len(cols) == len(set(cols)), f"duplicate columns in master view: {cols}"


def test_scai_wires_in_when_the_file_appears(db_env):
    scai_dir = db_env / "scai_data"
    scai_dir.mkdir()
    pd.DataFrame({
        "fips": ["09001", "34001", "36001"],
        "stroke_centers_per_100k": [1.1, 2.2, 3.3],
    }).to_csv(scai_dir / "scai_data.csv", index=False)
    build_db.build_db()
    con = _connect()
    master = pd.read_sql("SELECT * FROM master", con)
    con.close()
    assert "scai" in _tables()
    assert "stroke_centers_per_100k" in master.columns


def test_indices_table_loads_but_stays_out_of_master_view(db_env):
    # The index scores derive FROM master, so folding them back in would make
    # the data DAG cyclic — they get their own table, joined explicitly.
    pd.DataFrame({
        "fips": ["09001", "34001", "36001"],
        "sri": [50.0, 60.0, 70.0],
        "scai": [40.0, 45.0, 55.0],
        "gai": [30.0, 80.0, 90.0],
        "sbpi": [55.0, 50.0, 45.0],
        "sbpi_class": [2, 1, 1],
    }).to_csv(db_env / "indices.csv", index=False)
    build_db.build_db()
    con = _connect()
    master_cols = [d[0] for d in con.execute("SELECT * FROM master LIMIT 1").description]
    joined = pd.read_sql(
        "SELECT m.fips, i.sbpi FROM master m JOIN indices i USING (fips)", con)
    con.close()
    assert "indices" in _tables()
    assert "sri" not in master_cols and "sbpi" not in master_cols
    assert len(joined) == 3  # explicit join is the supported path


def test_missing_required_source_fails_loudly(db_env):
    # acs/mortality/geographic are REQUIRED: a vanished core file must raise,
    # never silently produce a thinner master view.
    (db_env / "acs_data.csv").unlink()
    with pytest.raises(FileNotFoundError):
        build_db.build_db()


def test_rebuild_replaces_existing_db(db_env):
    build_db.build_db()
    build_db.build_db()  # second run must not fail or duplicate anything
    con = _connect()
    n = con.execute("SELECT COUNT(*) FROM master").fetchone()[0]
    con.close()
    assert n == 3
