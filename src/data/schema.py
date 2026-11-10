"""
SoC layer      : Training (ML) / Transverse
Responsibility : Describe the PaySim data contract (required columns, type, valid values and role of
                 each column) and check a DataFrame against it
Never does     : Read or write a file; fix, clean or drop data; decide which columns enter the model
                 (build_features.py applies the roles, n° 18)
Reference      : Architecture_Projet.md v1.1 — section 8 (n° 09); brief §4.1, §4.2;
                 Matrice_Conformite.md R051–R053, R080
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd
from pandas.api import types as ptypes

# --- Roles (data dictionary, brief §4.4 / R055) -------------------------------
FEATURE = "feature"
IDENTIFIER = "identifier"
TARGET = "target"
RULE_FLAG = "rule_flag"  # simulator rule output: never a predictor in the main model (brief §4.2, R053)

TARGET_COLUMN = "isFraud"

TRANSACTION_TYPES = frozenset({"CASH_IN", "CASH_OUT", "DEBIT", "PAYMENT", "TRANSFER"})
BINARY_VALUES = frozenset({0, 1})


@dataclass(frozen=True)
class ColumnSpec:
    """What one column must look like. `allowed` = the only accepted values (None: any value)."""

    name: str
    kind: str  # "integer", "number" or "text"
    role: str
    allowed: frozenset | None = None
    non_negative: bool = False


# Order = order of the PaySim CSV header (checked on the downloaded copy, 2026-11-06).
COLUMNS: tuple[ColumnSpec, ...] = (
    ColumnSpec("step", "integer", FEATURE, non_negative=True),
    ColumnSpec("type", "text", FEATURE, allowed=TRANSACTION_TYPES),
    ColumnSpec("amount", "number", FEATURE, non_negative=True),
    ColumnSpec("nameOrig", "text", IDENTIFIER),
    ColumnSpec("oldbalanceOrg", "number", FEATURE, non_negative=True),
    ColumnSpec("newbalanceOrig", "number", FEATURE, non_negative=True),
    ColumnSpec("nameDest", "text", IDENTIFIER),
    ColumnSpec("oldbalanceDest", "number", FEATURE, non_negative=True),
    ColumnSpec("newbalanceDest", "number", FEATURE, non_negative=True),
    ColumnSpec(TARGET_COLUMN, "integer", TARGET, allowed=BINARY_VALUES),
    ColumnSpec("isFlaggedFraud", "integer", RULE_FLAG, allowed=BINARY_VALUES),
)

REQUIRED_COLUMNS: tuple[str, ...] = tuple(spec.name for spec in COLUMNS)

# --- dtype map pour pd.read_csv (force les types dès le chargement) --------
DTYPES: dict[str, str] = {
    "step":             "int64",
    "type":             "object",
    "amount":           "float64",
    "nameOrig":         "object",
    "oldbalanceOrg":    "float64",
    "newbalanceOrig":   "float64",
    "nameDest":         "object",
    "oldbalanceDest":   "float64",
    "newbalanceDest":   "float64",
    "isFraud":          "int64",
    "isFlaggedFraud":   "int64",
}

class SchemaError(Exception):
    """Raised when a DataFrame breaks the contract. The message lists every problem found."""


def validate_frame(frame: pd.DataFrame) -> None:
    """Check `frame` against the contract. Return None if it passes; raise SchemaError if not.

    Missing values in the features are allowed here (counted by the EDA, handled at J3);
    a missing target value is not: a row without its label cannot be used.
    """
    missing = [name for name in REQUIRED_COLUMNS if name not in frame.columns]
    unexpected = [name for name in frame.columns if name not in REQUIRED_COLUMNS]
    if missing or unexpected:
        raise SchemaError(
            f"Columns do not match the contract - missing: {missing}, unexpected: {unexpected}"
        )

    problems: list[str] = []
    for spec in COLUMNS:
        problems.extend(_check_column(frame[spec.name], spec))
    if frame[TARGET_COLUMN].isna().any():
        problems.append(f"{TARGET_COLUMN}: missing values in the target")
    if problems:
        raise SchemaError("PaySim contract not respected:\n- " + "\n- ".join(problems))


def _check_column(column: pd.Series, spec: ColumnSpec) -> list[str]:
    if not _has_kind(column, spec.kind):
        return [f"{spec.name}: expected {spec.kind}, got {column.dtype}"]
    problems: list[str] = []
    values = column.dropna()
    if spec.allowed is not None:
        invalid = sorted({str(v) for v in values.unique()} - {str(a) for a in spec.allowed})
        if invalid:
            problems.append(f"{spec.name}: values not allowed {invalid[:5]}")
    if spec.non_negative and (values < 0).any():
        problems.append(f"{spec.name}: negative values")
    return problems


def _has_kind(column: pd.Series, kind: str) -> bool:
    if ptypes.is_bool_dtype(column):
        return False  # True/False is not a PaySim value, even though Python treats it as 1/0
    if kind == "integer":
        return ptypes.is_integer_dtype(column)
    if kind == "number":
        return ptypes.is_numeric_dtype(column)
    return ptypes.is_string_dtype(column)