"""
SoC layer      : Tests
Responsibility : Prove that split.py cuts reproducibly, keeps the fraud rate and the shares, loses or
                 duplicates no row, keeps time order, and refuses unusable settings or parts
Never does     : Load the real PaySim CSV (a small synthetic frame is enough and runs in milliseconds)
Reference      : Architecture_Projet.md v1.1 — section 8 (n° 17); Features B02, B08;
                 Matrice_Conformite.md R102–R104; Points_A_Trancher_INTERNE I34
"""

from __future__ import annotations

import pandas as pd
import pytest

from src.data.schema import TARGET_COLUMN
from src.data.split import DataSplit, SplitError, stratified_split, temporal_split

SHARES = {"val_size": 0.15, "test_size": 0.15}
SEED = 42


def _frame(n_rows: int = 2000, n_frauds: int = 100, fraud_steps: range | None = None) -> pd.DataFrame:
    """Synthetic frame: `step` from 1 to 100 (20 rows per hour); frauds spread evenly over
    all hours, or only inside `fraud_steps`."""
    steps = [1 + i * 100 // n_rows for i in range(n_rows)]
    frame = pd.DataFrame({"step": steps, "amount": range(n_rows), TARGET_COLUMN: 0})
    candidates = frame.index if fraud_steps is None else frame.index[frame["step"].isin(fraud_steps)]
    chosen = candidates[:: max(1, len(candidates) // n_frauds)][:n_frauds]
    frame.loc[chosen, TARGET_COLUMN] = 1
    return frame


def _indexes(split: DataSplit) -> list[pd.Index]:
    return [split.train.index, split.validation.index, split.test.index]


# --- Reproducibility (B02) ----------------------------------------------------
def test_same_seed_gives_same_rows() -> None:
    first = stratified_split(_frame(), seed=SEED, **SHARES)
    second = stratified_split(_frame(), seed=SEED, **SHARES)
    for part_first, part_second in zip(_indexes(first), _indexes(second)):
        assert part_first.equals(part_second)


def test_other_seed_gives_other_test_rows() -> None:
    first = stratified_split(_frame(), seed=SEED, **SHARES)
    other = stratified_split(_frame(), seed=SEED + 1, **SHARES)
    assert not first.test.index.equals(other.test.index)


# --- No row lost, none in two parts --------------------------------------------
def test_no_row_lost_or_duplicated() -> None:
    frame = _frame()
    train, validation, test = (set(index) for index in _indexes(
        stratified_split(frame, seed=SEED, **SHARES)))
    assert not (train & validation) and not (train & test) and not (validation & test)
    assert train | validation | test == set(frame.index)


# --- Shares and fraud rate kept -------------------------------------------------
def test_shares_and_fraud_rate_are_kept() -> None:
    frame = _frame()
    summary = stratified_split(frame, seed=SEED, **SHARES).summary()
    assert summary["rows"]["test"] == pytest.approx(0.15 * len(frame), abs=1)
    assert summary["rows"]["validation"] == pytest.approx(0.15 * len(frame), abs=1)
    overall_rate = frame[TARGET_COLUMN].mean()
    for rate in summary["fraud_rate"].values():
        assert rate == pytest.approx(overall_rate, abs=0.005)


# --- Time-based split (B08, R104) ----------------------------------------------
def test_temporal_split_keeps_time_order() -> None:
    split = temporal_split(_frame(), **SHARES)
    train_steps, validation_steps, test_steps = (
        set(part["step"]) for part in (split.train, split.validation, split.test))
    assert max(train_steps) < min(validation_steps)
    assert max(validation_steps) < min(test_steps)
    assert split.seed is None


# --- Unusable settings or parts are refused ------------------------------------
@pytest.mark.parametrize("val_size, test_size", [(0.5, 0.5), (0.0, 0.15), (0.15, 1.2)])
def test_unusable_shares_are_refused(val_size: float, test_size: float) -> None:
    with pytest.raises(SplitError, match="Invalid shares"):
        stratified_split(_frame(), val_size=val_size, test_size=test_size, seed=SEED)


def test_frame_without_fraud_is_refused() -> None:
    frame = _frame()
    frame[TARGET_COLUMN] = 0
    with pytest.raises(SplitError, match="both classes"):
        stratified_split(frame, seed=SEED, **SHARES)


def test_validation_without_fraud_is_refused() -> None:
    frame = _frame(fraud_steps=range(1, 21))  # frauds only in the first 20 hours
    with pytest.raises(SplitError, match="validation part contains no fraud"):
        temporal_split(frame, **SHARES)