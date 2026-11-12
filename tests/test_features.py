"""
SoC layer      : Tests
Responsibility : Prove that build_features.py keeps the target, the simulator flag and the
                 identifiers out of the model (two barriers), derives the right values, learns only
                 from the data given to fit, and survives an unknown transaction type
Never does     : Load the real PaySim CSV (a small synthetic raw frame is enough)
Reference      : Architecture_Projet.md v1.1 — section 8 (n° 19); Points_A_Trancher_INTERNE I36;
                 Matrice_Conformite.md R053, R054, R097
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.data.schema import TARGET_COLUMN, TRANSACTION_TYPES
from src.features.build_features import (
    EXCLUDED_COLUMNS,
    MODEL_INPUT_COLUMNS,
    add_derived_features,
    build_preprocessor,
    signed_log1p,
    split_xy,
)


def _raw(n_rows: int = 200, seed: int = 0) -> pd.DataFrame:
    """Synthetic frame with the 11 PaySim columns (same names and kinds as the real CSV)."""
    rng = np.random.default_rng(seed)
    amount = rng.uniform(1, 50_000, n_rows)
    old_orig = rng.uniform(0, 100_000, n_rows)
    return pd.DataFrame({
        "step": rng.integers(1, 744, n_rows),
        "type": rng.choice(sorted(TRANSACTION_TYPES), n_rows),
        "amount": amount,
        "nameOrig": [f"C{i}" for i in range(n_rows)],
        "oldbalanceOrg": old_orig,
        "newbalanceOrig": np.maximum(old_orig - amount, 0),
        "nameDest": [f"M{i}" for i in range(n_rows)],
        "oldbalanceDest": rng.uniform(0, 100_000, n_rows),
        "newbalanceDest": rng.uniform(0, 100_000, n_rows),
        TARGET_COLUMN: rng.integers(0, 2, n_rows),
        "isFlaggedFraud": 0,
    })


# --- Barrier 1: split_xy --------------------------------------------------------
def test_excluded_columns_come_from_schema_roles() -> None:
    assert set(EXCLUDED_COLUMNS) == {"nameOrig", "nameDest", TARGET_COLUMN, "isFlaggedFraud"}


def test_target_flag_and_ids_never_in_x() -> None:
    frame = _raw()
    X, y = split_xy(frame)
    assert not set(EXCLUDED_COLUMNS) & set(X.columns)
    assert y.equals(frame[TARGET_COLUMN].astype("int64"))


# --- Barrier 2: only MODEL_INPUT_COLUMNS reach the model ------------------------
def test_model_inputs_never_include_excluded_columns() -> None:
    assert not set(EXCLUDED_COLUMNS) & set(MODEL_INPUT_COLUMNS)
    frame = _raw()  # even if the excluded columns were handed over, they are dropped
    assert list(add_derived_features(frame).columns) == list(MODEL_INPUT_COLUMNS)


# --- Derived values -------------------------------------------------------------
def test_derived_values_on_a_known_row() -> None:
    row = _raw(n_rows=1)
    row["step"] = 25
    row["type"] = "TRANSFER"
    row["amount"] = 400.0
    row["oldbalanceOrg"], row["newbalanceOrig"] = 1_000.0, 600.0
    row["oldbalanceDest"], row["newbalanceDest"] = 50.0, 450.0
    derived = add_derived_features(row).iloc[0]
    assert derived["error_balance_orig"] == 0.0  # 1000 - 600 - 400
    assert derived["error_balance_dest"] == 0.0  # 50 - 450 + 400
    assert derived["hour_of_day"] == 1           # 25 % 24
    assert derived["is_risky_type"] == 1         # TRANSFER


# --- Learns only during fit (R097) ---------------------------------------------
def test_preprocessor_learns_only_from_fit_data() -> None:
    fit_frame, other = _raw(seed=0), _raw(seed=1)
    other["amount"] = other["amount"] * 1_000  # very different amounts
    pre = build_preprocessor().fit(split_xy(fit_frame)[0])
    scaler = pre.named_steps["encode"].named_transformers_["money"].named_steps["scale"]
    learned = scaler.mean_.copy()
    pre.transform(split_xy(other)[0])  # transform must not change what was learned
    assert np.array_equal(learned, scaler.mean_)
    assert learned[0] == pytest.approx(signed_log1p(fit_frame["amount"].to_numpy()).mean())


# --- Output shape and robustness -----------------------------------------------
def test_output_has_12_columns_and_no_missing_value() -> None:
    X = split_xy(_raw())[0]
    Z = build_preprocessor().fit_transform(X)
    assert Z.shape == (len(X), 12)
    assert not np.isnan(Z).any()


def test_unknown_type_does_not_crash() -> None:
    pre = build_preprocessor().fit(split_xy(_raw())[0])
    strange = _raw(n_rows=3)
    strange["type"] = "CRYPTO"  # not a PaySim type: one-hot gives all zeros, no error
    Z = pre.transform(split_xy(strange)[0])
    assert Z.shape == (3, 12)