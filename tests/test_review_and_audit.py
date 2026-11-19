"""
SoC layer      : Tests
Responsibility : Test the storage layer and the audit trail: tables and constraints of section 10.2,
                 append-only audit, duplicate submission, step idempotency (started at J4, PR 3;
                 the review decision, the validation view and the export are added at J5)
Never does     : Use data/runtime/ (temporary database from tmp_path only); call the network or an LLM
Reference      : Architecture_Projet.md v1.4 — section 8 (n° 70, tests of n° 33, 34, 35, 65),
                 section 10.2, D-07; Features_Complet.md G10, I02; PASSATION.md §6, decisions PR 3, I64
"""

from __future__ import annotations

import ast
import csv
import io
import json
import math
import sqlite3
from pathlib import Path

import pytest
import yaml

from src.agent.domain import REVIEWER_OUTCOMES, AuditEvent, CaseState
from src.agent.routing_policy import PRIORITIES
from src.audit import audit_repository
from src.audit.audit_export import (
    EXPORT_COLUMNS,
    LABEL_KEYS,
    AuditExportError,
    export_audit,
)
from src.audit.audit_repository import (
    SecretInAuditError,
    append_event,
    list_all_events,
    list_events,
    secret_keys_in,
)
from src.storage.case_repository import (
    ALLOWED_PRIORITIES,
    LABEL_COLUMNS,
    CaseNotFoundError,
    DuplicateCaseError,
    InvalidPriorityError,
    LabelInCaseError,
    create_case,
    get_case,
    get_step_result,
    list_cases_in_state,
    save_step_result,
    set_priority,
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


# --- audit_repository.py (n° 35) -----------------------------------------------------------------


def _event(case_id: str = "CASE-1", **changes) -> AuditEvent:
    fields = dict(
        case_id=case_id,
        timestamp=NOW,
        actor="system",
        action="transition",
        result="ok",
        state_from=CaseState.RECEIVED,
        state_to=CaseState.SCORED,
        details={"attempt": 1, "latency_ms": 12},
        model_version="rf-v1",
        prompt_version=None,
    )
    fields.update(changes)
    return AuditEvent(**fields)


def test_append_and_read_events_in_order(db_conn):
    create_case(db_conn, "CASE-1", CaseState.RECEIVED, TRANSACTION)
    first = _event()
    second = _event(
        actor="tool:score_transaction", action="tool_call", result="timeout",
        state_from=None, state_to=None, details=None,
    )
    third = _event(action="invalid_transition", result="rejected", state_to=CaseState.VALIDATED)
    ids = [append_event(db_conn, e) for e in (first, second, third)]

    stored = list_events(db_conn, "CASE-1")
    assert ids == sorted(ids) and len(set(ids)) == 3
    assert [s.event_id for s in stored] == ids
    assert [s.event for s in stored] == [first, second, third]  # every field round-trips


def test_events_filtered_by_case(db_conn):
    create_case(db_conn, "CASE-1", CaseState.RECEIVED, TRANSACTION)
    create_case(db_conn, "CASE-2", CaseState.RECEIVED, TRANSACTION)
    append_event(db_conn, _event("CASE-1"))
    append_event(db_conn, _event("CASE-2"))
    append_event(db_conn, _event("CASE-1"))
    assert [s.event.case_id for s in list_events(db_conn, "CASE-1")] == ["CASE-1", "CASE-1"]
    assert list_events(db_conn, "UNKNOWN") == []


def test_event_for_unknown_case_refused(db_conn):
    with pytest.raises(sqlite3.IntegrityError):
        append_event(db_conn, _event("UNKNOWN"))


def test_audit_update_refused_by_trigger(db_conn):
    create_case(db_conn, "CASE-1", CaseState.RECEIVED, TRANSACTION)
    event_id = append_event(db_conn, _event())
    with pytest.raises(sqlite3.IntegrityError, match="append-only"):
        with db_conn:
            db_conn.execute(
                "UPDATE audit_events SET result = 'failed' WHERE event_id = ?", (event_id,)
            )
    assert list_events(db_conn, "CASE-1")[0].event.result == "ok"


def test_audit_delete_refused_by_trigger(db_conn):
    create_case(db_conn, "CASE-1", CaseState.RECEIVED, TRANSACTION)
    append_event(db_conn, _event())
    with pytest.raises(sqlite3.IntegrityError, match="append-only"):
        with db_conn:
            db_conn.execute("DELETE FROM audit_events")
    assert len(list_events(db_conn, "CASE-1")) == 1


def test_audited_case_cannot_be_deleted(db_conn):
    # No ON DELETE CASCADE: deleting the case would orphan its audit events, so it is refused.
    create_case(db_conn, "CASE-1", CaseState.RECEIVED, TRANSACTION)
    append_event(db_conn, _event())
    with pytest.raises(sqlite3.IntegrityError):
        with db_conn:
            db_conn.execute("DELETE FROM cases WHERE case_id = 'CASE-1'")


def test_audit_repository_has_no_update_or_delete():
    public = [name for name in dir(audit_repository) if not name.startswith("_")]
    forbidden = ("update", "delete", "remove", "edit", "modify", "clear", "drop")
    assert not [n for n in public if any(word in n.lower() for word in forbidden)]


@pytest.mark.parametrize(
    "details",
    [
        {"api_key": "x"},
        {"OPENAI_API_KEY": "x"},
        {"apikey": "x"},
        {"key": "x"},
        {"access_token": "x"},
        {"client-secret": "x"},
        {"db_password": "x"},
        {"passwd": "x"},
        {"request": {"headers": {"auth_token": "x"}}},
        {"calls": [{"ok": 1}, {"token": "x"}]},
    ],
)
def test_secret_key_in_details_refused(db_conn, details):
    create_case(db_conn, "CASE-1", CaseState.RECEIVED, TRANSACTION)
    with pytest.raises(SecretInAuditError):
        append_event(db_conn, _event(details=details))
    assert list_events(db_conn, "CASE-1") == []  # nothing written


def test_token_count_allowed(db_conn):
    # Whole pieces only: token counts and the idempotency key are not secrets.
    create_case(db_conn, "CASE-1", CaseState.RECEIVED, TRANSACTION)
    details = {"prompt_tokens": 120, "completion_tokens": 80, "idempotency_key": "CASE-1:draft",
               "monkey": 1, "keyword": "x"}
    append_event(db_conn, _event(details=details))
    assert list_events(db_conn, "CASE-1")[0].event.details == details


@pytest.mark.parametrize(
    "timestamp",
    ["2026-11-13T10:00:00", "2026-11-13T11:00:00+01:00", "13/11/2026 10:00", ""],
)
def test_non_utc_timestamp_refused(db_conn, timestamp):
    create_case(db_conn, "CASE-1", CaseState.RECEIVED, TRANSACTION)
    with pytest.raises(ValueError):
        append_event(db_conn, _event(timestamp=timestamp))
    assert list_events(db_conn, "CASE-1") == []


def test_utc_z_timestamp_accepted(db_conn):
    create_case(db_conn, "CASE-1", CaseState.RECEIVED, TRANSACTION)
    append_event(db_conn, _event(timestamp="2026-11-13T10:00:00Z"))
    assert len(list_events(db_conn, "CASE-1")) == 1


# --- set_priority (PR 9, decision (a)) — sensitive zone: only `priority` and `updated_at` change ---

LATER = "2026-11-13T11:00:00.000000+00:00"


def test_priority_sets_match():
    """Layer 2 keeps its own copy of the priorities (it never imports layer 3): both must agree."""
    assert ALLOWED_PRIORITIES == PRIORITIES == frozenset({"high", "normal"})


def test_set_priority_writes_only_priority(db_conn, monkeypatch):
    before = create_case(db_conn, "CASE-1", CaseState.HUMAN_REVIEW, TRANSACTION, "note")
    monkeypatch.setattr("src.storage.case_repository.utc_now", lambda: LATER)
    set_priority(db_conn, "CASE-1", "high")
    after = get_case(db_conn, "CASE-1")
    assert after.priority == "high"
    assert after.updated_at == LATER
    unchanged = ("case_id", "state", "transaction", "case_note", "reviewer_decision",
                 "reviewer_comment", "created_at")
    assert all(getattr(after, name) == getattr(before, name) for name in unchanged)


def test_set_priority_recomputed_is_overwritten(db_conn):
    create_case(db_conn, "CASE-1", CaseState.HUMAN_REVIEW, TRANSACTION)
    set_priority(db_conn, "CASE-1", "high")
    set_priority(db_conn, "CASE-1", "normal")
    assert get_case(db_conn, "CASE-1").priority == "normal"


@pytest.mark.parametrize("bad", ["urgent", "HIGH", "", None, 1, "high; DROP TABLE cases"])
def test_set_priority_rejects_unknown_value(db_conn, bad):
    before = create_case(db_conn, "CASE-1", CaseState.HUMAN_REVIEW, TRANSACTION)
    with pytest.raises(InvalidPriorityError):
        set_priority(db_conn, "CASE-1", bad)
    assert get_case(db_conn, "CASE-1") == before


def test_set_priority_unknown_case(db_conn):
    with pytest.raises(CaseNotFoundError):
        set_priority(db_conn, "CASE-404", "high")


def test_set_priority_touches_one_case(db_conn):
    create_case(db_conn, "CASE-1", CaseState.HUMAN_REVIEW, TRANSACTION)
    other = create_case(db_conn, "CASE-2", CaseState.HUMAN_REVIEW, TRANSACTION)
    set_priority(db_conn, "CASE-1", "high")
    assert get_case(db_conn, "CASE-1").priority == "high"
    assert get_case(db_conn, "CASE-2") == other


# --- list_all_events and secret_keys_in (J5, PR 11, decision I64) — read-only additions to n° 35 ---


def _sql_statements(conn: sqlite3.Connection, action) -> list[str]:
    """Run `action` and return every SQL statement sent to the database meanwhile."""
    seen: list[str] = []
    conn.set_trace_callback(seen.append)
    try:
        action()
    finally:
        conn.set_trace_callback(None)
    return seen


def test_list_all_events_empty(db_conn):
    assert list_all_events(db_conn) == []


def test_list_all_events_all_cases_in_order(db_conn):
    for case_id in ("CASE-1", "CASE-2", "CASE-3"):
        create_case(db_conn, case_id, CaseState.RECEIVED, TRANSACTION)
    written = [_event(c) for c in ("CASE-2", "CASE-1", "CASE-3", "CASE-1", "CASE-2")]
    ids = [append_event(db_conn, e) for e in written]

    stored = list_all_events(db_conn)
    assert [s.event_id for s in stored] == ids == sorted(ids)  # every case, by event_id
    assert [s.event for s in stored] == written  # every field round-trips


def test_list_all_events_reads_only(db_conn):
    create_case(db_conn, "CASE-1", CaseState.RECEIVED, TRANSACTION)
    append_event(db_conn, _event())
    before = db_conn.total_changes
    statements = _sql_statements(db_conn, lambda: list_all_events(db_conn))
    assert db_conn.total_changes == before
    assert statements and all(s.lstrip().upper().startswith("SELECT") for s in statements)


@pytest.mark.parametrize(
    ("details", "paths"),
    [
        ({"api_key": "x", "attempt": 1}, ["api_key"]),
        ({"request": {"headers": {"auth_token": "x"}}}, ["request.headers.auth_token"]),
        ({"calls": [{"ok": 1}, {"token": "x"}]}, ["calls[1].token"]),
    ],
)
def test_secret_keys_in_matches_append_refusal(db_conn, details, paths):
    """The export uses secret_keys_in: it must find the very paths append_event refuses."""
    create_case(db_conn, "CASE-1", CaseState.RECEIVED, TRANSACTION)
    assert secret_keys_in(details) == paths
    with pytest.raises(SecretInAuditError) as refused:
        append_event(db_conn, _event(details=details))
    assert str(paths) in str(refused.value)
    assert secret_keys_in({"prompt_tokens": 1, "idempotency_key": "CASE-1:draft"}) == []


# --- audit_export.py (n° 65, J5, PR 11 — I02, decision I64) ----------------------------------------
# Reads through audit_repository only, never writes; same number of lines as the events read.

REPO_ROOT = Path(__file__).resolve().parent.parent
EXPORT_SOURCE = REPO_ROOT / "src" / "audit" / "audit_export.py"
# An invented value: it must never show in an export nor in an error message.
INVENTED_SECRET = "sk-test-INVENTED-0000000000000000"


def _csv_rows(text: str) -> list[list[str]]:
    """Parse the CSV text (never splitlines(): a quoted cell may hold a line break)."""
    return list(csv.reader(io.StringIO(text)))


def _exported_ids(conn, fmt: str, case_id=None) -> list[int]:
    text = export_audit(conn, fmt, case_id)
    if fmt == "csv":
        return [int(row[0]) for row in _csv_rows(text)[1:]]
    return [record["event_id"] for record in json.loads(text)]


def _three_cases(conn) -> None:
    for case_id in ("CASE-1", "CASE-2", "CASE-3"):
        create_case(conn, case_id, CaseState.RECEIVED, TRANSACTION)
    for case_id in ("CASE-2", "CASE-1", "CASE-3", "CASE-1", "CASE-2", "CASE-1"):
        append_event(conn, _event(case_id))


@pytest.mark.parametrize("fmt", ["csv", "json"])
def test_audit_export_empty(db_conn, fmt):
    create_case(db_conn, "CASE-1", CaseState.RECEIVED, TRANSACTION)
    for case_id in ("CASE-1", "UNKNOWN", None):  # case without events, unknown case, empty base
        text = export_audit(db_conn, fmt, case_id)
        if fmt == "csv":
            assert _csv_rows(text) == [list(EXPORT_COLUMNS)]  # header only
        else:
            assert json.loads(text) == []


@pytest.mark.parametrize("fmt", ["csv", "json"])
def test_audit_export(db_conn, fmt):
    """Registry n° 65: the export of one case has as many lines as the events read."""
    create_case(db_conn, "CASE-1", CaseState.RECEIVED, TRANSACTION)
    for _ in range(4):
        append_event(db_conn, _event())
    read = list_events(db_conn, "CASE-1")
    assert _exported_ids(db_conn, fmt, "CASE-1") == [s.event_id for s in read]
    text = export_audit(db_conn, fmt, "CASE-1")
    count = len(_csv_rows(text)) - 1 if fmt == "csv" else len(json.loads(text))
    assert count == len(read) == 4


@pytest.mark.parametrize("fmt", ["csv", "json"])
def test_audit_export_all_cases_in_order(db_conn, fmt):
    _three_cases(db_conn)
    ids = _exported_ids(db_conn, fmt)
    assert ids == [s.event_id for s in list_all_events(db_conn)]
    assert len(ids) == 6 and all(a < b for a, b in zip(ids, ids[1:]))  # strictly increasing


@pytest.mark.parametrize("fmt", ["csv", "json"])
def test_audit_export_one_case_among_many(db_conn, fmt):
    _three_cases(db_conn)
    assert _exported_ids(db_conn, fmt, "CASE-1") == [s.event_id for s in list_events(db_conn, "CASE-1")]
    assert len(_exported_ids(db_conn, fmt, "CASE-1")) == 3


def test_audit_export_columns(db_conn):
    create_case(db_conn, "CASE-1", CaseState.RECEIVED, TRANSACTION)
    append_event(db_conn, _event())
    assert _csv_rows(export_audit(db_conn, "csv"))[0] == list(EXPORT_COLUMNS)
    record = json.loads(export_audit(db_conn, "json"))[0]
    assert list(record) == list(EXPORT_COLUMNS)
    assert record["state_from"] == "RECEIVED" and record["state_to"] == "SCORED"
    assert record["model_version"] == "rf-v1" and record["prompt_version"] is None


def test_audit_export_details_absent(db_conn):
    create_case(db_conn, "CASE-1", CaseState.RECEIVED, TRANSACTION)
    append_event(db_conn, _event(details=None, state_from=None, state_to=None))
    row = dict(zip(EXPORT_COLUMNS, _csv_rows(export_audit(db_conn, "csv"))[1]))
    assert row["details"] == "" and row["state_from"] == "" and row["prompt_version"] == ""
    record = json.loads(export_audit(db_conn, "json"))[0]
    assert record["details"] is None and record["state_from"] is None


def test_audit_export_nested_details_round_trip(db_conn):
    details = {"reasons": ["band_mismatch", "unsupported_evidence"],
               "attempt": {"number": 2, "latency_ms": 12.5, "ok": False}, "note": "élevé"}
    create_case(db_conn, "CASE-1", CaseState.RECEIVED, TRANSACTION)
    append_event(db_conn, _event(details=details))
    row = dict(zip(EXPORT_COLUMNS, _csv_rows(export_audit(db_conn, "csv"))[1]))
    assert json.loads(row["details"]) == details  # one column, valid JSON text
    assert json.loads(export_audit(db_conn, "json"))[0]["details"] == details


def test_audit_export_comma_quote_line_break(db_conn):
    tricky = 'tool:a,"b"\nc'
    details = {"reason": 'x, "y"\nz'}
    create_case(db_conn, "CASE-1", CaseState.RECEIVED, TRANSACTION)
    append_event(db_conn, _event(actor=tricky, details=details))
    append_event(db_conn, _event())
    rows = _csv_rows(export_audit(db_conn, "csv"))
    assert len(rows) == 3 and all(len(r) == len(EXPORT_COLUMNS) for r in rows)
    row = dict(zip(EXPORT_COLUMNS, rows[1]))
    assert row["actor"] == tricky and json.loads(row["details"]) == details
    assert json.loads(export_audit(db_conn, "json"))[0]["actor"] == tricky


def test_audit_export_formula_neutralised_in_csv_only(db_conn):
    """Decision Q-A: a cell a spreadsheet could run gets "'" in front (CSV only)."""
    create_case(db_conn, "CASE-1", CaseState.RECEIVED, TRANSACTION)
    for start in ("=", "+", "-", "@", "\t", "\r"):
        append_event(db_conn, _event(actor=f"{start}1+1"))
    append_event(db_conn, _event(actor="=1+1", details={"reason": "=1+1"}))
    rows = [dict(zip(EXPORT_COLUMNS, r)) for r in _csv_rows(export_audit(db_conn, "csv"))[1:]]
    assert [r["actor"][:2] for r in rows] == ["'=", "'+", "'-", "'@", "'\t", "'\r", "'="]
    assert json.loads(rows[-1]["details"]) == {"reason": "=1+1"}  # inside JSON text: not a cell start
    records = json.loads(export_audit(db_conn, "json"))
    assert records[-1]["actor"] == "=1+1" and records[-1]["details"] == {"reason": "=1+1"}


@pytest.mark.parametrize(
    ("details", "path"),
    [
        ({"isFraud": 1}, "isFraud"),
        ({"model": {"inputs": [{"isFlaggedFraud": 0}]}}, "model.inputs[0].isFlaggedFraud"),
    ],
)
@pytest.mark.parametrize("fmt", ["csv", "json"])
def test_audit_export_refuses_label(db_conn, details, path, fmt):
    # append_event accepts a label key: the export is the only barrier (I64).
    create_case(db_conn, "CASE-1", CaseState.RECEIVED, TRANSACTION)
    event_id = append_event(db_conn, _event(details=details))
    with pytest.raises(AuditExportError) as refused:
        export_audit(db_conn, fmt)
    assert str(event_id) in str(refused.value) and path in str(refused.value)


def _insert_event_raw(conn: sqlite3.Connection, details_json: str) -> int:
    """Plain SQL insert that skips append_event's checks (an old or tampered row)."""
    with conn:
        cursor = conn.execute(
            "INSERT INTO audit_events (case_id, timestamp, actor, action, result, details_json)"
            " VALUES (?, ?, ?, ?, ?, ?)",
            ("CASE-1", NOW, "system", "tool_call", "ok", details_json),
        )
    return cursor.lastrowid


@pytest.mark.parametrize("fmt", ["csv", "json"])
def test_audit_export_refuses_secret_inserted_raw(db_conn, fmt):
    create_case(db_conn, "CASE-1", CaseState.RECEIVED, TRANSACTION)
    append_event(db_conn, _event())
    event_id = _insert_event_raw(db_conn, json.dumps({"call": {"api_key": INVENTED_SECRET}}))
    with pytest.raises(AuditExportError) as refused:
        export_audit(db_conn, fmt)
    message = str(refused.value)
    assert str(event_id) in message and "call.api_key" in message
    assert INVENTED_SECRET not in message


@pytest.mark.parametrize("fmt", ["csv", "json"])
def test_secret_never_reaches_an_export(db_conn, fmt):
    """Two barriers (append_event, then the export): the secret value is never exported."""
    create_case(db_conn, "CASE-1", CaseState.RECEIVED, TRANSACTION)
    try:
        append_event(db_conn, _event(details={"token": INVENTED_SECRET}))
    except SecretInAuditError:
        pass
    try:
        text = export_audit(db_conn, fmt)
    except AuditExportError as refused:
        text = str(refused)
    assert INVENTED_SECRET not in text


def test_audit_export_allows_token_counts(db_conn):
    details = {"prompt_tokens": 120, "idempotency_key": "CASE-1:draft"}
    create_case(db_conn, "CASE-1", CaseState.RECEIVED, TRANSACTION)
    append_event(db_conn, _event(details=details))
    assert json.loads(export_audit(db_conn, "json"))[0]["details"] == details


@pytest.mark.parametrize("fmt", ["csv", "json"])
@pytest.mark.parametrize("bad", [math.nan, math.inf])
def test_audit_export_refuses_non_finite(db_conn, fmt, bad):
    """Decision Q-B: strict JSON; append_event stores NaN, the export refuses it."""
    create_case(db_conn, "CASE-1", CaseState.RECEIVED, TRANSACTION)
    event_id = append_event(db_conn, _event(details={"attempt": {"latency_ms": bad}}))
    with pytest.raises(AuditExportError) as refused:
        export_audit(db_conn, fmt)
    message = str(refused.value)
    assert str(event_id) in message and "attempt.latency_ms" in message
    assert "nan" not in message.lower() and "inf" not in message.lower()


@pytest.mark.parametrize("fmt", ["xlsx", "CSV", "", None])
def test_audit_export_unknown_format(db_conn, fmt):
    with pytest.raises(AuditExportError):
        export_audit(db_conn, fmt)


def test_label_keys_match():
    """The export keeps its own copy of the label names (registry n° 65): both must agree."""
    assert LABEL_KEYS == LABEL_COLUMNS == frozenset({"isFraud", "isFlaggedFraud"})


@pytest.mark.parametrize("fmt", ["csv", "json"])
@pytest.mark.parametrize("case_id", ["CASE-1", None])
def test_audit_export_never_writes(db_conn, fmt, case_id):
    """Decision Q-C: the export writes nothing, not even an audit event about itself."""
    _three_cases(db_conn)
    before_changes, before_events = db_conn.total_changes, len(list_all_events(db_conn))
    statements = _sql_statements(db_conn, lambda: export_audit(db_conn, fmt, case_id))
    assert db_conn.total_changes == before_changes
    assert len(list_all_events(db_conn)) == before_events
    assert statements and all(s.lstrip().upper().startswith("SELECT") for s in statements)


def test_audit_export_dependencies():
    """Registry n° 65: audit_repository.py only (+ csv, io, json, math); no file, no direct SQL."""
    tree = ast.parse(EXPORT_SOURCE.read_text(encoding="utf-8"))
    modules = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            modules.add(node.module)
    assert modules == {"__future__", "csv", "io", "json", "math", "typing",
                       "src.audit.audit_repository"}
    forbidden_calls = {"open", "append_event", "execute", "executemany", "executescript",
                       "write_text", "write_bytes", "commit"}
    called = {
        node.func.id if isinstance(node.func, ast.Name) else node.func.attr
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, (ast.Name, ast.Attribute))
    }
    assert not called & forbidden_calls


