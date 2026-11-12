"""
SoC layer      : Training (ML) / Transverse (reloaded by joblib with the saved pipeline, D-13)
Responsibility : Separate inputs from the target, derive the model variables, and build the
                 preprocessing step that turns them into numbers (12 columns)
Never does     : Fit anything itself (the caller fits on train only, R097); read a file;
                 use the target, the simulator flag or the identifiers as inputs (R053, R054)
Reference      : Architecture_Projet.md v1.1 — section 8 (n° 18), D-13; Points_A_Trancher_INTERNE I36;
                 Donnees_et_Modeles.md §4; Matrice_Conformite.md R053, R054, R097
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import FunctionTransformer, OneHotEncoder, StandardScaler

from src.data.schema import COLUMNS, FEATURE, TARGET_COLUMN, TRANSACTION_TYPES

# --- What never enters X: every column whose schema role is not FEATURE -------
# (target isFraud, rule flag isFlaggedFraud, identifiers nameOrig / nameDest)
EXCLUDED_COLUMNS: tuple[str, ...] = tuple(spec.name for spec in COLUMNS if spec.role != FEATURE)

# --- Model variables (I36) -------------------------------------------------------
RISKY_TYPES = ("TRANSFER", "CASH_OUT")  # the only types where fraud occurs (J2 decision)
HOURS_PER_DAY = 24
MONEY_FEATURES = (
    "amount", "oldbalanceOrg", "oldbalanceDest", "error_balance_orig", "error_balance_dest",
)
TIME_FEATURES = ("hour_of_day",)        # replaces raw `step` (raw step learns the period)
CATEGORICAL_FEATURES = ("type",)
FLAG_FEATURES = ("is_risky_type",)
MODEL_INPUT_COLUMNS = MONEY_FEATURES + TIME_FEATURES + CATEGORICAL_FEATURES + FLAG_FEATURES
# Dropped after the VIF analysis (I36): exact linear combinations of the kept columns.
DROPPED_AFTER_VIF = ("newbalanceOrig", "newbalanceDest")


def split_xy(frame: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    """X = every column except the excluded ones; y = the target as 0/1 integers."""
    return frame.drop(columns=list(EXCLUDED_COLUMNS)), frame[TARGET_COLUMN].astype("int64")


def add_derived_features(frame: pd.DataFrame) -> pd.DataFrame:
    """Row by row only (nothing learned, so no leakage): returns a NEW frame holding exactly
    the model input columns, in a fixed order."""
    out = pd.DataFrame(index=frame.index)
    out["amount"] = frame["amount"]
    out["oldbalanceOrg"] = frame["oldbalanceOrg"]
    out["oldbalanceDest"] = frame["oldbalanceDest"]
    # The sender's balance should drop by exactly `amount`; the receiver's should rise by it.
    out["error_balance_orig"] = frame["oldbalanceOrg"] - frame["newbalanceOrig"] - frame["amount"]
    out["error_balance_dest"] = frame["oldbalanceDest"] - frame["newbalanceDest"] + frame["amount"]
    out["hour_of_day"] = frame["step"] % HOURS_PER_DAY
    out["type"] = frame["type"]
    out["is_risky_type"] = frame["type"].isin(RISKY_TYPES).astype("int64")
    return out[list(MODEL_INPUT_COLUMNS)]


def signed_log1p(values: np.ndarray) -> np.ndarray:
    """log(1 + |x|) keeping the sign: tames huge amounts and accepts the negative balance errors."""
    return np.sign(values) * np.log1p(np.abs(values))


def build_preprocessor() -> Pipeline:
    """Unfitted recipe: raw columns in, 12 numeric columns out. The CALLER fits it on train only.
    Module-level functions only (no lambda), so joblib can save and reload it (D-13)."""
    money = Pipeline([
        ("signed_log", FunctionTransformer(signed_log1p, feature_names_out="one-to-one")),
        ("scale", StandardScaler()),
    ])
    encode = ColumnTransformer(
        [
            ("money", money, list(MONEY_FEATURES)),
            ("time", StandardScaler(), list(TIME_FEATURES)),
            ("type", OneHotEncoder(categories=[sorted(TRANSACTION_TYPES)],
                                   handle_unknown="ignore", sparse_output=False),
             list(CATEGORICAL_FEATURES)),
            ("flags", "passthrough", list(FLAG_FEATURES)),
        ],
        remainder="drop",
        verbose_feature_names_out=False,
    )
    return Pipeline([
        ("derive", FunctionTransformer(add_derived_features, feature_names_out=_derived_names)),
        ("encode", encode),
    ])


def _derived_names(transformer: FunctionTransformer, input_features: object) -> list[str]:
    """Column names after `add_derived_features` (lets get_feature_names_out work end to end)."""
    return list(MODEL_INPUT_COLUMNS)