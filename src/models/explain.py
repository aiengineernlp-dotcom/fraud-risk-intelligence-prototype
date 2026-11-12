"""
SoC layer      : Training (ML)
Responsibility : Explain the final model: permutation importance on the raw input columns (D-11, I10),
                 error analysis of missed frauds and false alerts at the chosen threshold, fig09
Never does     : Use the test part (validation only); retrain; claim causality (importance says what the
                 model relies on, not why fraud happens)
Reference      : Architecture_Projet.md v1.1 — section 7 (fig09), section 8 (n° 26), D-11;
                 Points_A_Trancher I10; Matrice_Conformite.md R103
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.inspection import permutation_importance

from src.models.evaluate import _save, fraud_scores, plt
from src.models.train_classical import Candidate, sample_train

IMPORTANCE_ROWS = 100_000  # stratified validation rows used for permutation (time budget)
IMPORTANCE_REPEATS = 3


def permutation_table(
    candidate: Candidate, X_val: pd.DataFrame, y_val: pd.Series, *, seed: int,
    max_rows: int = IMPORTANCE_ROWS, n_repeats: int = IMPORTANCE_REPEATS,
) -> pd.DataFrame:
    """Drop in validation PR-AUC when one RAW column is shuffled (whole pipeline, so the
    derived variables built from that column are affected too)."""
    X, y = sample_train(X_val, y_val, max_rows, seed)  # same stratified sampler as training
    result = permutation_importance(
        candidate.pipeline, X, y, scoring="average_precision",
        n_repeats=n_repeats, random_state=seed,
    )
    return pd.DataFrame({
        "column": X.columns,
        "importance_mean": result.importances_mean,
        "importance_std": result.importances_std,
    }).sort_values("importance_mean", ascending=False, ignore_index=True)


def error_table(
    candidate: Candidate, X_val: pd.DataFrame, y_val: pd.Series, threshold: float
) -> pd.DataFrame:
    """Missed frauds, false alerts and caught frauds by transaction type, with median amount
    and score -> artifacts/metrics/error_analysis.csv (written by train.py)."""
    scores = fraud_scores(candidate, X_val)
    flagged = scores >= threshold
    fraud = y_val.to_numpy() == 1
    outcome = np.select(
        [flagged & fraud, flagged & ~fraud, ~flagged & fraud],
        ["caught_fraud", "false_alert", "missed_fraud"],
        default="normal_left_alone",
    )
    rows = X_val.assign(outcome=outcome, score=scores)
    rows = rows[rows["outcome"] != "normal_left_alone"]
    return (rows.groupby(["outcome", "type"])
                .agg(count=("amount", "size"), median_amount=("amount", "median"),
                     median_score=("score", "median"))
                .reset_index())


def plot_importance(table: pd.DataFrame, path: Path) -> None:
    """fig09: permutation importance (drop in validation PR-AUC), with its spread."""
    ordered = table.sort_values("importance_mean")
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.barh(ordered["column"], ordered["importance_mean"], xerr=ordered["importance_std"])
    ax.set(xlabel="Drop in validation PR-AUC when the column is shuffled",
           title="Permutation importance (final model)")
    _save(fig, path)