# End to end: the audit written by a real run_case (fake LLM client, small test model).

def test_audit_export_after_run_case(db_conn, tmp_path, scoring_model):
    from src.agent import orchestrator
    from src.agent.llm.fake_client import DraftFacts, FakeLLMClient
    from src.config import AppConfig, LLMSettings, Paths, RetrySettings, Secret, SplitSettings

    settings = yaml.safe_load((REPO_ROOT / "configs" / "settings.yaml").read_text(encoding="utf-8"))
    tools, llm, routing = settings["retries"]["tools"], settings["retries"]["llm"], settings["routing"]
    store = tmp_path / "evidence_store.json"
    store.write_text(json.dumps({"evidence": [
        {"case_id": "CASE-0900", "source_id": "EV-0001", "text": "Synthetic evidence."}]}),
        encoding="utf-8")
    unused = tmp_path / "unused"
    config = AppConfig(
        tool_retries=RetrySettings(max_retries=tools["max_retries"],
                                   timeout_seconds=float(tools["timeout_seconds"])),
        llm_retries=RetrySettings(max_retries=llm["max_retries_after_rejection"],
                                  timeout_seconds=float(llm["timeout_seconds"])),
        near_threshold_margin=routing["near_threshold_margin"],
        review_capacity_per_day=routing["review_capacity_per_day"],
        split=SplitSettings(seed=42, val_size=0.15, test_size=0.15),
        paths=Paths(raw_data_dir=tmp_path, runtime_db=unused, demo_cases=unused,
                    evidence_store=store, model_pipeline=unused, mlp_state=unused,
                    model_metadata=unused, metrics_dir=tmp_path, figures_dir=tmp_path,
                    prohibited_terms=REPO_ROOT / "configs" / "prohibited_terms.yaml"),
        llm=LLMSettings(provider="fake", base_url="", model="", api_key=Secret("")),
    )
    raw = {"case_id": "CASE-0900", "step": 1, "type": "TRANSFER", "amount": 181.0,
           "oldbalanceOrg": 181.0, "newbalanceOrig": 0.0, "oldbalanceDest": 0.0,
           "newbalanceDest": 0.0, "case_note": "Synthetic note."}
    outcome = orchestrator.run_case(
        raw, conn=db_conn, config=config, scoring_model=scoring_model,
        make_llm_client=lambda case_id, score, evidence: FakeLLMClient(
            "valid", DraftFacts.from_official(case_id, score, evidence)),
        clock=lambda: 0.0,
    )
    assert outcome.state is CaseState.HUMAN_REVIEW

    read = list_events(db_conn, "CASE-0900")
    assert len(read) > 5  # transitions and tool calls
    rows = _csv_rows(export_audit(db_conn, "csv", "CASE-0900"))
    records = json.loads(export_audit(db_conn, "json", "CASE-0900"))
    assert len(rows) - 1 == len(records) == len(read)
    assert [int(r[0]) for r in rows[1:]] == [rec["event_id"] for rec in records] == [
        s.event_id for s in read]
    for text in (export_audit(db_conn, "csv"), export_audit(db_conn, "json")):
        assert not any(label in text for label in LABEL_KEYS)


