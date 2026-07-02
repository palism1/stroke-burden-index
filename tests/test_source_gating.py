"""Every source loader must run the CT gate on its own file.

A source CSV arriving in planning-region codes (09110-09190) used to left-join
into 8 blank CT rows with no error. These tests pin that it now fails loudly
at load time.
"""
import sys
from pathlib import Path
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "reference" / "ct_crosswalk"))

import loaders
from merge import build_master
from validate_ct_codes import CTCodeError


_SPINE = pd.DataFrame({
    "fips": ["09001", "34001", "36001"],
    "county": ["Fairfield County", "Atlantic County", "Albany County"],
    "state": ["CT", "NJ", "NY"],
})


@pytest.fixture
def data_dir(tmp_path, monkeypatch):
    """Point the shared loaders at a tmp data dir with just a spine in it."""
    monkeypatch.setattr(loaders, "DATA", tmp_path)
    _SPINE.to_csv(tmp_path / "ny_nj_ct_fips.csv", index=False)
    return tmp_path


def test_region_coded_source_raises_at_load(data_dir):
    acs = pd.DataFrame({"fips": ["09110", "34001", "36001"], "poverty_rate": [1.0, 2.0, 3.0]})
    acs.to_csv(data_dir / "acs_data.csv", index=False)
    with pytest.raises(CTCodeError, match="09110"):
        loaders.load_acs()


def test_build_master_stops_on_region_coded_source(data_dir):
    acs = pd.DataFrame({"fips": ["09110", "34001", "36001"], "poverty_rate": [1.0, 2.0, 3.0]})
    acs.to_csv(data_dir / "acs_data.csv", index=False)
    with pytest.raises(CTCodeError, match="09110"):
        build_master()


def test_build_master_skips_missing_sources_and_joins_the_rest(data_dir):
    acs = pd.DataFrame({"fips": ["09001", "34001", "36001"], "poverty_rate": [1.0, 2.0, 3.0]})
    acs.to_csv(data_dir / "acs_data.csv", index=False)
    master = build_master()
    assert len(master) == 3
    assert "poverty_rate" in master.columns
    assert master.set_index("fips").loc["09001", "poverty_rate"] == 1.0


def test_clean_ct_source_passes_the_gate(data_dir):
    acs = pd.DataFrame({"fips": ["09001", "34001"], "poverty_rate": [1.0, 2.0]})
    acs.to_csv(data_dir / "acs_data.csv", index=False)
    result = loaders.load_acs()
    assert list(result.columns) == ["fips", "poverty_rate"]
