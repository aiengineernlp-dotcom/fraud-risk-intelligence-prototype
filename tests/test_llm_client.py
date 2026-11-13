"""
SoC layer      : Tests
Responsibility : Test the LLM layer without network: the interface and errors (n° 55), the scripted
                 fake client (n° 56), the OpenAI-compatible adapter on a simulated transport (n° 57)
                 and the factory (n° 58); prove that the key never shows in an error, a repr or a log
Never does     : Open a network connection; call a real LLM; read .env or call load_config();
                 use a real key (the key below is invented)
Reference      : Architecture_Projet.md v1.3 — section 4 (D-04, D-05, D-08), section 8 (n° 55 to 59);
                 Features_Complet.md F01, F02; brief §10.5, §14; PASSATION.md §6, decisions PR 7
"""

from __future__ import annotations

import dataclasses
import json
import socket
from pathlib import Path

import pytest

from src.agent.domain import EvidenceItem, ScoreResult
from src.agent.llm.base import LLMClient, LLMError, LLMMessage, LLMResponse, LLMTimeout, LLMUnavailable
from src.agent.llm.fake_client import (
    FAKE_MODEL_NAME,
    PROHIBITED_TERM,
    SCENARIOS,
    SCORE_MISMATCH_SHIFT,
    UNSUPPORTED_SOURCE_ID,
    DraftFacts,
    FakeLLMClient,
)
from src.agent.tools.validate_investigation_json import validate_investigation_json


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    """Any real connection attempt fails the test instead of leaving the machine."""

    def refuse(*args, **kwargs):
        raise AssertionError("network access attempted in an offline test")

    monkeypatch.setattr(socket.socket, "connect", refuse)
    monkeypatch.setattr(socket, "create_connection", refuse)


# --- n° 55 base.py ------------------------------------------------------------


def test_message_and_response_are_frozen():
    message = LLMMessage(role="user", content="hello")
    response = LLMResponse(text="{}", model="m", latency_seconds=0.1, input_tokens=None, output_tokens=None)
    with pytest.raises(dataclasses.FrozenInstanceError):
        message.content = "changed"
    with pytest.raises(dataclasses.FrozenInstanceError):
        response.text = "changed"


def test_llm_client_is_abstract():
    with pytest.raises(TypeError):
        LLMClient()


def test_llm_error_family():
    timeout = LLMTimeout("LLM provider did not answer in time", kind="timeout")
    unavailable = LLMUnavailable("LLM provider error (HTTP 500)", kind="http_status", status_code=500)
    assert isinstance(timeout, LLMError) and isinstance(unavailable, LLMError)
    assert not isinstance(timeout, LLMUnavailable)
    assert (timeout.kind, timeout.status_code) == ("timeout", None)
    assert (unavailable.kind, unavailable.status_code) == ("http_status", 500)


# --- n° 56 fake_client.py -----------------------------------------------------
# Invented official facts (not the real model). The score has many decimals on purpose:
# the "valid" draft must copy it exactly (decision PR 6 (a)).
CASE_ID = "CASE-9001"
OFFICIAL = ScoreResult(score=0.8123456789, threshold=0.3, risk_band="high", model_version="test_model@2026-01-01")
EVIDENCE = [
    EvidenceItem(source_id="EV-0001", text="Transaction type: TRANSFER."),
    EvidenceItem(source_id="EV-0002", text="The amount (100.00) is 100.0% of the origin account balance."),
]
TERMS_PATH = Path(__file__).resolve().parents[1] / "configs" / "prohibited_terms.yaml"
MESSAGES = [LLMMessage(role="system", content="instructions"), LLMMessage(role="user", content="case")]


def _fake(scenario: str, score: ScoreResult = OFFICIAL, evidence=EVIDENCE) -> FakeLLMClient:
    return FakeLLMClient(scenario, DraftFacts.from_official(CASE_ID, score, evidence))


def _validate(text: str, score: ScoreResult = OFFICIAL, evidence=EVIDENCE):
    """Pass a fake draft through the real validation tool (n° 52)."""
    return validate_investigation_json(text, score, CASE_ID, evidence, TERMS_PATH)


