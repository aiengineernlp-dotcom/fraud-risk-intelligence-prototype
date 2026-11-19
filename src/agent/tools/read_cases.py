"""
SoC layer      : 3 — Logic Engine
Responsibility : Tool read_cases: the orchestrator's only way to read SEVERAL stored cases — every
                 case in one state (case_repository.list_cases_in_state), for the review queue (J08)
Never does     : Write anything (no state, step result, priority or audit event); sort or decide a
                 priority (the orchestrator sorts with routing_policy.py constants); call the LLM;
                 retry; any financial action
Reference      : Architecture_Projet.md v1.4 — section 1.2, section 5, section 8 (n° 34; this file is
                 outside the register, to be added by the founder); Features_Complet.md J08, G11, G12;
                 PASSATION.md §6, decisions I67, I69 (1), (2)
"""

from __future__ import annotations

import sqlite3

from src.agent.domain import CaseState
from src.agent.tools.errors import ToolInputError, ToolUnavailableError
from src.storage.case_repository import CaseRecord, list_cases_in_state as _list_cases_in_state

# What this tool may change (G12 test): nothing, it only reads the cases (I69 (1)).
TOOL_EFFECT = "read_only"


def list_cases_in_state(conn: sqlite3.Connection, state: CaseState) -> list[CaseRecord]:
    """Return every stored case whose current state is `state`, in no particular order.

    Raises ToolInputError if `state` is not a CaseState, ToolUnavailableError if the database fails.
    """
    if not isinstance(state, CaseState):
        raise ToolInputError("list_cases_in_state needs a CaseState")
    try:
        return _list_cases_in_state(conn, state)
    except sqlite3.Error as error:
        raise ToolUnavailableError("The case database is unavailable") from error
