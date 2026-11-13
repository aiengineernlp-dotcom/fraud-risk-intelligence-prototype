"""
SoC layer      : Tests
Responsibility : Test the storage layer and the audit trail: tables and constraints of section 10.2,
                 append-only audit, duplicate submission, step idempotency (started at J4, PR 3;
                 the review decision, the validation view and the export are added at J5)
Never does     : Use data/runtime/ (temporary database from tmp_path only); call the network or an LLM
Reference      : Architecture_Projet.md v1.3 — section 8 (n° 70, tests of n° 33, 34, 35),
                 section 10.2, D-07; Features_Complet.md G10; PASSATION.md §6, decisions PR 3
"""

from __future__ import annotations

import sqlite3

import pytest

from src.agent.domain import REVIEWER_OUTCOMES, CaseState
from src.storage.case_repository import (
    CaseNotFoundError,
    DuplicateCaseError,
    LabelInCaseError,
    create_case,
    get_case,
    get_step_result,
    save_step_result,
    update_state,
)
from src.storage.db import create_tables, init_db

NOW = "2026-11-13T10:00:00.000000+00:00"


def _insert_case_raw(conn: sqlite3.Connection, case_id: str, state: str) -> None:
    """Plain SQL insert, to test the database constraints without the repository."""
    with conn:
        conn.execute(
            "INSERT INTO cases (case_id, state, transaction_json, created_at, updated_at)"
            " VALUES (?, ?, ?, ?, ?)",
            (case_id, state, "{}", NOW, NOW),
        )


def _insert_step_raw(conn: sqlite3.Connection, case_id: str, step: str, attempts: int) -> None:
    with conn:
        conn.execute(
            "INSERT INTO step_results (idempotency_key, case_id, step, result_json, attempts,"
            " created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (f"{case_id}:{step}", case_id, step, "{}", attempts, NOW),
        )


# --- db.py (n° 33) -------------------------------------------------------------------------------


def test_tables_and_triggers_created(db_conn):
    names = {
        (row["type"], row["name"])
        for row in db_conn.execute("SELECT type, name FROM sqlite_master")
    }
    assert {("table", "cases"), ("table", "step_results"), ("table", "audit_events")} <= names
    assert ("trigger", "audit_events_no_update") in names
    assert ("trigger", "audit_events_no_delete") in names


def test_create_tables_is_idempotent(tmp_path):
    db_path = tmp_path / "again.db"
    conn = init_db(db_path)
    _insert_case_raw(conn, "CASE-1", "RECEIVED")
    create_tables(conn)  # second run on the same connection
    conn.close()
    conn = init_db(db_path)  # third run, new connection
    count = conn.execute("SELECT COUNT(*) FROM cases").fetchone()[0]
    conn.close()
    assert count == 1


def test_foreign_keys_enabled(db_conn):
    assert db_conn.execute("PRAGMA foreign_keys").fetchone()[0] == 1
    with pytest.raises(sqlite3.IntegrityError):
        _insert_step_raw(db_conn, "UNKNOWN-CASE", "score", 1)


@pytest.mark.parametrize("state", list(CaseState))
def test_every_case_state_accepted(db_conn, state):
    # Keeps the hard-coded list in db.py aligned with CaseState (founder decision, PR 3).
    _insert_case_raw(db_conn, f"CASE-{state.value}", state.value)


def test_unknown_state_rejected(db_conn):
    with pytest.raises(sqlite3.IntegrityError):
        _insert_case_raw(db_conn, "CASE-1", "APPROVED")


@pytest.mark.parametrize("decision", sorted(o.value for o in REVIEWER_OUTCOMES))
def test_reviewer_decision_accepted(db_conn, decision):
    _insert_case_raw(db_conn, "CASE-1", "HUMAN_REVIEW")
    with db_conn:
        db_conn.execute(
            "UPDATE cases SET reviewer_decision = ? WHERE case_id = ?", (decision, "CASE-1")
        )


def test_unknown_reviewer_decision_rejected(db_conn):
    _insert_case_raw(db_conn, "CASE-1", "HUMAN_REVIEW")
    with pytest.raises(sqlite3.IntegrityError):
        with db_conn:
            db_conn.execute(
                "UPDATE cases SET reviewer_decision = ? WHERE case_id = ?", ("FAILED", "CASE-1")
            )


