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
    result = build_index(df, ["a", "b"], name="sri")
    assert list(result.scores.index) == list(df.index)
    assert result.scores.name == "sri"


def test_duplicate_variables_raise():
    with pytest.raises(ValueError, match="duplicate variables"):
        build_index(_agreeing_frame(), ["a", "b", "a"])


def test_cancelling_variables_raise():
    # A variable and its exact negation: the aligned "majority direction"
    # is undefined, so the pipeline must refuse rather than pick a side.
    df = _agreeing_frame()
    df["anti_a"] = -df["a"]
    with pytest.raises(ValueError, match="cancel out"):
        build_index(df, ["a", "anti_a"])


def test_disagreeing_variables_raise():
    # Two anti-correlated pairs plus noise: the anchor is pure noise and
    # PC1 is a contrast between the pairs — direction is a coin flip.
    n = 60
    t = np.linspace(0, 1, n)
    u = np.sin(np.linspace(0, 9, n))
    noise = lambda: rng.normal(0, 0.01, n)
    df = pd.DataFrame({
        "p1": t + noise(), "p2": -t + noise(),
        "q1": u + noise(), "q2": -u + noise(),
    })
    with pytest.raises(ValueError, match="direction is ambiguous"):
        build_index(df, ["p1", "p2", "q1", "q2"])


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


# --- skew diagnostics & opt-in transforms -----------------------------------

def _lognormal_frame(n=400):
    """A heavily right-skewed variable ('skewed') alongside two tame ones."""
    r = np.random.default_rng(7)
    return pd.DataFrame({
        "skewed": r.lognormal(mean=0.0, sigma=1.0, size=n),
        "b": r.normal(10, 1, n),
        "c": r.normal(5, 1, n),
    })


def test_no_transform_scores_byte_identical_to_baseline():
    # Regression guard: the additive diagnostics must not perturb scores by a
    # single bit versus a call with no transforms argument at all.
    df = _agreeing_frame()
    variables = ["a", "b", "c"]
    baseline = build_index(df, variables).scores.to_numpy()
    with_arg = build_index(df, variables, transforms={}).scores.to_numpy()
    assert baseline.tobytes() == with_arg.tobytes()


def test_skewness_matches_hand_computed_value():
    # Adjusted Fisher-Pearson (pandas default). [1,2,3,4,10] worked by hand to
    # ~1.6971; a symmetric column is exactly 0. "b" is unflipped so its raw and
    # aligned skew coincide.
    df = pd.DataFrame({
        "b": [1.0, 2.0, 3.0, 4.0, 10.0],
        "sym": [1.0, 2.0, 3.0, 4.0, 5.0],
    })
    result = build_index(df, ["b", "sym"])
    assert result.skewness["b"] == pytest.approx(1.6970562748, abs=1e-9)
    assert result.skewness["sym"] == pytest.approx(0.0, abs=1e-12)


def test_log1p_reduces_absolute_skew_on_lognormal():
    df = _lognormal_frame()
    variables = ["skewed", "b", "c"]
    raw_skew = abs(build_index(df, variables).skewness["skewed"])
    logged_skew = abs(
        build_index(df, variables, transforms={"skewed": "log1p"}).skewness["skewed"]
    )
    assert raw_skew > 2.0                  # heavily skewed to begin with
    assert logged_skew < raw_skew          # the log pulls the tail in
    assert logged_skew < raw_skew / 2      # and roughly halves the skew here


def test_transform_changes_scores():
    df = _lognormal_frame()
    variables = ["skewed", "b", "c"]
    plain = build_index(df, variables).scores.to_numpy()
    logged = build_index(df, variables, transforms={"skewed": "log1p"}).scores.to_numpy()
    assert not np.allclose(plain, logged)


def test_high_skew_flags_untransformed_and_clears_when_transformed():
    df = _lognormal_frame()
    variables = ["skewed", "b", "c"]
    flagged = build_index(df, variables)
    assert "skewed" in flagged.high_skew         # |skew| > threshold, no transform
    assert "b" not in flagged.high_skew
    cleared = build_index(df, variables, transforms={"skewed": "log1p"})
    assert "skewed" not in cleared.high_skew      # transformed vars are never flagged


def test_log_requires_positive_values():
    df = _agreeing_frame()   # "a" starts at 0.0
    with pytest.raises(ValueError, match="'log' transform on 'a' needs all values > 0"):
        build_index(df, ["a", "b"], transforms={"a": "log"})


def test_log1p_requires_nonnegative_values():
    df = _agreeing_frame()
    df["a"] = df["a"] - 1.0   # now includes a negative value
    with pytest.raises(ValueError, match="'log1p' transform on 'a' needs all values >= 0"):
        build_index(df, ["a", "b"], transforms={"a": "log1p"})


def test_unknown_transform_name_raises_and_lists_options():
    with pytest.raises(ValueError, match="unknown transform 'sqrt'.*log, log1p"):
        build_index(_agreeing_frame(), ["a", "b"], transforms={"a": "sqrt"})


def test_transform_on_unknown_variable_raises():
    with pytest.raises(ValueError, match="transform entries not in variables"):
        build_index(_agreeing_frame(), ["a", "b"], transforms={"nope": "log1p"})


def test_transform_applies_before_flip():
    # log then negate must not error; negate then log would blow up on the
    # negatives. The pipeline transforms raw values first, so this succeeds and
    # the flipped variable's contribution still reverses the single-var order.
    df = _lognormal_frame()
    ascending = build_index(df, ["skewed"], transforms={"skewed": "log1p"}).scores
    descending = build_index(
        df, ["skewed"], flip=["skewed"], transforms={"skewed": "log1p"}
    ).scores
    assert np.allclose(ascending, 100 - descending)


def test_callable_transform_supported():
    # A caller-supplied callable is honored just like a named transform.
    df = _lognormal_frame()
    variables = ["skewed", "b", "c"]
    by_name = build_index(df, variables, transforms={"skewed": "log1p"}).scores
    by_callable = build_index(df, variables, transforms={"skewed": np.log1p}).scores
    assert np.allclose(by_name, by_callable)
