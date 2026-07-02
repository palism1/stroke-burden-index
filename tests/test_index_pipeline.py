import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from index_pipeline import build_index

rng = np.random.default_rng(42)


def _agreeing_frame(n=20):
    """All variables increase together — the true ranking is the row order."""
    base = np.arange(n, dtype=float)
    return pd.DataFrame({
        "a": base,
        "b": base * 2 + rng.normal(0, 0.1, n),
        "c": base + 5 + rng.normal(0, 0.1, n),
    })


def test_reproduces_known_ordering():
    df = _agreeing_frame()
    scores = build_index(df, ["a", "b", "c"]).scores
    assert list(scores.sort_values().index) == list(df.index)
    assert scores.iloc[0] == 0.0
    assert scores.iloc[-1] == 100.0


def test_scores_bounded_0_100():
    df = pd.DataFrame(rng.normal(size=(50, 4)), columns=list("abcd"))
    scores = build_index(df, list("abcd")).scores
    assert scores.min() == 0.0
    assert scores.max() == 100.0
    assert scores.between(0, 100).all()


def test_sign_invariance():
    # PCA component signs are arbitrary; the sign check must make the final
    # scores identical whichever way PC1 happens to come out. Negating every
    # input and flipping every variable is the same aligned problem.
    df = _agreeing_frame()
    variables = ["a", "b", "c"]
    plain = build_index(df, variables).scores
    negated = build_index(-df, variables, flip=variables).scores
    assert np.allclose(plain, negated)


def test_flip_reverses_a_variables_contribution():
    df = _agreeing_frame()
    # With "a" flipped, a row that is high on raw "a" contributes low.
    # Single-variable index makes the effect exact: order reverses.
    ascending = build_index(df, ["a"]).scores
    descending = build_index(df, ["a"], flip=["a"]).scores
    assert np.allclose(ascending, 100 - descending)


def test_nan_raises_and_names_variable():
    df = _agreeing_frame()
    df.loc[3, "b"] = np.nan
    with pytest.raises(ValueError, match=r"NaN in \['b'\]"):
        build_index(df, ["a", "b", "c"])


def test_missing_variable_raises():
    with pytest.raises(ValueError, match="not in DataFrame"):
        build_index(_agreeing_frame(), ["a", "nope"])


def test_flip_not_in_variables_raises():
    with pytest.raises(ValueError, match="flip entries not in variables"):
        build_index(_agreeing_frame(), ["a", "b"], flip=["c"])


def test_zero_variance_variable_raises():
    df = _agreeing_frame()
    df["a"] = 7.0
    with pytest.raises(ValueError, match="zero-variance"):
        build_index(df, ["a", "b"])


def test_empty_variables_raises():
    with pytest.raises(ValueError, match="no variables"):
        build_index(_agreeing_frame(), [])


def test_loadings_and_explained_variance():
    df = _agreeing_frame()
    result = build_index(df, ["a", "b", "c"])
    # Strongly correlated variables: PC1 dominates and all loadings agree
    # in sign after the sign correction.
    assert result.explained_variance_ratio > 0.95
    assert (result.loadings > 0).all()
    assert list(result.loadings.index) == ["a", "b", "c"]


def test_scores_align_to_df_index():
    df = _agreeing_frame()
    df.index = [f"county_{i}" for i in range(len(df))]
    result = build_index(df, ["a", "b"], name="svi")
    assert list(result.scores.index) == list(df.index)
    assert result.scores.name == "svi"


def test_gai_orientation_end_to_end():
    # GAI per plan 2c: 4 distance/time variables, all flipped so that the
    # closest county scores 100 (best access) and the farthest scores 0.
    n = 10
    dist = np.linspace(5, 120, n)
    df = pd.DataFrame({
        "drive_time_min": dist,
        "drive_time_advanced": dist * 1.4 + rng.normal(0, 0.5, n),
        "nearest_stroke_distance": dist * 0.8 + rng.normal(0, 0.5, n),
        "nearest_stroke_distance_advanced": dist * 1.1 + rng.normal(0, 0.5, n),
    })
    variables = list(df.columns)
    gai = build_index(df, variables, flip=variables, name="gai").scores
    assert gai.iloc[0] == 100.0   # closest county = best access
    assert gai.iloc[-1] == 0.0    # farthest county = worst access
