"""
SoC layer      : Training (ML)
Responsibility : Measure the candidates (confusion counts, precision, recall, F1, ROC-AUC, PR-AUC),
                 build the comparison table, pick the final model on validation (I09), run the ONE
                 final test evaluation, draw fig07, fig08 and fig10
Never does     : Train or tune a model; choose the decision threshold (n° 24); look at the test
                 part before the final model and its threshold are fixed (R103)
Reference      : Architecture_Projet.md v1.1 — section 7 (figure names), section 8 (n° 23);
                 J2 decision (PR-AUC and F1); Points_A_Trancher I09; Matrice_Conformite.md R103
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

import matplotlib

matplotlib.use("Agg")  # draw to files, never open a window
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from sklearn.metrics import (  # noqa: E402
    average_precision_score,
    confusion_matrix,
    f1_score,
    precision_recall_curve,
    precision_score,
    recall_score,
    roc_auc_score,
)

from src.models.train_classical import Candidate  # noqa: E402

if TYPE_CHECKING:
    from src.models.train_mlp import MLPHistory


def fraud_scores(candidate: Candidate, X: pd.DataFrame) -> np.ndarray:
    return candidate.pipeline.predict_proba(X)[:, 1]


def ranking_metrics(y_true: pd.Series, scores: np.ndarray) -> dict[str, float]:
    """Threshold-free: how well the scores rank frauds above normal rows."""
    return {
        "pr_auc": float(average_precision_score(y_true, scores)),   # chance level = fraud rate
        "roc_auc": float(roc_auc_score(y_true, scores)),            # chance level = 0.5
    }


def metrics_at_threshold(y_true: pd.Series, scores: np.ndarray, threshold: float) -> dict[str, Any]:
    """Decision metrics once a threshold is applied: counts first, then the rates built on them."""
    flagged = (scores >= threshold).astype(int)
    tn, fp, fn, tp = confusion_matrix(y_true, flagged, labels=[0, 1]).ravel()
    return {
        "threshold": float(threshold),
        "tp": int(tp), "fp": int(fp), "fn": int(fn), "tn": int(tn),
        "precision": float(precision_score(y_true, flagged, zero_division=0)),  # tp / (tp + fp)
        "recall": float(recall_score(y_true, flagged, zero_division=0)),        # tp / (tp + fn)
        "f1": float(f1_score(y_true, flagged, zero_division=0)),
    }


def best_f1_threshold(y_true: pd.Series, scores: np.ndarray) -> tuple[float, float]:
    """For the comparison table only (the real threshold comes from n° 24)."""
    precision, recall, thresholds = precision_recall_curve(y_true, scores)
    f1 = 2 * precision * recall / np.clip(precision + recall, 1e-12, None)
    best = int(np.argmax(f1[:-1]))
    return float(thresholds[best]), float(f1[best])


def compare_candidates(
    candidates: list[Candidate], X_val: pd.DataFrame, y_val: pd.Series
) -> pd.DataFrame:
    """One row per candidate, measured on validation, best PR-AUC first."""
    rows = []
    for candidate in candidates:
        scores = fraud_scores(candidate, X_val)
        threshold, f1 = best_f1_threshold(y_val, scores)
        rows.append({
            "model": candidate.name,
            "params": str(candidate.params),
            **ranking_metrics(y_val, scores),
            "best_f1": f1,
            "best_f1_threshold": threshold,
        })
    return pd.DataFrame(rows).sort_values("pr_auc", ascending=False, ignore_index=True)


def select_final(table: pd.DataFrame) -> str:
    """I09: the final model is the one with the best validation PR-AUC (J2 main metric)."""
    return str(table.iloc[0]["model"])


def evaluate_on_test(
    candidate: Candidate, X_test: pd.DataFrame, y_test: pd.Series, threshold: float
) -> dict[str, Any]:
    """The ONE look at the test part (R103): model and threshold were fixed on validation."""
    scores = fraud_scores(candidate, X_test)
    return {
        "model": candidate.name,
        "rows": int(len(y_test)),
        "frauds": int(np.sum(y_test)),
        **ranking_metrics(y_test, scores),
        **metrics_at_threshold(y_test, scores, threshold),
    }


# --- Figures (names from Architecture_Projet.md section 7) ------------------------
def plot_precision_recall(
    candidates: list[Candidate], X_val: pd.DataFrame, y_val: pd.Series, path: Path,
    final_name: str | None = None, threshold: float | None = None,
) -> None:
    """fig07: precision-recall curves on validation, with the chosen threshold marked."""
    fig, ax = plt.subplots(figsize=(7, 5))
    for candidate in candidates:
        scores = fraud_scores(candidate, X_val)
        precision, recall, _ = precision_recall_curve(y_val, scores)
        ax.plot(recall, precision,
                label=f"{candidate.name} (PR-AUC {average_precision_score(y_val, scores):.3f})")
        if candidate.name == final_name and threshold is not None:
            point = metrics_at_threshold(y_val, scores, threshold)
            ax.scatter(point["recall"], point["precision"], s=60, color="black", zorder=3,
                       label=f"threshold {threshold:.3f}")
    ax.set(xlabel="Recall", ylabel="Precision", title="Precision-recall on validation")
    ax.legend(fontsize=8)
    _save(fig, path)


def plot_confusion(counts: dict[str, Any], path: Path) -> None:
    """fig08: confusion matrix in counts (test part, final model, chosen threshold)."""
    matrix = np.array([[counts["tn"], counts["fp"]], [counts["fn"], counts["tp"]]])
    fig, ax = plt.subplots(figsize=(5, 4))
    ax.imshow(matrix, cmap="Blues")
    for (row, col), value in np.ndenumerate(matrix):
        ax.text(col, row, f"{value:,}", ha="center", va="center")
    ax.set(xticks=[0, 1], yticks=[0, 1], xticklabels=["not flagged", "flagged"],
           yticklabels=["not fraud", "fraud"],
           title=f"Confusion matrix (threshold {counts['threshold']:.3f})")
    _save(fig, path)


def plot_learning_curve(history: MLPHistory, path: Path) -> None:
    """fig10: MLP weighted train loss and validation PR-AUC per epoch; dashed = epoch kept."""
    epochs = range(1, len(history.train_loss) + 1)
    fig, loss_axis = plt.subplots(figsize=(7, 4))
    loss_axis.plot(epochs, history.train_loss, label="train loss")
    loss_axis.set(xlabel="Epoch", ylabel="Weighted train loss",
                  title="MLP learning curves (dashed: best epoch kept)")
    score_axis = loss_axis.twinx()
    score_axis.plot(epochs, history.val_pr_auc, color="tab:orange", label="validation PR-AUC")
    score_axis.set_ylabel("Validation PR-AUC")
    score_axis.axvline(history.best_epoch, linestyle="--", color="grey")
    _save(fig, path)


def _save(fig: plt.Figure, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(path, dpi=120)
    plt.close(fig)