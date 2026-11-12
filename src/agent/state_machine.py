"""
SoC layer      : 3 — Logic Engine
Responsibility : Hold the explicit state machine of a case: the initial state, the allowed
                 transitions, the terminal states, and the refusal of any other transition
                 (InvalidTransitionError)
Never does     : Call the LLM; read or write the database; write audit events (the orchestrator
                 records the refusal); import Streamlit
Reference      : Architecture_Projet.md v1.1 — section 3bis (transition table), section 5,
                 section 8 (n° 42); Features_Complet.md G01, G02; brief §11.3
"""

from __future__ import annotations

from src.agent.domain import CaseState

# A case is created in RECEIVED once intake_case has accepted the input (section 3bis).
INITIAL_STATE = CaseState.RECEIVED

# Allowed transitions, copied from the table of Architecture_Projet.md section 3bis.
# Anything not listed here is refused.
# Decision: FAILED is reachable only from RECEIVED, SCORED, EVIDENCE_READY and DRAFTED
# (the steps that call a tool or the LLM), as in section 3bis — not from VALIDATED or
# HUMAN_REVIEW, although the brief §11.3 says "any step" (gap noted in PASSATION.md §6).
ALLOWED_TRANSITIONS: dict[CaseState, frozenset[CaseState]] = {
    CaseState.RECEIVED: frozenset({CaseState.SCORED, CaseState.FAILED}),
    CaseState.SCORED: frozenset({CaseState.EVIDENCE_READY, CaseState.FAILED}),
    CaseState.EVIDENCE_READY: frozenset({CaseState.DRAFTED, CaseState.FAILED}),
    CaseState.DRAFTED: frozenset(
        {CaseState.VALIDATED, CaseState.VALIDATION_REJECTED, CaseState.FAILED}
    ),
    # A validated draft always goes to a human (brief §11.6).
    CaseState.VALIDATED: frozenset({CaseState.HUMAN_REVIEW}),
    CaseState.HUMAN_REVIEW: frozenset(
        {CaseState.CLOSED, CaseState.ESCALATED, CaseState.NEEDS_MORE_INFORMATION}
    ),
}

# Final states: no way out (section 3bis). They are exactly the states with no entry above.
TERMINAL_STATES = frozenset(
    {
        CaseState.CLOSED,
        CaseState.ESCALATED,
        CaseState.NEEDS_MORE_INFORMATION,
        CaseState.VALIDATION_REJECTED,
        CaseState.FAILED,
    }
)


class InvalidTransitionError(Exception):
    """Raised when a transition is not in ALLOWED_TRANSITIONS (G02)."""

    def __init__(self, current: CaseState, target: CaseState) -> None:
        self.current = current
        self.target = target
        super().__init__(f"Invalid transition: {current.value} -> {target.value}")


def is_terminal(state: CaseState) -> bool:
    """True if the case can no longer change state."""
    return state in TERMINAL_STATES


def check_transition(current: CaseState, target: CaseState) -> CaseState:
    """Return `target` if current -> target is allowed; otherwise raise InvalidTransitionError.

    The caller (the orchestrator) stores the new state and writes the audit event,
    including the "invalid_transition" event when this function raises.
    """
    # A terminal state has no entry in the table, so .get() gives an empty set: refused.
    if target not in ALLOWED_TRANSITIONS.get(current, frozenset()):
        raise InvalidTransitionError(current, target)
    return target
