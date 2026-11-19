"""
SoC layer      : 3 — Logic Engine
Responsibility : Tool read_audit: the orchestrator's only way to read the audit trail (I67, option B)
                 — the events of one case or of every case, checked like an export (no label, no
                 secret-looking key, no non-finite number: audit_export.check_events), and the
                 CSV / JSON export text (audit_export.export_audit, n° 65)
Never does     : Write anything (not even an audit event about the read); show a refused value in an
                 error message; read the database other than through audit_export.py; call the LLM;
                 retry (a refused audit gives the same refusal every time); any financial action
Reference      : Architecture_Projet.md v1.4 — section 1.2, section 5, section 8 (n° 35, n° 65; this
                 file is outside the register, to be added by the founder); Features_Complet.md I02,
                 J06, G12; PASSATION.md §6, decisions I64, I67, I69 (1), (7)
"""

from __future__ import annotations

import sqlite3

from src.agent.tools.errors import ToolInputError, ToolUnavailableError
from src.audit.audit_export import AuditExportError, check_events, export_audit, read_audit
from src.audit.audit_repository import StoredAuditEvent

# What this tool may change (G12 test): nothing, it only reads the audit trail (I69 (1)).
TOOL_EFFECT = "read_only"


def read_events(conn: sqlite3.Connection, case_id: str | None = None) -> list[StoredAuditEvent]:
    """Return the audit events of `case_id` (or of every case if None), in event_id order.

    The events go through the same check as an export (I69 (7)): one event with a label key, a
    secret-looking key or a non-finite number refuses the whole read. An unknown case gives [].
    Raises ToolInputError for a refused read, ToolUnavailableError if the database fails.
    """
    try:
        events = read_audit(conn, case_id)
        check_events(events)
    except AuditExportError as error:
        # The message names the event_id and key paths only, never a value (n° 65). Same input,
        # same refusal: ToolInputError is never retried (retry.py).
        raise ToolInputError(str(error)) from None
    except sqlite3.Error as error:
        raise ToolUnavailableError("The audit database is unavailable") from error
    return events


def export_events(conn: sqlite3.Connection, fmt: str, case_id: str | None = None) -> str:
    """Return the audit of `case_id` (or of every case if None) as CSV or JSON text (I02).

    Raises ToolInputError for an unknown format or a refused export, ToolUnavailableError if the
    database fails.
    """
    try:
        return export_audit(conn, fmt, case_id)
    except AuditExportError as error:
        raise ToolInputError(str(error)) from None
    except sqlite3.Error as error:
        raise ToolUnavailableError("The audit database is unavailable") from error
