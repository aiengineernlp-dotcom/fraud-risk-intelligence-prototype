"""
SoC layer      : 2 — Ingestion/Parser
Responsibility : Read cases (one, or all those in a state) and write them, their state, step results: create a case
                 once (DuplicateCaseError, D-07), store the state ALREADY DECIDED by the caller,
                 store a step result once under the key "{case_id}:{step}" (D-07, G10), store the
                 reviewer decision with its state in one UPDATE (set_review_decision, I71)
Never does     : Decide a transition (state_machine.py + the orchestrator do); decide a score, band
                 or validity; build SQL from formatted strings (parameters "?" only); delete a row;
                 store a label (isFraud, isFlaggedFraud)
Reference      : Architecture_Projet.md v1.3 — section 1.2, section 5, section 8 (n° 34),
                 section 10.2, D-07; Features_Complet.md G10; PASSATION.md §6, decisions PR 3
"""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from src.agent.domain import CaseState
from src.agent.domain import REVIEWER_OUTCOMES  # PR 13: the 3 decisions a reviewer can record

# Decision (e): the labels never enter a case (section 10.2: "jamais l'étiquette").
LABEL_COLUMNS = frozenset({"isFraud", "isFlaggedFraud"})

# Decision PR 9 (a): the only values of cases.priority. A copy of routing_policy.PRIORITIES, because
# layer 2 never imports layer 3; tests/test_review_and_audit.py checks the two sets are equal.
ALLOWED_PRIORITIES = frozenset({"high", "normal"})


class DuplicateCaseError(Exception):
    """Raised when a case_id already exists: a case is created only once (D-07)."""

    def __init__(self, case_id: str) -> None:
        self.case_id = case_id
        super().__init__(f"Case already exists: {case_id}")


class CaseNotFoundError(Exception):
    """Raised when the case to update does not exist."""

    def __init__(self, case_id: str) -> None:
        self.case_id = case_id
        super().__init__(f"Case not found: {case_id}")


class LabelInCaseError(ValueError):
    """Raised when the transaction of a case contains isFraud or isFlaggedFraud (decision (e))."""


class InvalidPriorityError(ValueError):
    """Raised when the priority is not one of ALLOWED_PRIORITIES (decision PR 9 (a))."""


@dataclass(frozen=True)
class CaseRecord:
    """One row of `cases`, as read back (section 10.2)."""

    case_id: str
    state: CaseState
    transaction: dict[str, Any]
    case_note: str | None
    priority: str | None
    reviewer_decision: CaseState | None
    reviewer_comment: str | None
    created_at: str
    updated_at: str


@dataclass(frozen=True)
class StepResult:
    """One row of `step_results`, as read back (section 10.2)."""

    idempotency_key: str
    case_id: str
    step: str
    result: dict[str, Any]
    attempts: int
    created_at: str


def utc_now() -> str:
    """Current time, ISO 8601 UTC with its offset, e.g. 2026-11-13T14:05:09.123456+00:00 (decision (d))."""
    return datetime.now(timezone.utc).isoformat(timespec="microseconds")


def idempotency_key(case_id: str, step: str) -> str:
    """The key of a step result: "{case_id}:{step}" (D-07)."""
    return f"{case_id}:{step}"


def _to_json(value: dict[str, Any]) -> str:
    # No default=str: an object that is not JSON (e.g. a dataclass) raises TypeError, on purpose.
    return json.dumps(value, sort_keys=True, ensure_ascii=False)


