"""
SoC layer      : 3 — Logic Engine
Responsibility : Export the audit trail of one case, or of every case, as CSV or JSON text (I02):
                 one header line then one line per event read (CSV), or one object per event (JSON),
                 in event_id order; refuse the whole export if an event holds a label key, a
                 secret-looking key or a non-finite number in `details`
Never does     : Write to the database (not even an audit event about the export) or to a file
                 (the caller gets a str); read the database other than through audit_repository.py;
                 put a label or a secret in an export; show a refused value in an error message;
                 call the LLM; import Streamlit
Reference      : Architecture_Projet.md v1.4 — section 1.2, section 5, section 8 (n° 65),
                 section 10.2 (audit_events); Features_Complet.md I02; PASSATION.md §6, decision I64
                 (a), (b), (c), Q-A, Q-B, Q-C, (1), (2)
"""

from __future__ import annotations

import csv
import io
import json
import math
from typing import Any, Sequence

from src.audit.audit_repository import (
    StoredAuditEvent,
    list_all_events,
    list_events,
    secret_keys_in,
)

# The columns of audit_events (section 10.2), in that order; `details_json` is exported as `details`.
EXPORT_COLUMNS = (
    "event_id",
    "case_id",
    "timestamp",
    "actor",
    "action",
    "state_from",
    "state_to",
    "result",
    "details",
    "model_version",
    "prompt_version",
)

FORMATS = ("csv", "json")

# Copy of case_repository.LABEL_COLUMNS: the registry (n° 65) lets this file depend on
# audit_repository.py only. test_label_keys_match checks that both sets stay equal (I64 (2)).
LABEL_KEYS = frozenset({"isFraud", "isFlaggedFraud"})

# Decision Q-A (I64): a CSV cell starting with one of these could be run as a formula by a
# spreadsheet, so it gets an apostrophe in front. CSV only: the JSON export keeps the exact value.
FORMULA_PREFIXES = ("=", "+", "-", "@", "\t", "\r")


class AuditExportError(ValueError):
    """Raised when an export is refused (unknown format, label, secret or non-finite number).

    The message names the event_id and the key paths only, never a value.
    """


def read_audit(conn: Any, case_id: str | None = None) -> list[StoredAuditEvent]:
    """Read the events to export: one case if `case_id` is given, every case if it is None."""
    if case_id is None:
        return list_all_events(conn)
    return list_events(conn, case_id)


def _label_keys(value: Any, path: str = "") -> list[str]:
    """Return the paths of the label keys, looking inside nested dicts and lists."""
    found: list[str] = []
    if isinstance(value, dict):
        for key, inner in value.items():
            key_path = f"{path}.{key}" if path else str(key)
            if key in LABEL_KEYS:
                found.append(key_path)
            found.extend(_label_keys(inner, key_path))
    elif isinstance(value, list):
        for index, inner in enumerate(value):
            found.extend(_label_keys(inner, f"{path}[{index}]"))
    return found


def _non_finite_paths(value: Any, path: str = "") -> list[str]:
    """Return the paths of the NaN or infinite numbers (decision Q-B: strict JSON only)."""
    if isinstance(value, float) and not math.isfinite(value):
        return [path]
    found: list[str] = []
    if isinstance(value, dict):
        for key, inner in value.items():
            found.extend(_non_finite_paths(inner, f"{path}.{key}" if path else str(key)))
    elif isinstance(value, list):
        for index, inner in enumerate(value):
            found.extend(_non_finite_paths(inner, f"{path}[{index}]"))
    return found


def check_events(events: Sequence[StoredAuditEvent]) -> None:
    """Refuse the whole export if one event cannot be exported safely (nothing is half exported)."""
    for stored in events:
        details = stored.event.details
        labels = _label_keys(details)
        if labels:
            raise AuditExportError(f"Label key(s) in audit event {stored.event_id}: {labels}")
        secrets = secret_keys_in(details)
        if secrets:
            raise AuditExportError(f"Secret-looking key(s) in audit event {stored.event_id}: {secrets}")
        non_finite = _non_finite_paths(details)
        if non_finite:
            raise AuditExportError(
                f"Non-finite number(s) in audit event {stored.event_id}: {non_finite}"
            )


def _as_record(stored: StoredAuditEvent) -> dict[str, Any]:
    """One event as a dict with the EXPORT_COLUMNS keys; `details` stays an object (or None)."""
    event = stored.event
    return {
        "event_id": stored.event_id,
        "case_id": event.case_id,
        "timestamp": event.timestamp,
        "actor": event.actor,
        "action": event.action,
        "state_from": event.state_from.value if event.state_from is not None else None,
        "state_to": event.state_to.value if event.state_to is not None else None,
        "result": event.result,
        "details": event.details,
        "model_version": event.model_version,
        "prompt_version": event.prompt_version,
    }


def _csv_cell(value: Any) -> str:
    """None → empty cell; a cell that a spreadsheet could run as a formula gets a "'" (Q-A)."""
    if value is None:
        return ""
    text = str(value)
    if text.startswith(FORMULA_PREFIXES):
        return "'" + text
    return text


def to_csv(events: Sequence[StoredAuditEvent]) -> str:
    """CSV text: one header line, then one line per event; `details` as JSON text in one column."""
    check_events(events)
    buffer = io.StringIO()
    # csv.writer quotes the cells holding a comma, a quote or a line break (never joined by hand).
    writer = csv.writer(buffer)
    writer.writerow(EXPORT_COLUMNS)
    for stored in events:
        record = _as_record(stored)
        if record["details"] is not None:
            record["details"] = json.dumps(
                record["details"], sort_keys=True, ensure_ascii=False, allow_nan=False
            )
        writer.writerow([_csv_cell(record[column]) for column in EXPORT_COLUMNS])
    return buffer.getvalue()


def to_json(events: Sequence[StoredAuditEvent]) -> str:
    """JSON text: a list with one object per event, in the order given (event_id order)."""
    check_events(events)
    records = [_as_record(stored) for stored in events]
    return json.dumps(records, ensure_ascii=False, indent=2, allow_nan=False)


def export_audit(conn: Any, fmt: str, case_id: str | None = None) -> str:
    """Read the audit of one case (or of every case if `case_id` is None) and return it as text."""
    if fmt not in FORMATS:
        raise AuditExportError(f"Unknown export format {fmt!r}; expected one of {FORMATS}")
    events = read_audit(conn, case_id)
    return to_csv(events) if fmt == "csv" else to_json(events)
