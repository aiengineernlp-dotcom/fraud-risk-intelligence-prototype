"""
SoC layer      : 2 — Ingestion/Parser
Responsibility : Append structured audit events (AuditEvent, section 10.2) and read the events of a
                 case in order (event_id); refuse a secret-looking key in `details`
                 (SecretInAuditError) and a timestamp that is not ISO 8601 UTC
Never does     : Modify or delete an event (no such function; the database triggers refuse it too);
                 decide anything; build SQL from formatted strings (parameters "?" only)
Reference      : Architecture_Projet.md v1.3 — section 1.2, section 5, section 8 (n° 35),
                 section 10.2; brief §11.3; PASSATION.md §6, decisions PR 3 (a), (b), (d)
"""

from __future__ import annotations

import json
import re
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

from src.agent.domain import AuditEvent, CaseState

# Decision (b): a key of `details` is cut into pieces on "_" and "-" (lower case).
# It is refused if one piece is in this set, if a piece "api" is followed by "key", or if the
# whole key is "key". Whole pieces only: "prompt_tokens" and "idempotency_key" stay allowed.
_SECRET_PIECES = frozenset({"secret", "password", "passwd", "token", "apikey"})


class SecretInAuditError(ValueError):
    """Raised when `details` has a key that looks like a secret: nothing is written (decision (b)).

    The audit is append-only, so a secret written by mistake could never be removed.
    """


@dataclass(frozen=True)
class StoredAuditEvent:
    """An audit event read back, with the event_id given by the database."""

    event_id: int
    event: AuditEvent


def _looks_like_secret(key: str) -> bool:
    name = key.lower()
    if name == "key":
        return True
    pieces = re.split(r"[_-]", name)
    if _SECRET_PIECES & set(pieces):
        return True
    return any(a == "api" and b == "key" for a, b in zip(pieces, pieces[1:]))


def _secret_keys(value: Any, path: str = "") -> list[str]:
    """Return the paths of the secret-looking keys, looking inside nested dicts and lists."""
    found: list[str] = []
    if isinstance(value, dict):
        for key, inner in value.items():
            key_path = f"{path}.{key}" if path else str(key)
            if _looks_like_secret(str(key)):
                found.append(key_path)
            found.extend(_secret_keys(inner, key_path))
    elif isinstance(value, list):
        for index, inner in enumerate(value):
            found.extend(_secret_keys(inner, f"{path}[{index}]"))
    return found


def _check_utc_timestamp(timestamp: str) -> None:
    """Decision (d): ISO 8601 with a UTC offset (+00:00 or Z); anything else is refused."""
    try:
        parsed = datetime.fromisoformat(timestamp)
    except (TypeError, ValueError):
        raise ValueError(f"Audit timestamp is not ISO 8601: {timestamp!r}") from None
    # utcoffset() is None for a time without a zone, so that case is refused too.
    if parsed.utcoffset() != timedelta(0):
        raise ValueError(f"Audit timestamp is not UTC: {timestamp!r}")


def append_event(conn: sqlite3.Connection, event: AuditEvent) -> int:
    """Append one event and return its event_id. The case must exist (foreign key)."""
    _check_utc_timestamp(event.timestamp)
    secrets = _secret_keys(event.details)
    if secrets:
        # Only the key paths are named in the message, never the values.
        raise SecretInAuditError(f"Secret-looking key(s) in audit details: {secrets}")

    details_json = (
        json.dumps(event.details, sort_keys=True, ensure_ascii=False)
        if event.details is not None
        else None
    )
    with conn:
        cursor = conn.execute(
            "INSERT INTO audit_events (case_id, timestamp, actor, action, state_from, state_to,"
            " result, details_json, model_version, prompt_version)"
            " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                event.case_id,
                event.timestamp,
                event.actor,
                event.action,
                event.state_from.value if event.state_from is not None else None,
                event.state_to.value if event.state_to is not None else None,
                event.result,
                details_json,
                event.model_version,
                event.prompt_version,
            ),
        )
    return cursor.lastrowid


def list_events(conn: sqlite3.Connection, case_id: str) -> list[StoredAuditEvent]:
    """Return the events of one case, oldest first (ordered by event_id, never by timestamp)."""
    rows = conn.execute(
        "SELECT * FROM audit_events WHERE case_id = ? ORDER BY event_id ASC", (case_id,)
    ).fetchall()
    return [
        StoredAuditEvent(
            event_id=row["event_id"],
            event=AuditEvent(
                case_id=row["case_id"],
                timestamp=row["timestamp"],
                actor=row["actor"],
                action=row["action"],
                result=row["result"],
                state_from=CaseState(row["state_from"]) if row["state_from"] else None,
                state_to=CaseState(row["state_to"]) if row["state_to"] else None,
                details=json.loads(row["details_json"]) if row["details_json"] else None,
                model_version=row["model_version"],
                prompt_version=row["prompt_version"],
            ),
        )
        for row in rows
    ]