def test_attempts_zero_rejected(db_conn):
    _insert_case_raw(db_conn, "CASE-1", "RECEIVED")
    with pytest.raises(sqlite3.IntegrityError):
        _insert_step_raw(db_conn, "CASE-1", "score", 0)


def test_unknown_step_rejected(db_conn):
    _insert_case_raw(db_conn, "CASE-1", "RECEIVED")
    with pytest.raises(sqlite3.IntegrityError):
        _insert_step_raw(db_conn, "CASE-1", "payment", 1)


# --- case_repository.py (n° 34) ------------------------------------------------------------------

TRANSACTION = {"type": "TRANSFER", "amount": 181.0, "step": 1}


def test_duplicate_submission(db_conn):
    first = create_case(db_conn, "CASE-1", CaseState.RECEIVED, TRANSACTION, "note A")
    with pytest.raises(DuplicateCaseError):
        create_case(db_conn, "CASE-1", CaseState.SCORED, {"amount": 1.0}, "note B")
    assert get_case(db_conn, "CASE-1") == first  # the original is untouched
    assert db_conn.execute("SELECT COUNT(*) FROM cases").fetchone()[0] == 1


def test_create_case_round_trip(db_conn):
    case = create_case(db_conn, "CASE-1", CaseState.RECEIVED, TRANSACTION, "note")
    assert case.state is CaseState.RECEIVED
    assert case.transaction == TRANSACTION
    assert case.case_note == "note"
    assert case.reviewer_decision is None
    assert case.created_at == case.updated_at
    assert case.created_at.endswith("+00:00")


@pytest.mark.parametrize("label", ["isFraud", "isFlaggedFraud"])
def test_label_in_case_refused(db_conn, label):
    with pytest.raises(LabelInCaseError):
        create_case(db_conn, "CASE-1", CaseState.RECEIVED, {**TRANSACTION, label: 0})
    assert get_case(db_conn, "CASE-1") is None


def test_get_unknown_case_returns_none(db_conn):
    assert get_case(db_conn, "UNKNOWN") is None


def test_update_state_records_given_state(db_conn):
    before = create_case(db_conn, "CASE-1", CaseState.RECEIVED, TRANSACTION)
    update_state(db_conn, "CASE-1", CaseState.SCORED)
    after = get_case(db_conn, "CASE-1")
    assert after.state is CaseState.SCORED
    # Same ISO format, so text order = time order; ">=" because two calls can share a microsecond.
    assert after.updated_at >= before.updated_at
    assert after.created_at == before.created_at


def test_update_state_unknown_case(db_conn):
    with pytest.raises(CaseNotFoundError):
        update_state(db_conn, "UNKNOWN", CaseState.SCORED)


def test_step_result_idempotent(db_conn):
    create_case(db_conn, "CASE-1", CaseState.RECEIVED, TRANSACTION)
    first, created_first = save_step_result(db_conn, "CASE-1", "score", {"score": 0.91}, 1)
    second, created_second = save_step_result(db_conn, "CASE-1", "score", {"score": 0.12}, 3)
    assert created_first is True
    assert created_second is False
    assert second == first  # the stored result is returned, the new one is ignored (D-07)
    assert second.result == {"score": 0.91}
    assert second.idempotency_key == "CASE-1:score"
    assert db_conn.execute("SELECT COUNT(*) FROM step_results").fetchone()[0] == 1


def test_get_unknown_step_returns_none(db_conn):
    create_case(db_conn, "CASE-1", CaseState.RECEIVED, TRANSACTION)
    assert get_step_result(db_conn, "CASE-1", "draft") is None


def test_step_result_constraints_still_apply(db_conn):
    create_case(db_conn, "CASE-1", CaseState.RECEIVED, TRANSACTION)
    with pytest.raises(sqlite3.IntegrityError):
        save_step_result(db_conn, "CASE-1", "score", {}, 0)  # attempts >= 1
    with pytest.raises(sqlite3.IntegrityError):
        save_step_result(db_conn, "UNKNOWN", "score", {}, 1)  # foreign key
