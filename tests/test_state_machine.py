"""
SoC layer      : Tests
Responsibility : Prove that state_machine.py accepts the normal path and every transition of the
                 section 3bis table, refuses every other transition (e.g. RECEIVED -> VALIDATED)
                 with InvalidTransitionError, and never lets a case leave a terminal state
Never does     : Touch the database, the audit log or the LLM (the audit event of a refusal is
                 tested with the orchestrator, PR 3 / PR 10)
Reference      : Architecture_Projet.md v1.2 — section 3bis, section 8 (n° 43);
                 Features_Complet.md G01, G02; brief §11.3
"""

from __future__ import annotations

import itertools

import pytest

from src.agent.domain import CaseState
from src.agent.state_machine import (
    ALLOWED_TRANSITIONS,
    INITIAL_STATE,
    TERMINAL_STATES,
    InvalidTransitionError,
    check_transition,
    is_terminal,
)

# The section 3bis (v1.2, decision I45) table, written out by hand so the test does not just
# re-read the code: 15 allowed transitions.
EXPECTED_TRANSITIONS = {
    (CaseState.RECEIVED, CaseState.SCORED),
    (CaseState.SCORED, CaseState.EVIDENCE_READY),
    (CaseState.EVIDENCE_READY, CaseState.DRAFTED),
    (CaseState.DRAFTED, CaseState.VALIDATED),
    (CaseState.DRAFTED, CaseState.VALIDATION_REJECTED),
    (CaseState.VALIDATED, CaseState.HUMAN_REVIEW),
    (CaseState.HUMAN_REVIEW, CaseState.CLOSED),
    (CaseState.HUMAN_REVIEW, CaseState.ESCALATED),
    (CaseState.HUMAN_REVIEW, CaseState.NEEDS_MORE_INFORMATION),
    (CaseState.RECEIVED, CaseState.FAILED),
    (CaseState.SCORED, CaseState.FAILED),
    (CaseState.EVIDENCE_READY, CaseState.FAILED),
    (CaseState.DRAFTED, CaseState.FAILED),
    (CaseState.VALIDATED, CaseState.FAILED),
    (CaseState.HUMAN_REVIEW, CaseState.FAILED),
}

ALL_PAIRS = set(itertools.product(CaseState, repeat=2))


def test_eleven_states() -> None:
    assert len(CaseState) == 11


def test_valid_path() -> None:
    path = [
        CaseState.SCORED,
        CaseState.EVIDENCE_READY,
        CaseState.DRAFTED,
        CaseState.VALIDATED,
        CaseState.HUMAN_REVIEW,
        CaseState.CLOSED,
    ]
    state = INITIAL_STATE
    assert state is CaseState.RECEIVED
    for target in path:
        state = check_transition(state, target)
        assert state is target
    assert is_terminal(state)


def test_table_matches_section_3bis() -> None:
    assert len(EXPECTED_TRANSITIONS) == 15
    coded = {(src, dst) for src, targets in ALLOWED_TRANSITIONS.items() for dst in targets}
    assert coded == EXPECTED_TRANSITIONS


@pytest.mark.parametrize(
    ("current", "target"), sorted(EXPECTED_TRANSITIONS, key=lambda p: (p[0].value, p[1].value))
)
def test_each_allowed_transition_accepted(current: CaseState, target: CaseState) -> None:
    assert check_transition(current, target) is target


def test_invalid_transition_rejected() -> None:
    # The example of the brief §11.3.
    with pytest.raises(InvalidTransitionError) as excinfo:
        check_transition(CaseState.RECEIVED, CaseState.VALIDATED)
    assert excinfo.value.current is CaseState.RECEIVED
    assert excinfo.value.target is CaseState.VALIDATED
    assert "RECEIVED -> VALIDATED" in str(excinfo.value)

    # And every pair absent from the table (including staying in place).
    for current, target in sorted(
        ALL_PAIRS - EXPECTED_TRANSITIONS, key=lambda p: (p[0].value, p[1].value)
    ):
        with pytest.raises(InvalidTransitionError):
            check_transition(current, target)


def test_terminal_states_are_final() -> None:
    assert TERMINAL_STATES == {
        CaseState.CLOSED,
        CaseState.ESCALATED,
        CaseState.NEEDS_MORE_INFORMATION,
        CaseState.VALIDATION_REJECTED,
        CaseState.FAILED,
    }
    for terminal in TERMINAL_STATES:
        assert is_terminal(terminal)
        for target in CaseState:
            with pytest.raises(InvalidTransitionError):
                check_transition(terminal, target)
    for state in set(CaseState) - TERMINAL_STATES:
        assert not is_terminal(state)
