"""
The standard index pipeline from docs/plan.md section 2, implemented once for
SVI, SCAI, and GAI:

    raw -> align direction -> standardize -> PCA (PC1) -> sign check -> 0-100

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
"""

from dataclasses import dataclass
from typing import Sequence

import numpy as np
import pandas as pd


@dataclass
class IndexResult:
    scores: pd.Series                 # 0-100, aligned to the input df index
    loadings: pd.Series               # PC1 loading per (aligned) variable
    explained_variance_ratio: float   # fraction of total variance in PC1


def build_index(
    df: pd.DataFrame,
    variables: Sequence[str],
    *,
    flip: Sequence[str] = (),
    name: str = "index",
) -> IndexResult:
    variables = list(variables)
    if not variables:
        raise ValueError(f"{name}: no variables given")

    missing = [v for v in variables if v not in df.columns]
    if missing:
        raise ValueError(f"{name}: variables not in DataFrame: {missing}")

    bad_flip = [v for v in flip if v not in variables]
    if bad_flip:
        raise ValueError(f"{name}: flip entries not in variables: {bad_flip}")

    X = df[variables].astype(float).copy()

    with_nan = [v for v in variables if X[v].isna().any()]
    if with_nan:
        raise ValueError(
            f"{name}: NaN in {with_nan} — impute or drop in the notebook first"
        )

    if len(X) < 2:
        raise ValueError(f"{name}: need at least 2 rows, got {len(X)}")

    for v in flip:
        X[v] = -X[v]

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
    # means "more of what the index measures".
    anchor = Z.mean(axis=1).to_numpy()
    if np.corrcoef(pc1, anchor)[0, 1] < 0:
        pc1 = -pc1
        loadings = -loadings

    lo, hi = pc1.min(), pc1.max()
    scores = (pc1 - lo) / (hi - lo) * 100.0

    return IndexResult(
        scores=pd.Series(scores, index=df.index, name=name),
        loadings=pd.Series(loadings, index=variables, name=f"{name}_pc1_loading"),
        explained_variance_ratio=explained,
    )
