"""
SoC layer      : 1 — Data
Responsibility : Open the SQLite database at a path RECEIVED AS A PARAMETER (foreign keys on) and
                 create the 3 tables of section 10.2 (cases, step_results, audit_events) with their
                 constraints, plus the 2 triggers that make audit_events append-only; idempotent
Never does     : Any business logic; read config.py (the caller passes paths.runtime_db); import
                 domain.py (registry n° 33); delete data
Reference      : Architecture_Projet.md v1.3 — section 1.2, section 5, section 8 (n° 33),
                 section 10.2, D-07; PASSATION.md §6, decisions PR 3 (2026-11-13)
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

# Founder decision (PR 3): the allowed values are written here, in the SQL, because the registry
# does not let db.py import domain.py. tests/test_review_and_audit.py inserts every CaseState
# value, so the two lists cannot drift apart unnoticed.

_CREATE_CASES = """
CREATE TABLE IF NOT EXISTS cases (
    case_id           TEXT PRIMARY KEY,
    state             TEXT NOT NULL CHECK (state IN (
                          'RECEIVED', 'SCORED', 'EVIDENCE_READY', 'DRAFTED', 'VALIDATED',
                          'VALIDATION_REJECTED', 'HUMAN_REVIEW', 'CLOSED', 'ESCALATED',
                          'NEEDS_MORE_INFORMATION', 'FAILED')),
    transaction_json  TEXT NOT NULL,
    case_note         TEXT,
    priority          TEXT,
    reviewer_decision TEXT CHECK (reviewer_decision IS NULL OR reviewer_decision IN (
                          'CLOSED', 'ESCALATED', 'NEEDS_MORE_INFORMATION')),
    reviewer_comment  TEXT,
    created_at        TEXT NOT NULL,
    updated_at        TEXT NOT NULL
)
"""

# idempotency_key = "{case_id}:{step}" (D-07). No ON DELETE CASCADE: no data is deleted.
_CREATE_STEP_RESULTS = """
CREATE TABLE IF NOT EXISTS step_results (
    idempotency_key TEXT PRIMARY KEY,
    case_id         TEXT NOT NULL REFERENCES cases (case_id),
    step            TEXT NOT NULL CHECK (step IN ('score', 'evidence', 'draft', 'validation')),
    result_json     TEXT NOT NULL,
    attempts        INTEGER NOT NULL CHECK (attempts >= 1),
    created_at      TEXT NOT NULL
)
"""

# AUTOINCREMENT: an event_id is never reused, so event_id gives the order of the events.
_CREATE_AUDIT_EVENTS = """
CREATE TABLE IF NOT EXISTS audit_events (
    event_id       INTEGER PRIMARY KEY AUTOINCREMENT,
    case_id        TEXT NOT NULL REFERENCES cases (case_id),
    timestamp      TEXT NOT NULL,
    actor          TEXT NOT NULL,
    action         TEXT NOT NULL,
    state_from     TEXT,
    state_to       TEXT,
    result         TEXT NOT NULL,
    details_json   TEXT,
    model_version  TEXT,
    prompt_version TEXT
)
"""

# Decision (a): the database itself refuses any change to an audit event, on top of
# audit_repository.py offering no update or delete function.
_CREATE_AUDIT_NO_UPDATE = """
CREATE TRIGGER IF NOT EXISTS audit_events_no_update
BEFORE UPDATE ON audit_events
BEGIN
    SELECT RAISE(ABORT, 'audit_events is append-only');
END
"""

_CREATE_AUDIT_NO_DELETE = """
CREATE TRIGGER IF NOT EXISTS audit_events_no_delete
BEFORE DELETE ON audit_events
BEGIN
    SELECT RAISE(ABORT, 'audit_events is append-only');
END
"""

_SCHEMA = (
    _CREATE_CASES,
    _CREATE_STEP_RESULTS,
    _CREATE_AUDIT_EVENTS,
    _CREATE_AUDIT_NO_UPDATE,
    _CREATE_AUDIT_NO_DELETE,
)


def connect(db_path: str | Path) -> sqlite3.Connection:
    """Open the database file at `db_path` and turn foreign keys on.

    SQLite keeps `foreign_keys` for one connection only, so every connection must come from here.
    """
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row  # rows readable by column name
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def create_tables(conn: sqlite3.Connection) -> None:
    """Create the tables and triggers if they do not exist yet (running it again changes nothing).

    Limit (PASSATION §6, Q-11): an existing database keeps its old schema; nothing is migrated.
    """
    with conn:
        for statement in _SCHEMA:
            conn.execute(statement)


def init_db(db_path: str | Path) -> sqlite3.Connection:
    """Open the database and make sure the schema exists; return the open connection."""
    conn = connect(db_path)
    create_tables(conn)
    return conn
