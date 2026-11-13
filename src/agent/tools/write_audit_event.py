"""
SoC layer      : 3 — Logic Engine
Responsibility : Tool write_audit_event: append one structured AuditEvent (audit_repository.py) and
                 confirm the write by returning its event_id; write one technical log line with
                 the event_id, case, action and result only
Never does     : Call the LLM; modify or delete an event (append only); put `details` or any secret
                 in the log line (secret-looking keys are refused by audit_repository.py); configure
                 logging (src/logging_setup.py does it at launch, with its secret-hiding formatter);
                 retry (retry.py, n° 62); any financial action
Reference      : Architecture_Projet.md v1.3 — section 3 (Flux 1), section 5, section 8 (n° 47),
                 section 10.2; Features_Complet.md G07, I01, G12; brief §11.4, §14;
                 PASSATION.md §6, decisions PR 3 (b), PR 5 (iii)
"""

from __future__ import annotations

import logging
import sqlite3

from src.agent.domain import AuditEvent
from src.agent.tools.errors import ToolInputError, ToolUnavailableError
from src.audit.audit_repository import append_event

# What this tool may change (G12 test): it appends audit events, nothing else.
TOOL_EFFECT = "writes_audit"

# Standard logger: its lines go through the handler set up by logging_setup.setup_logging (n° 08).
logger = logging.getLogger(__name__)


def write_audit_event(conn: sqlite3.Connection, event: AuditEvent) -> int:
    """Append `event` and return the event_id given by the database (the confirmation, G07).

    One attempt only (decision (a)). Raises ToolInputError (not an AuditEvent, secret-looking key,
    timestamp not UTC, details not JSON, unknown case) or ToolUnavailableError (the database failed).
    """
    if not isinstance(event, AuditEvent):
        raise ToolInputError("write_audit_event needs an AuditEvent")

    try:
        event_id = append_event(conn, event)
    except sqlite3.IntegrityError as error:
        # Foreign key (unknown case) or CHECK refused: the event itself is wrong.
        raise ToolInputError(f"Audit event refused by the database for {event.case_id}") from error
    except sqlite3.Error as error:
        raise ToolUnavailableError(f"Database error while auditing {event.case_id}") from error
    except (ValueError, TypeError) as error:
        # ValueError: SecretInAuditError or a timestamp that is not UTC (message names keys only,
        # never values). TypeError: `details` holds something that is not JSON.
        raise ToolInputError(f"Audit event refused for {event.case_id}: {error}") from error

    # Never `details` here: only what identifies the event.
    logger.info(
        "audit event %d written: case=%s action=%s result=%s",
        event_id, event.case_id, event.action, event.result,
    )
    return event_id