# --- list_cases_in_state (J5, PR 12, decision I69 (2)) — read-only addition to n° 34 --------------


def _cases_in_three_states(conn: sqlite3.Connection) -> None:
    create_case(conn, "CASE-1", CaseState.RECEIVED, TRANSACTION, "note 1")
    create_case(conn, "CASE-2", CaseState.RECEIVED, TRANSACTION)
    create_case(conn, "CASE-3", CaseState.RECEIVED, TRANSACTION)
    update_state(conn, "CASE-2", CaseState.HUMAN_REVIEW)
    update_state(conn, "CASE-3", CaseState.HUMAN_REVIEW)
    # CASE-1 stays RECEIVED; a FAILED case too:
    create_case(conn, "CASE-4", CaseState.RECEIVED, TRANSACTION)
    update_state(conn, "CASE-4", CaseState.FAILED)


def test_list_cases_in_state_returns_only_that_state(db_conn):
    _cases_in_three_states(db_conn)
    assert sorted(c.case_id for c in list_cases_in_state(db_conn, CaseState.HUMAN_REVIEW)) == [
        "CASE-2", "CASE-3"]
    assert [c.case_id for c in list_cases_in_state(db_conn, CaseState.RECEIVED)] == ["CASE-1"]
    assert [c.case_id for c in list_cases_in_state(db_conn, CaseState.FAILED)] == ["CASE-4"]


def test_list_cases_in_state_empty(db_conn):
    assert list_cases_in_state(db_conn, CaseState.HUMAN_REVIEW) == []
    _cases_in_three_states(db_conn)
    assert list_cases_in_state(db_conn, CaseState.CLOSED) == []


def test_list_cases_in_state_returns_case_records(db_conn):
    _cases_in_three_states(db_conn)
    for record in list_cases_in_state(db_conn, CaseState.HUMAN_REVIEW):
        assert record == get_case(db_conn, record.case_id)  # same record as a single read


def test_list_cases_in_state_is_read_only(db_conn):
    _cases_in_three_states(db_conn)
    before = db_conn.total_changes
    statements = _sql_statements(
        db_conn, lambda: list_cases_in_state(db_conn, CaseState.HUMAN_REVIEW))
    assert db_conn.total_changes == before
    assert statements and all(s.lstrip().upper().startswith("SELECT") for s in statements)


def test_list_cases_in_state_never_returns_a_label(db_conn):
    _cases_in_three_states(db_conn)
    for state in CaseState:
        for record in list_cases_in_state(db_conn, state):
            assert not LABEL_COLUMNS & set(record.transaction)
