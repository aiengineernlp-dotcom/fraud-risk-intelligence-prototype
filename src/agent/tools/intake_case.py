"""
SoC layer      : 3 — Logic Engine
Responsibility : Tool intake_case: check the raw input of a case (case_input.py) and create the case
                 once, in the state RECEIVED (case_repository.py); a second submission of the same
                 case_id raises DuplicateSubmissionError (D-07)
Never does     : Call the LLM; retry (retry.py, n° 62); write an audit event (the orchestrator calls
                 write_audit_event); score; accept a label (isFraud, isFlaggedFraud); any financial action
Reference      : Architecture_Projet.md v1.3 — section 3 (Flux 1), section 5, section 8 (n° 44), D-07;
                 Features_Complet.md G03, G12; brief §11.4; PASSATION.md §6, decisions PR 5
"""

from __future__ import annotations

import sqlite3
from typing import Any

from src.agent.domain import CaseState
from src.agent.tools.errors import DuplicateSubmissionError, ToolInputError, ToolUnavailableError
from src.data.case_input import CaseInputError, parse_case_input
from src.storage.case_repository import (
    CaseRecord,
    DuplicateCaseError,
    LabelInCaseError,
    create_case,
)

# What this tool may change (G12 test): it creates a case row, nothing else.
TOOL_EFFECT = "writes_case"


def intake_case(conn: sqlite3.Connection, raw: Any) -> CaseRecord:
    """Check `raw` and store it as a new case in the state RECEIVED. One attempt only (decision (a)).

    Raises ToolInputError (invalid input), DuplicateSubmissionError (case already there, D-07)
    or ToolUnavailableError (the database failed).
    """
    try:
        case = parse_case_input(raw)
    except CaseInputError as error:
        raise ToolInputError(f"Invalid case input: {error}") from error

    try:
        return create_case(
            conn,
            case.case_id,
            CaseState.RECEIVED,
            case.transaction(),
            case_note=case.case_note,
        )
    except DuplicateCaseError as error:
        raise DuplicateSubmissionError(case.case_id) from error
    except LabelInCaseError as error:
        # Cannot happen after parse_case_input (labels refused there); kept as a second guard.
        raise ToolInputError(str(error)) from error
    except sqlite3.Error as error:
        # Locked or broken database: not the input's fault.
        raise ToolUnavailableError(f"Database error while creating {case.case_id}") from error
