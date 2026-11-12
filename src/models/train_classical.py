"""
SoC layer      : Training (ML)
Responsibility : Train the classical candidates (prior baseline, logistic regression, random forest)
                 on train, keep for each family the setting with the best PR-AUC on validation
Never does     : Touch the test part (R103); choose the decision threshold (n° 24);
                 save files (model_io.py, n° 20); pick the final model (n° 23)
Reference      : Architecture_Projet.md v1.1 — section 8 (n° 21); Points_A_Trancher I37, I05;
                 J2 decision (PR-AUC as main metric); Matrice_Conformite.md R097, R103
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline

from src.features.build_features import build_preprocessor

TRAIN_SAMPLE_ROWS = 1_000_000  # I37 / I05: stratified sample of train, keeps the 0.13 % fraud rate
GRID_KEYS = ("C", "max_depth")  # the settings we vary, reported with each candidate


@dataclass(frozen=True)
class Candidate:
    name: str
    pipeline: Pipeline         # fitted: preprocessing (n° 18) + model
    params: dict[str, Any]     # the grid values kept
    val_pr_auc: float          # PR-AUC on validation, used to choose the setting


def candidate_grids(seed: int) -> dict[str, list[Any]]:
    """Each family with its small grid (I37). class_weight balanced: one fraud weighs as much as
    the ~775 normal rows around it, otherwise the model learns to always say 'no fraud'."""
    return {
        "baseline_prior": [DummyClassifier(strategy="prior")],
        "logistic_regression": [
            LogisticRegression(C=c, class_weight="balanced", max_iter=1000, random_state=seed)
            for c in (0.1, 1.0)
        ],
        "random_forest": [
            RandomForestClassifier(
                n_estimators=200, max_depth=depth, min_samples_leaf=5,
                class_weight="balanced_subsample", n_jobs=-1, random_state=seed,
            )
            for depth in (12, 20)
        ],
    }


def sample_train(
    X: pd.DataFrame, y: pd.Series, n_rows: int, seed: int
) -> tuple[pd.DataFrame, pd.Series]:
    """Stratified sample of train (same fraud rate); the whole train part if already smaller."""
    if len(X) <= n_rows:
        return X, y
    X_sample, _, y_sample, _ = train_test_split(
        X, y, train_size=n_rows, stratify=y, random_state=seed
    )
    return X_sample, y_sample


def train_classical(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    X_val: pd.DataFrame,
    y_val: pd.Series,
    *,
    seed: int,
    train_rows: int = TRAIN_SAMPLE_ROWS,
) -> list[Candidate]:
    """Fit every setting on train, score it on validation, keep the best setting per family."""
    X_fit, y_fit = sample_train(X_train, y_train, train_rows, seed)
    candidates: list[Candidate] = []
    for name, grid in candidate_grids(seed).items():
        best: Candidate | None = None
        for estimator in grid:
            pipeline = Pipeline([("features", build_preprocessor()), ("model", estimator)])
            pipeline.fit(X_fit, y_fit)  # fit on train only (R097)
            score = float(average_precision_score(y_val, pipeline.predict_proba(X_val)[:, 1]))
            if best is None or score > best.val_pr_auc:
                params = {key: value for key, value in estimator.get_params().items()
                          if key in GRID_KEYS}
                best = Candidate(name, pipeline, params, score)
        candidates.append(best)
    return candidates