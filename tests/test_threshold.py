"""
SoC layer      : Tests
Responsibility : Prove that threshold.py takes the LOWEST threshold within the alert budget, never
                 exceeds the team's capacity, gives more alerts (and no less recall) when capacity
                 grows, and refuses impossible cases with a clear message
Never does     : Train a model or load PaySim (scores are built so the right answer is known)
Reference      : Architecture_Projet.md v1.1 — section 8 (n° 25); Points_A_Trancher I08;
                 Matrice_Conformite.md R146, R148–R151
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.models.threshold import alert_share, choose_threshold, daily_volume, threshold_table

N_ROWS = 1000
PER_DAY = 8  # with capacity 1 -> share 1/8 = 0.125 exactly -> budget 125 alerts on 1000 rows


def _scores() -> tuple[pd.Series, np.ndarray]:
    """1000 distinct scores from 0 to 0.999; the 50 highest are frauds."""
    scores = np.linspace(0, 1, N_ROWS, endpoint=False)
    return pd.Series((scores >= 0.95).astype(int)), scores


def test_lowest_threshold_within_budget_is_chosen() -> None:
    y, scores = _scores()
    choice = choose_threshold(y, scores, capacity_per_day=1, transactions_per_day=PER_DAY)
    expected = np.sort(scores)[::-1][124]  # the 125th highest score
    assert choice.threshold == pytest.approx(expected)
    assert choice.validation["tp"] + choice.validation["fp"] == 125


@pytest.mark.parametrize("capacity, budget", [(1, 125), (2, 250), (3, 375)])
def test_alerts_never_exceed_capacity(capacity: int, budget: int) -> None:
    y, scores = _scores()
    counts = choose_threshold(y, scores, capacity_per_day=capacity,
                              transactions_per_day=PER_DAY).validation
    assert counts["tp"] + counts["fp"] <= budget


def test_more_capacity_more_alerts_and_no_less_recall() -> None:
    y, scores = _scores()
    table = threshold_table(y, scores, transactions_per_day=PER_DAY, capacities=(1, 2, 3))
    assert table["alerts"].is_monotonic_increasing
    assert table["recall"].is_monotonic_increasing
    assert table["threshold"].is_monotonic_decreasing


def test_ties_above_budget_are_refused() -> None:
    y, _ = _scores()
    tied = np.full(N_ROWS, 0.9)  # every row has the same score: no threshold fits the budget
    with pytest.raises(ValueError, match="highest score"):
        choose_threshold(y, tied, capacity_per_day=1, transactions_per_day=PER_DAY)


def test_capacity_too_small_is_refused() -> None:
    y, scores = _scores()
    with pytest.raises(ValueError, match="not one alert"):
        choose_threshold(y, scores, capacity_per_day=1, transactions_per_day=1e9)


def test_alert_share_is_capped_and_checked() -> None:
    assert alert_share(5, 2) == 1.0  # capacity above the volume: everything can be reviewed
    with pytest.raises(ValueError):
        alert_share(0, 10)


def test_daily_volume_counts_transactions_per_day() -> None:
    frame = pd.DataFrame({"step": np.repeat(np.arange(1, 49), 10)})  # 48 hours x 10 rows
    assert daily_volume(frame) == pytest.approx(240.0)  # 480 rows over 2 days