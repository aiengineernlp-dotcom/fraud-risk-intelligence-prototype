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