def test_fake_scenarios_are_those_of_d05():
    assert set(SCENARIOS) == {
        "valid", "malformed", "missing_field", "score_mismatch",
        "unsupported_evidence", "prohibited_claim", "timeout",
    }


def test_fake_unknown_scenario_refused():
    with pytest.raises(ValueError, match="Unknown fake scenario"):
        _fake("polite")


def test_draft_facts_copy_the_official_values():
    facts = DraftFacts.from_official(CASE_ID, OFFICIAL, EVIDENCE)
    assert facts == DraftFacts(CASE_ID, "high", 0.8123456789, "test_model@2026-01-01", ("EV-0001", "EV-0002"))


@pytest.mark.validation_workflow
def test_fake_valid_draft_passes_the_validator():
    response = _fake("valid").complete(MESSAGES)
    result = _validate(response.text)
    assert result.passed, result.reasons
    assert response.model == FAKE_MODEL_NAME


@pytest.mark.validation_workflow
def test_fake_valid_draft_without_evidence_passes_the_validator():
    # F07: no evidence -> the draft must state an uncertainty and a review step.
    response = _fake("valid", evidence=[]).complete(MESSAGES)
    result = _validate(response.text, evidence=[])
    assert result.passed, result.reasons


def test_fake_valid_draft_copies_the_exact_score():
    draft = json.loads(_fake("valid").complete(MESSAGES).text)
    assert draft["model_score"] == OFFICIAL.score  # exact, not approximately
    assert draft["validation_status"] == "pending"


@pytest.mark.validation_workflow
@pytest.mark.parametrize(
    ("scenario", "expected_reason"),
    [
        ("malformed", "malformed JSON"),
        ("missing_field", "schema: uncertainties"),
        ("score_mismatch", "model_score"),
        ("unsupported_evidence", f"source IDs not in the supplied evidence: {UNSUPPORTED_SOURCE_ID}"),
        ("prohibited_claim", f"prohibited term '{PROHIBITED_TERM}'"),
    ],
)
def test_fake_faulty_drafts_are_rejected(scenario, expected_reason):
    result = _validate(_fake(scenario).complete(MESSAGES).text)
    assert not result.passed
    assert any(expected_reason in reason for reason in result.reasons), result.reasons


@pytest.mark.validation_workflow
@pytest.mark.parametrize("official_score", [0.0, 0.5, 0.9, 0.95, 1.0])
def test_fake_score_mismatch_stays_in_range_and_is_rejected(official_score):
    # Founder decision PR 7 (2): above 0.9 the shift is subtracted, so the wrong score stays in [0, 1].
    score = dataclasses.replace(OFFICIAL, score=official_score)
    text = _fake("score_mismatch", score=score).complete(MESSAGES).text
    wrong = json.loads(text)["model_score"]
    assert 0.0 <= wrong <= 1.0
    assert abs(wrong - official_score) == pytest.approx(SCORE_MISMATCH_SHIFT)
    assert not _validate(text, score=score).passed


def test_fake_unsupported_evidence_refuses_a_supplied_id():
    evidence = [EvidenceItem(source_id=UNSUPPORTED_SOURCE_ID, text="Transaction type: TRANSFER.")]
    with pytest.raises(ValueError):
        _fake("unsupported_evidence", evidence=evidence).complete(MESSAGES)


def test_fake_timeout_raises_at_once():
    client = _fake("timeout")
    with pytest.raises(LLMTimeout) as caught:
        client.complete(MESSAGES)
    assert caught.value.kind == "timeout"
    assert client.calls == 1


def test_fake_records_calls_without_reading_them():
    client = _fake("valid")
    client.complete(MESSAGES)
    client.complete(MESSAGES)
    assert client.calls == 2
    assert client.last_messages == tuple(MESSAGES)


@pytest.mark.parametrize("scenario", [s for s in SCENARIOS if s != "timeout"])
def test_fake_outputs_contain_no_label(scenario):
    text = _fake(scenario).complete(MESSAGES).text
    assert "isFraud" not in text and "isFlaggedFraud" not in text
