"""
SoC layer      : 2 — Ingestion/Parser
Responsibility : Check the input of one case (synthetic ID, the 7 verified transaction fields, an
                 optional case note) and return a typed, read-only CaseInput; refuse anything else
                 with CaseInputError, naming the field at fault
Never does     : Decide (no score, no band, no priority); read or write a file or the database;
                 accept a label (isFraud, isFlaggedFraud) or an identifier (nameOrig, nameDest);
                 trust or interpret the case note (it is untrusted data, F05)
Reference      : Architecture_Projet.md v1.3 — section 1.2, section 5, section 8 (n° 39), D-09, D-10;
                 Features_Complet.md G08, F05; brief §10.1, §10.3; PASSATION.md §6, decisions PR 4
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass
from typing import Any

from src.data.schema import COLUMNS, FEATURE, TARGET_COLUMN

# Synthetic case ID: "CASE-" + 4 digits (D-09 notation "CASE-xxxx", PASSATION.md §7).
CASE_ID_PATTERN = re.compile(r"CASE-\d{4}")

# The verified transaction fields = the columns whose role is FEATURE in the PaySim contract.
# Taken from schema.py, so the case input and the model contract cannot drift apart.
FEATURE_SPECS = tuple(spec for spec in COLUMNS if spec.role == FEATURE)
FEATURE_FIELDS: tuple[str, ...] = tuple(spec.name for spec in FEATURE_SPECS)

CASE_ID_FIELD = "case_id"
CASE_NOTE_FIELD = "case_note"
ALLOWED_FIELDS = frozenset({CASE_ID_FIELD, CASE_NOTE_FIELD, *FEATURE_FIELDS})
REQUIRED_FIELDS = (CASE_ID_FIELD, *FEATURE_FIELDS)  # case_note is optional

# Labels are refused with their own message: they must never enter a case (D-09, D-10).
LABEL_FIELDS = frozenset({TARGET_COLUMN, "isFlaggedFraud"})


class CaseInputError(ValueError):
    """Raised when a case input is invalid. The message names the field at fault."""


@dataclass(frozen=True)
class CaseInput:
    """A checked case input. No length limit on case_note (founder decision, PR 4, Q2)."""

    case_id: str
    step: int
    type: str
    amount: float
    oldbalanceOrg: float
    newbalanceOrig: float
    oldbalanceDest: float
    newbalanceDest: float
    case_note: str | None = None

    def transaction(self) -> dict[str, Any]:
        """The 7 verified transaction fields, as a plain dict (what is stored and scored)."""
        return {name: getattr(self, name) for name in FEATURE_FIELDS}


def parse_case_input(raw: Any) -> CaseInput:
    """Check `raw` (a dict) and return a CaseInput; raise CaseInputError at the first problem."""
    if not isinstance(raw, dict):
        raise CaseInputError(f"Case input must be a dict, got {type(raw).__name__}")

    labels = sorted(LABEL_FIELDS & set(raw))
    if labels:
        raise CaseInputError(f"Labels are not allowed in a case input: {labels}")
    unknown = sorted(str(key) for key in raw if key not in ALLOWED_FIELDS)
    if unknown:
        raise CaseInputError(f"Unknown fields in case input: {unknown}")
    missing = [name for name in REQUIRED_FIELDS if name not in raw]
    if missing:
        raise CaseInputError(f"Missing fields in case input: {missing}")

    case_id = raw[CASE_ID_FIELD]
    if not isinstance(case_id, str) or not CASE_ID_PATTERN.fullmatch(case_id):
        raise CaseInputError(f"{CASE_ID_FIELD}: expected 'CASE-' followed by 4 digits")

    values: dict[str, Any] = {}
    for spec in FEATURE_SPECS:
        values[spec.name] = _check_value(spec, raw[spec.name])

    case_note = raw.get(CASE_NOTE_FIELD)
    if case_note is not None and not isinstance(case_note, str):
        raise CaseInputError(f"{CASE_NOTE_FIELD}: expected text or null")

    return CaseInput(case_id=case_id, case_note=case_note, **values)


def _check_value(spec: Any, value: Any) -> Any:
    """Check one transaction field against its ColumnSpec (kind, allowed values, sign)."""
    # bool is a subclass of int in Python: True/False is not a PaySim value (same rule as schema.py).
    if isinstance(value, bool):
        raise CaseInputError(f"{spec.name}: expected {spec.kind}, got a boolean")
    if spec.kind == "integer":
        if not isinstance(value, int):
            raise CaseInputError(f"{spec.name}: expected integer, got {type(value).__name__}")
    elif spec.kind == "number":
        if not isinstance(value, (int, float)):
            raise CaseInputError(f"{spec.name}: expected number, got {type(value).__name__}")
        if not math.isfinite(value):
            raise CaseInputError(f"{spec.name}: expected a finite number")
        value = float(value)
    elif not isinstance(value, str):
        raise CaseInputError(f"{spec.name}: expected text, got {type(value).__name__}")

    if spec.allowed is not None and value not in spec.allowed:
        raise CaseInputError(f"{spec.name}: value not allowed ({value!r})")
    if spec.non_negative and value < 0:
        raise CaseInputError(f"{spec.name}: negative value not allowed")
    return value
