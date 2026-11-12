"""
SoC layer      : Training (ML)
Responsibility : Choose the decision threshold on validation from the operational objective (I08):
                 the lowest threshold whose alert volume fits the team's daily review capacity, i.e. the
                 most frauds caught without overloading the team; build the candidate-threshold table
Never does     : Look at the test part (R149); train or pick a model; hold a capacity value (it comes
                 from configs/settings.yaml through config.py)
Reference      : Architecture_Projet.md v1.1 — section 8 (n° 24), D-12; Points_A_Trancher I08;
                 Matrice_Conformite.md R146, R148–R151
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd

from src.models.evaluate import metrics_at_threshold

HOURS_PER_DAY = 24


@dataclass(frozen=True)
class ThresholdChoice:
    threshold: float
    capacity_per_day: int
    alert_share: float              # share of all transactions the team can review
    validation: dict[str, Any]      # counts and rates on validation at this threshold


def daily_volume(frame: pd.DataFrame) -> float:
    """Transactions per day in the data (PaySim: 744 hourly steps -> 31 days)."""
    return len(frame) * HOURS_PER_DAY / frame["step"].nunique()


def alert_share(capacity_per_day: int, transactions_per_day: float) -> float:
    if capacity_per_day < 1 or transactions_per_day <= 0:
        raise ValueError("capacity must be >= 1 and the daily volume > 0")
    return min(1.0, capacity_per_day / transactions_per_day)


def choose_threshold(
    y_val: pd.Series, scores: np.ndarray, *, capacity_per_day: int, transactions_per_day: float
) -> ThresholdChoice:
    """Turn the capacity into an alert budget on validation, then take the LOWEST threshold whose
    number of alerts stays within that budget (lower threshold = more frauds caught)."""
    share = alert_share(capacity_per_day, transactions_per_day)
    budget = int(np.floor(share * len(scores)))
    if budget < 1:
        raise ValueError("Capacity too small for this validation set: not one alert allowed")
    values = np.unique(scores)  # ascending candidate thresholds
    alerts_at = len(scores) - np.searchsorted(np.sort(scores), values, side="left")  # scores >= value
    within_budget = values[alerts_at <= budget]
    if within_budget.size == 0:
        raise ValueError("Even the highest score gives more alerts than the budget (ties)")
    threshold = float(within_budget.min())
    return ThresholdChoice(
        threshold, capacity_per_day, share, metrics_at_threshold(y_val, scores, threshold)
    )


def threshold_table(
    y_val: pd.Series,
    scores: np.ndarray,
    *,
    transactions_per_day: float,
    capacities: tuple[int, ...] = (100, 200, 300, 500, 1000),
) -> pd.DataFrame:
    """The precision-recall trade-off across candidate capacities (R150) ->
    artifacts/metrics/threshold_analysis.csv (written by train.py)."""
    rows = []
    for capacity in capacities:
        choice = choose_threshold(y_val, scores, capacity_per_day=capacity,
                                  transactions_per_day=transactions_per_day)
        counts = choice.validation
        rows.append({"capacity_per_day": capacity, "alert_share": choice.alert_share,
                     "alerts": counts["tp"] + counts["fp"], **counts})
    return pd.DataFrame(rows)