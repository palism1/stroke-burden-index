"""
The standard index pipeline from docs/plan.md section 2, implemented once for
SVI, SCAI, and GAI:

    raw -> [optional transform] -> align direction -> standardize -> PCA (PC1)
        -> sign check -> 0-100

Usage from a notebook (SVI example):

    import sys; sys.path.insert(0, "src")   # adjust to your notebook's location
    from index_pipeline import build_index

    result = build_index(
        df,
        ["pcnt_65_plus", "poverty_rate", "smoking_prevalence", "obesity_prevalence",
         "pcnt_bachelors", "pcnt_insured"],
        flip=["pcnt_bachelors", "pcnt_insured"],   # protective vars point the other way
    )
    df["svi"] = result.scores                  # 0 = lowest, 100 = highest
    result.loadings                            # PC1 loadings per variable
    result.explained_variance_ratio           # fraction of variance PC1 captures

Orientation is the caller's contract: put every variable whose *high* raw value
points against the index direction in `flip`. For SVI (higher = worse), flip
protective variables like income and education. For GAI (higher = better
access), flip all four drive-time/distance variables, since lower = closer.

The PC1 sign is chosen automatically so the index agrees with the majority
direction of the aligned variables — no manual "flip the index if it came out
backwards" step. Loadings are reported against the aligned (post-flip)
variables.

NaNs raise on purpose: imputation is an analytical decision that belongs in
the notebook, never silently inside the pipeline.

Skew & transforms
-----------------
PCA is sensitive to extreme outliers and heavy skew: a single fat tail can
dominate PC1. Every call therefore reports per-variable skewness of the values
as they enter standardization (`result.skewness`) and flags the heavily skewed
ones that got no transform (`result.high_skew`, |skew| > HIGH_SKEW_THRESHOLD).
These diagnostics never change the scores.

Fixing skew is opt-in and explicit — nothing auto-transforms. Pass
`transforms={var: "log1p"}` (or "log") to reshape a variable's RAW values
*before* direction alignment and standardizing (a log of a negated variable is
nonsense, so order matters). "log" refuses values <= 0; "log1p" refuses values
< 0. Which variables to reshape is the analyst's call; the diagnostics exist so
that call is informed.
"""

from dataclasses import dataclass, field
from typing import Callable, Dict, Mapping, Sequence, Union

import numpy as np
import pandas as pd

# |skewness| above this is "heavily skewed" per the team's PCA rule: such a
# variable's tail can dominate PC1, so it is a candidate for a log transform.
HIGH_SKEW_THRESHOLD = 2.0

# Named transforms usable in the `transforms` argument. Each takes/returns a
# pandas Series; callers may also pass their own callable.
TransformSpec = Union[str, Callable[[pd.Series], pd.Series]]


def _apply_log(name: str, var: str, s: pd.Series) -> pd.Series:
    if (s <= 0).any():
        raise ValueError(
            f"{name}: 'log' transform on {var!r} needs all values > 0, "
            "but some are <= 0 — use 'log1p' or shift the variable first"
        )
    return np.log(s)


def _apply_log1p(name: str, var: str, s: pd.Series) -> pd.Series:
    if (s < 0).any():
        raise ValueError(
            f"{name}: 'log1p' transform on {var!r} needs all values >= 0, "
            "but some are < 0 — shift the variable so its minimum is >= 0 first"
        )
    return np.log1p(s)


_NAMED_TRANSFORMS = {"log": _apply_log, "log1p": _apply_log1p}


def _resolve_transform(name: str, var: str, spec: TransformSpec, s: pd.Series) -> pd.Series:
    if callable(spec):
        return pd.Series(np.asarray(spec(s), dtype=float), index=s.index)
    if spec in _NAMED_TRANSFORMS:
        return _NAMED_TRANSFORMS[spec](name, var, s)
    valid = ", ".join(sorted(_NAMED_TRANSFORMS)) + ", or a callable"
    raise ValueError(
        f"{name}: unknown transform {spec!r} for {var!r}; valid options: {valid}"
    )


@dataclass
class IndexResult:
    scores: pd.Series                 # 0-100, aligned to the input df index
    loadings: pd.Series               # PC1 loading per (aligned) variable
    explained_variance_ratio: float   # fraction of total variance in PC1
    skewness: Dict[str, float] = field(default_factory=dict)  # per-var skew entering standardization
    high_skew: list = field(default_factory=list)  # untransformed vars with |skew| > HIGH_SKEW_THRESHOLD


