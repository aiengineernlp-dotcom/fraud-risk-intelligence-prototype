"""
SoC layer      : Tests
Responsibility : Test the inputs of the agent tools: case input checks (n° 39), approved evidence
                 store (n° 36), demo cases and evidence builder (n° 37) (started at J4, PR 4;
                 the tools n° 44 to 47 are added at PR 5)
Never does     : Load the real PaySim file or the trained model; call the network or an LLM;
                 write outside tmp_path
Reference      : Architecture_Projet.md v1.3 — section 8 (n° 48, tests of n° 36, 37, 39), D-09, D-10;
                 Features_Complet.md G05, G08, F07; PASSATION.md §6, decisions PR 4
"""

from __future__ import annotations

import pytest

from src.data.case_input import CaseInput, CaseInputError, parse_case_input


def _valid_input(**changes):
    """A valid case input (invented values); `changes` overrides or adds fields."""
    raw = {
        "case_id": "CASE-0001",
        "step": 1,
        "type": "TRANSFER",
        "amount": 181.0,
        "oldbalanceOrg": 181.0,
        "newbalanceOrig": 0.0,
        "oldbalanceDest": 0.0,
        "newbalanceDest": 0.0,
        "case_note": "Synthetic note.",
    }
    raw.update(changes)
    return raw


# --- n° 39 case_input.py ------------------------------------------------------------------------


def test_valid_input_accepted():
    case = parse_case_input(_valid_input())
    assert isinstance(case, CaseInput)
    assert case.case_id == "CASE-0001"
    assert case.transaction() == {
        "step": 1, "type": "TRANSFER", "amount": 181.0, "oldbalanceOrg": 181.0,
        "newbalanceOrig": 0.0, "oldbalanceDest": 0.0, "newbalanceDest": 0.0,
    }


def test_case_note_is_optional_and_unbounded():
    raw = _valid_input()
    del raw["case_note"]
    assert parse_case_input(raw).case_note is None
    assert parse_case_input(_valid_input(case_note=None)).case_note is None
    long_note = "x" * 100_000  # no length limit (founder decision, PR 4, Q2)
    assert parse_case_input(_valid_input(case_note=long_note)).case_note == long_note


def test_integer_amount_becomes_float():
    case = parse_case_input(_valid_input(amount=181))
    assert case.amount == 181.0 and isinstance(case.amount, float)


def _without(field):
    raw = _valid_input()
    del raw[field]
    return raw


@pytest.mark.parametrize(
    ("raw", "field_in_message"),
    [
        (["not", "a", "dict"], "dict"),
        (_valid_input(case_id="CASE-1"), "case_id"),
        (_valid_input(case_id="case-0001"), "case_id"),
        (_valid_input(case_id="CASE-00012"), "case_id"),
        (_valid_input(case_id=1), "case_id"),
        (_without("amount"), "amount"),
        (_without("case_id"), "case_id"),
        (_valid_input(extra_field=1), "extra_field"),
        (_valid_input(nameOrig="C123"), "nameOrig"),
        (_valid_input(nameDest="C456"), "nameDest"),
        (_valid_input(step=1.5), "step"),
        (_valid_input(step="1"), "step"),
        (_valid_input(step=True), "step"),
        (_valid_input(amount="181"), "amount"),
        (_valid_input(amount=True), "amount"),
        (_valid_input(amount=float("nan")), "amount"),
        (_valid_input(amount=float("inf")), "amount"),
        (_valid_input(amount=-1.0), "amount"),
        (_valid_input(oldbalanceDest=-0.01), "oldbalanceDest"),
        (_valid_input(type="WIRE"), "type"),
        (_valid_input(type=3), "type"),
        (_valid_input(case_note=42), "case_note"),
    ],
)
def test_invalid_input_rejected(raw, field_in_message):
    with pytest.raises(CaseInputError, match=field_in_message):
        parse_case_input(raw)


@pytest.mark.parametrize("label", ["isFraud", "isFlaggedFraud"])
def test_label_in_case_input_rejected(label):
    with pytest.raises(CaseInputError, match="Labels are not allowed"):
        parse_case_input(_valid_input(**{label: 0}))


def test_case_input_is_read_only():
    case = parse_case_input(_valid_input())
    with pytest.raises(AttributeError):
        case.amount = 0.0  # frozen dataclass
