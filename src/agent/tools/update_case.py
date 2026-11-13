"""
SoC layer      : 3 — Logic Engine
Responsibility : Tool update_case: the ONLY way the orchestrator reads or changes a stored case —
                 state (checked by state_machine.py, then update_state), step result
                 (save_step_result, D-07) and priority (set_priority) (Q-28, decision PR 10 (a))
Never does     : Call the LLM; retry (never wrapped in retry.py: it writes); decide a transition,
                 a priority or a score; write an audit event (the orchestrator calls
                 write_audit_event); delete anything; any financial action
Reference      : Architecture_Projet.md v1.3 — section 3bis, section 5 ("écrire en base sans passer
                 par un outil" forbidden to layer 4), section 10.2; Features_Complet.md G01, G10, G12;
                 PASSATION.md §6, Q-28, Q-30 (tool outside the register, accepted), decisions PR 10
"""

from __future__ import annotations

import sqlite3
from typing import Any

from src.agent.domain import CaseState
from src.agent.state_machine import check_transition
from src.agent.tools.errors import ToolInputError, ToolUnavailableError
from src.storage import case_repository
from src.storage.case_repository import (
    CaseNotFoundError,
    CaseRecord,
    InvalidPriorityError,
    StepResult,
)

# What this tool may change (G12 test): the state, step results and priority of an existing case.
TOOL_EFFECT = "writes_case"


def get_case(conn: sqlite3.Connection, case_id: str) -> CaseRecord | None:
    """Return the stored case, or None if it does not exist."""
    try:
        return case_repository.get_case(conn, case_id)
    except sqlite3.Error as error:
        raise ToolUnavailableError("The case database is unavailable") from error


def get_step(conn: sqlite3.Connection, case_id: str, step: str) -> StepResult | None:
    """Return the stored result of a step, or None if the step was never stored (G10)."""
    try:
        return case_repository.get_step_result(conn, case_id, step)
    except sqlite3.Error as error:
        raise ToolUnavailableError("The case database is unavailable") from error


def transition_case(conn: sqlite3.Connection, case_id: str, target: CaseState) -> CaseState:
    """Move the case to `target` if state_machine.py allows it; return the PREVIOUS state.

    The transition is checked BEFORE anything is written: a refused transition raises
    InvalidTransitionError (unchanged, the orchestrator audits it) and the state stays as it was.
    Raises ToolInputError (unknown case, target not a CaseState) or ToolUnavailableError (database).
    """
    if not isinstance(target, CaseState):
        raise ToolInputError("transition_case needs a CaseState target")
    case = get_case(conn, case_id)
    if case is None:
        raise ToolInputError(f"Unknown case: {case_id}")

    check_transition(case.state, target)  # raises InvalidTransitionError: nothing written

    try:
        case_repository.update_state(conn, case_id, target)
    except CaseNotFoundError as error:
        raise ToolInputError(f"Unknown case: {case_id}") from error
    except sqlite3.Error as error:
        raise ToolUnavailableError("The case database is unavailable") from error
    return case.state


def save_step(
    conn: sqlite3.Connection,
    case_id: str,
    step: str,
    result: dict[str, Any],
    attempts: int,
) -> tuple[StepResult, bool]:
    """Store a step result once (key "{case_id}:{step}", D-07); return (stored result, created).

    A step already stored is returned as it is, with created=False: never a second score or draft.
    """
    try:
        return case_repository.save_step_result(conn, case_id, step, result, attempts)
    except sqlite3.IntegrityError as error:
        # Unknown case (foreign key), unknown step or attempts < 1 (CHECK): a caller mistake.
        raise ToolInputError(f"Step result refused for case {case_id}, step {step}") from error
    except sqlite3.Error as error:
        raise ToolUnavailableError("The case database is unavailable") from error


def set_case_priority(conn: sqlite3.Connection, case_id: str, priority: str) -> None:
    """Store the priority already decided by routing_policy.py; decide nothing."""
    try:
        case_repository.set_priority(conn, case_id, priority)
    except (InvalidPriorityError, CaseNotFoundError) as error:
        raise ToolInputError(f"Priority refused for case {case_id}") from error
    except sqlite3.Error as error:
        raise ToolUnavailableError("The case database is unavailable") from error