def _case_from_row(row: sqlite3.Row) -> CaseRecord:
    decision = row["reviewer_decision"]
    return CaseRecord(
        case_id=row["case_id"],
        state=CaseState(row["state"]),
        transaction=json.loads(row["transaction_json"]),
        case_note=row["case_note"],
        priority=row["priority"],
        reviewer_decision=CaseState(decision) if decision is not None else None,
        reviewer_comment=row["reviewer_comment"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def create_case(
    conn: sqlite3.Connection,
    case_id: str,
    state: CaseState,
    transaction: dict[str, Any],
    case_note: str | None = None,
) -> CaseRecord:
    """Store a new case with the state given by the caller; refuse a case_id that already exists."""
    labels = LABEL_COLUMNS & set(transaction)
    if labels:
        raise LabelInCaseError(f"Label field(s) not allowed in a case: {sorted(labels)}")

    now = utc_now()
    try:
        with conn:
            conn.execute(
                "INSERT INTO cases (case_id, state, transaction_json, case_note, created_at,"
                " updated_at) VALUES (?, ?, ?, ?, ?, ?)",
                (case_id, state.value, _to_json(transaction), case_note, now, now),
            )
    except sqlite3.IntegrityError:
        # The same error comes from a duplicate key or from a failed CHECK:
        # it is a duplicate only if the case is really there.
        if get_case(conn, case_id) is not None:
            raise DuplicateCaseError(case_id) from None
        raise
    return get_case(conn, case_id)


def get_case(conn: sqlite3.Connection, case_id: str) -> CaseRecord | None:
    """Return the case, or None if it does not exist."""
    row = conn.execute("SELECT * FROM cases WHERE case_id = ?", (case_id,)).fetchone()
    return _case_from_row(row) if row is not None else None


def list_cases_in_state(conn: sqlite3.Connection, state: CaseState) -> list[CaseRecord]:
    """Return every case whose current state is `state` (read only, decision I69 (2)).

    No order on purpose: sorting the review queue is the routing policy's job (G11), not layer 2's.
    """
    rows = conn.execute("SELECT * FROM cases WHERE state = ?", (state.value,)).fetchall()
    return [_case_from_row(row) for row in rows]


def update_state(conn: sqlite3.Connection, case_id: str, new_state: CaseState) -> None:
    """Store the new state. The caller has already checked the transition with state_machine.py."""
    with conn:
        cursor = conn.execute(
            "UPDATE cases SET state = ?, updated_at = ? WHERE case_id = ?",
            (new_state.value, utc_now(), case_id),
        )
    if cursor.rowcount == 0:
        raise CaseNotFoundError(case_id)


def set_priority(conn: sqlite3.Connection, case_id: str, priority: str) -> None:
    """Store the priority ALREADY decided by routing_policy.py (n° 54); decide nothing.

    Only `priority` and `updated_at` change. A recomputed priority overwrites the old one: the
    history stays in the audit trail (decision PR 9, GO of the plan).
    """
    # No CHECK in db.py (a schema change without migration, Q-11): this check is the only barrier.
    if not isinstance(priority, str) or priority not in ALLOWED_PRIORITIES:
        raise InvalidPriorityError(f"Priority must be one of {sorted(ALLOWED_PRIORITIES)}")
    with conn:
        cursor = conn.execute(
            "UPDATE cases SET priority = ?, updated_at = ? WHERE case_id = ?",
            (priority, utc_now(), case_id),
        )
    if cursor.rowcount == 0:
        raise CaseNotFoundError(case_id)


def save_step_result(
    conn: sqlite3.Connection,
    case_id: str,
    step: str,
    result: dict[str, Any],
    attempts: int,
) -> tuple[StepResult, bool]:
    """Store a step result once; return (stored result, created).

    Decision (c), D-07: if the step is already stored, nothing is rewritten and the STORED result
    is returned with created=False, even if `result` is different.
    """
    key = idempotency_key(case_id, step)
    with conn:
        # DO NOTHING applies only to an existing key; a failed CHECK or foreign key still raises.
        cursor = conn.execute(
            "INSERT INTO step_results (idempotency_key, case_id, step, result_json, attempts,"
            " created_at) VALUES (?, ?, ?, ?, ?, ?)"
            " ON CONFLICT (idempotency_key) DO NOTHING",
            (key, case_id, step, _to_json(result), attempts, utc_now()),
        )
    created = cursor.rowcount == 1
    return get_step_result(conn, case_id, step), created


def get_step_result(conn: sqlite3.Connection, case_id: str, step: str) -> StepResult | None:
    """Return the stored result of this step, or None if the step was never stored."""
    row = conn.execute(
        "SELECT * FROM step_results WHERE idempotency_key = ?",
        (idempotency_key(case_id, step),),
    ).fetchone()
    if row is None:
        return None
    return StepResult(
        idempotency_key=row["idempotency_key"],
        case_id=row["case_id"],
        step=row["step"],
        result=json.loads(row["result_json"]),
        attempts=row["attempts"],
        created_at=row["created_at"],
    )


# --- reviewer decision (PR 13, decisions I71) -----------------------------------------------------

# Decision I71 (c1): the longest reviewer comment accepted. A longer text is refused, never cut.
REVIEWER_COMMENT_MAX_CHARS = 1000


class InvalidReviewDecisionError(ValueError):
    """Raised when the decision is not one of domain.REVIEWER_OUTCOMES (FAILED included, I71 (1))."""


class InvalidReviewCommentError(ValueError):
    """Raised when the comment is not text, or is longer than REVIEWER_COMMENT_MAX_CHARS."""


class CaseNotInReviewError(Exception):
    """Raised when the case exists but is no longer in HUMAN_REVIEW: nothing was written."""

    def __init__(self, case_id: str) -> None:
        self.case_id = case_id
        super().__init__(f"Case not in human review: {case_id}")


def check_reviewer_comment(comment: Any) -> str | None:
    """Return the comment to store: None for no comment, empty text or spaces only; otherwise the
    text exactly as given. Not text, or longer than REVIEWER_COMMENT_MAX_CHARS -> refused (I71 (c1))."""
    if comment is None:
        return None
    if not isinstance(comment, str):
        raise InvalidReviewCommentError("The reviewer comment must be text")
    if comment.strip() == "":
        return None
    if len(comment) > REVIEWER_COMMENT_MAX_CHARS:
        raise InvalidReviewCommentError(
            f"The reviewer comment must have at most {REVIEWER_COMMENT_MAX_CHARS} characters")
    return comment


def set_review_decision(
    conn: sqlite3.Connection,
    case_id: str,
    decision: CaseState,
    comment: str | None,
) -> None:
    """Store the reviewer decision ALREADY checked by the caller (update_case + state_machine.py).

    One UPDATE writes the new state, reviewer_decision, reviewer_comment and updated_at together:
    the state never changes without its decision. The guard "AND state = HUMAN_REVIEW" makes a
    second writer (double click, two sessions) touch no row instead of overwriting a decision.
    """
    # Barriers of the last layer before the database (the CHECK of db.py is a second one).
    if not isinstance(decision, CaseState) or decision not in REVIEWER_OUTCOMES:
        raise InvalidReviewDecisionError(
            f"Decision must be one of {sorted(state.value for state in REVIEWER_OUTCOMES)}")
    stored_comment = check_reviewer_comment(comment)
    with conn:
        cursor = conn.execute(
            "UPDATE cases SET state = ?, reviewer_decision = ?, reviewer_comment = ?, updated_at = ?"
            " WHERE case_id = ? AND state = ?",
            (decision.value, decision.value, stored_comment, utc_now(), case_id,
             CaseState.HUMAN_REVIEW.value),
        )
    if cursor.rowcount == 0:
        if get_case(conn, case_id) is None:
            raise CaseNotFoundError(case_id)
        raise CaseNotInReviewError(case_id)