def build_index(
    df: pd.DataFrame,
    variables: Sequence[str],
    *,
    flip: Sequence[str] = (),
    transforms: Mapping[str, TransformSpec] | None = None,
    name: str = "index",
) -> IndexResult:
    variables = list(variables)
    if not variables:
        raise ValueError(f"{name}: no variables given")

    dupes = sorted({v for v in variables if variables.count(v) > 1})
    if dupes:
        raise ValueError(f"{name}: duplicate variables: {dupes}")

    missing = [v for v in variables if v not in df.columns]
    if missing:
        raise ValueError(f"{name}: variables not in DataFrame: {missing}")

    bad_flip = [v for v in flip if v not in variables]
    if bad_flip:
        raise ValueError(f"{name}: flip entries not in variables: {bad_flip}")

    transforms = dict(transforms or {})
    bad_transform = [v for v in transforms if v not in variables]
    if bad_transform:
        raise ValueError(
            f"{name}: transform entries not in variables: {sorted(bad_transform)}"
        )

    X = df[variables].astype(float).copy()

    with_nan = [v for v in variables if X[v].isna().any()]
    if with_nan:
        raise ValueError(
            f"{name}: NaN in {with_nan} — impute or drop in the notebook first"
        )

    if len(X) < 2:
        raise ValueError(f"{name}: need at least 2 rows, got {len(X)}")

    # Transforms reshape the RAW values first — before direction alignment and
    # standardizing — because a log of a negated variable is meaningless.
    for v in variables:
        if v in transforms:
            X[v] = _resolve_transform(name, v, transforms[v], X[v])

    for v in flip:
        X[v] = -X[v]

    # Skewness of the (optionally transformed, then aligned) values as they
    # enter standardization. Diagnostic only — computed here so it reflects
    # exactly what PCA sees, but it never feeds back into the scores. Flip is a
    # pure sign change, so |skew| of the aligned values equals |skew| of the
    # transformed raw values; reporting the aligned skew keeps it consistent
    # with the matrix PCA actually runs on.
    skew = X.skew()  # adjusted Fisher-Pearson (pandas default), bias-corrected
    skewness = {v: float(skew[v]) for v in variables}
    high_skew = [
        v for v in variables
        if v not in transforms and abs(skewness[v]) > HIGH_SKEW_THRESHOLD
    ]

    std = X.std(ddof=0)
    constant = list(std.index[std == 0])
    if constant:
        raise ValueError(f"{name}: zero-variance variables cannot be standardized: {constant}")
    Z = (X - X.mean()) / std

    # PC1 via SVD on the standardized matrix (no dependency beyond numpy)
    _, s, vt = np.linalg.svd(Z.to_numpy(), full_matrices=False)
    loadings = vt[0]
    pc1 = Z.to_numpy() @ loadings
    explained = float(s[0] ** 2 / np.sum(s**2))

    # Sign check: PC1's sign is mathematically arbitrary. Anchor it to the
    # majority direction of the aligned variables so higher score always
    # means "more of what the index measures". If the aligned variables
    # cancel each other out, the anchor is meaningless and choosing a
    # direction would be a coin flip — refuse instead of ranking blind.
    anchor = Z.mean(axis=1).to_numpy()
    if anchor.std() < 1e-12:
        raise ValueError(
            f"{name}: aligned variables cancel out, so the index direction is "
            "undefined — some variables point opposite ways; review the flip list"
        )
    r = np.corrcoef(pc1, anchor)[0, 1]
    if abs(r) < 0.1:
        raise ValueError(
            f"{name}: PC1 is uncorrelated with the aligned variables "
            f"(r={r:.3f}), so the index direction is ambiguous — the variables "
            "likely disagree with each other; review the flip list and variable set"
        )
    if r < 0:
        pc1 = -pc1
        loadings = -loadings

    lo, hi = pc1.min(), pc1.max()
    scores = (pc1 - lo) / (hi - lo) * 100.0

    return IndexResult(
        scores=pd.Series(scores, index=df.index, name=name),
        loadings=pd.Series(loadings, index=variables, name=f"{name}_pc1_loading"),
        explained_variance_ratio=explained,
        skewness=skewness,
        high_skew=high_skew,
    )
