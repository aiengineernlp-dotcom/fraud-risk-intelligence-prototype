"""
SoC layer      : Training (ML)
Responsibility : Split the validated PaySim frame into train / validation / test sets with a fixed
                 seed, stratified on the target; optional time-based split on `step` (R104)
Never does     : Read or write a file; clean, change or resample rows; fit a transformer or a model;
                 compute anything on the test rows (it only sets them aside, R103)
Reference      : Architecture_Projet.md v1.1 — section 8 (n° 16); brief §6.3;
                 Matrice_Conformite.md R102–R104; Points_A_Trancher_INTERNE I34 (revised 2026-11-11:
                 seed and shares come from configs/settings.yaml, passed by train.py)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd
from sklearn.model_selection import train_test_split

from src.data.schema import TARGET_COLUMN

# Seed and shares are NOT set here: they live in configs/settings.yaml (`split`, I34), are checked
# by config.py and passed by train.py (n° 27). No default values -> no second source of truth.

TIME_COLUMN = "step"  # 1 step = 1 simulated hour

STRATIFIED = "stratified"
TEMPORAL = "temporal"


class SplitError(ValueError):
    """Raised when the frame or the settings make a usable split impossible."""


@dataclass(frozen=True)
class DataSplit:
    """The three parts. Each keeps the original row index, so rows can be traced back
    (overlap test in n° 17, demo cases taken from the test part in n° 37)."""

    train: pd.DataFrame
    validation: pd.DataFrame
    test: pd.DataFrame
    strategy: str
    seed: int | None  # None for the time-based split: nothing random in it
    val_size: float
    test_size: float

    def summary(self) -> dict[str, Any]:
        """Settings, rows and fraud rate per part: what the README, the report and the
        model metadata quote (R102)."""
        parts = {"train": self.train, "validation": self.validation, "test": self.test}
        return {
            "strategy": self.strategy,
            "seed": self.seed,
            "val_size": self.val_size,
            "test_size": self.test_size,
            "rows": {name: len(part) for name, part in parts.items()},
            "fraud_rate": {
                name: round(float(part[TARGET_COLUMN].mean()), 6) for name, part in parts.items()
            },
        }


def stratified_split(
    frame: pd.DataFrame, *, val_size: float, test_size: float, seed: int
) -> DataSplit:
    """Random split that keeps the fraud rate (~0.13 %) the same in all three parts.

    Two cuts with the same seed: the test part first, out of all rows; then the validation
    part, out of what remains. Same frame + same seed -> exactly the same rows in each part.
    """
    _check_settings(val_size, test_size)
    _check_target(frame)

    rest, test = train_test_split(
        frame, test_size=test_size, stratify=frame[TARGET_COLUMN], random_state=seed
    )
    # val_size is a share of ALL rows; the second cut only sees `rest`, so rescale it.
    val_share_of_rest = val_size / (1.0 - test_size)
    train, validation = train_test_split(
        rest, test_size=val_share_of_rest, stratify=rest[TARGET_COLUMN], random_state=seed
    )

    split = DataSplit(train, validation, test, STRATIFIED, seed, val_size, test_size)
    _check_parts(split)
    return split


def temporal_split(frame: pd.DataFrame, *, val_size: float, test_size: float) -> DataSplit:

    """Time-based split for the extra experiment (R104): earliest steps -> train,
    middle steps -> validation, latest steps -> test.

    All rows of one step stay in the same part (no hour is cut in two), so the shares are
    close to the requested ones, not exact. The fraud rate is NOT forced: it may drift
    between parts, and that drift is part of what the experiment shows.
    """
    _check_settings(val_size, test_size)
    _check_target(frame)
    if TIME_COLUMN not in frame.columns:
        raise SplitError(f"Time-based split needs the '{TIME_COLUMN}' column")

    rows_per_step = frame[TIME_COLUMN].value_counts().sort_index()
    # Share of all rows that come strictly BEFORE each step.
    share_before = (rows_per_step.cumsum() - rows_per_step) / len(frame)
    train_end = 1.0 - val_size - test_size
    validation_end = 1.0 - test_size
    part_of_step = share_before.map(
        lambda share: "train"
        if share < train_end
        else ("validation" if share < validation_end else "test")
    )
    part = frame[TIME_COLUMN].map(part_of_step)

    split = DataSplit(
        frame[part == "train"],
        frame[part == "validation"],
        frame[part == "test"],
        TEMPORAL,
        None,
        val_size,
        test_size,
    )
    _check_parts(split)
    return split


def _check_settings(val_size: float, test_size: float) -> None:
    if not (0.0 < val_size < 1.0 and 0.0 < test_size < 1.0 and val_size + test_size < 1.0):
        raise SplitError(
            f"Invalid shares: val_size={val_size}, test_size={test_size} "
            "(each must be between 0 and 1, and together leave rows for train)"
        )


def _check_target(frame: pd.DataFrame) -> None:
    if TARGET_COLUMN not in frame.columns:
        raise SplitError(f"Target column '{TARGET_COLUMN}' is missing")
    if set(frame[TARGET_COLUMN].unique()) != {0, 1}:
        raise SplitError(f"'{TARGET_COLUMN}' must contain both classes (0 and 1) to split")


def _check_parts(split: DataSplit) -> None:
    """Every part must be non-empty and hold at least one fraud: without fraud in the
    validation part, no threshold can be chosen; without fraud in the test part, recall
    cannot be measured."""
    for name, part in (("train", split.train), ("validation", split.validation),
                       ("test", split.test)):
        if part.empty:
            raise SplitError(f"The {name} part is empty")
        if int(part[TARGET_COLUMN].sum()) == 0:
            raise SplitError(f"The {name} part contains no fraud")