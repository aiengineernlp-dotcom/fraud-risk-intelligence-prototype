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
import logging
import socket
import traceback
from pathlib import Path

import httpx2
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
from src.agent.llm.openai_compatible_client import OpenAICompatibleClient
from src.agent.tools.validate_investigation_json import validate_investigation_json
from src.config import LLMSettings, Secret


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


# --- n° 57 openai_compatible_client.py (simulated transport, never the network) ---------------
# Invented key: it only has to be recognisable in a text. Never a real key.
FAKE_KEY = "sk-test-NOT-A-REAL-KEY-0000"
SETTINGS = LLMSettings(
    provider="openai_compatible",
    base_url="http://llm.invalid/v1",  # .invalid: a domain that can never resolve
    model="test-model",
    api_key=Secret(FAKE_KEY),
)
TIMEOUT = 7.5  # invented for the tests (the real value comes from settings.yaml through the factory)


class Transport:
    """A simulated HTTP transport: counts the calls and answers with the handler given."""

    def __init__(self, handler):
        self.handler = handler
        self.requests = []

    def __call__(self, request):
        self.requests.append(request)
        return self.handler(request)

    def client(self):
        return httpx2.Client(transport=httpx2.MockTransport(self))


def _ok_body(content="{\"draft\": true}"):
    return {
        "id": "cmpl-1", "object": "chat.completion", "created": 0, "model": "test-model",
        "choices": [{"index": 0, "finish_reason": "stop",
                     "message": {"role": "assistant", "content": content}}],
        "usage": {"prompt_tokens": 11, "completion_tokens": 7, "total_tokens": 18},
    }


def _adapter(handler, settings: LLMSettings = SETTINGS) -> tuple[OpenAICompatibleClient, Transport]:
    transport = Transport(handler)
    return OpenAICompatibleClient(settings, timeout_seconds=TIMEOUT, http_client=transport.client()), transport


def _echo_key_401(request):
    # Worst case: the provider copies the key into its error message (seen on openai 3.45.0).
    return httpx2.Response(401, json={"error": {"message": f"Incorrect API key provided: {FAKE_KEY}"}})


def _raise_timeout(request):
    raise httpx2.ReadTimeout("simulated timeout", request=request)


def _raise_connect_error(request):
    raise httpx2.ConnectError("simulated refused connection", request=request)


def test_adapter_returns_the_reply_with_tokens_and_latency():
    adapter, transport = _adapter(lambda request: httpx2.Response(200, json=_ok_body("hello")))
    response = adapter.complete(MESSAGES)
    assert response.text == "hello"
    assert (response.model, response.input_tokens, response.output_tokens) == ("test-model", 11, 7)
    assert response.latency_seconds >= 0
    assert len(transport.requests) == 1


def test_adapter_sends_the_messages_and_the_model():
    adapter, transport = _adapter(lambda request: httpx2.Response(200, json=_ok_body()))
    adapter.complete(MESSAGES)
    body = json.loads(transport.requests[0].content)
    assert body["model"] == "test-model"
    assert body["messages"] == [{"role": "system", "content": "instructions"}, {"role": "user", "content": "case"}]
    # Q-22: no model parameter set for now.
    assert set(body) == {"model", "messages"}


def test_adapter_passes_the_delay_to_the_sdk_with_no_sdk_retry():
    adapter, _ = _adapter(lambda request: httpx2.Response(200, json=_ok_body()))
    assert adapter.timeout_seconds == TIMEOUT
    assert adapter._client.timeout == TIMEOUT
    assert adapter._client.max_retries == 0


@pytest.mark.parametrize(
    ("handler", "error_class", "kind", "status_code"),
    [
        (_raise_timeout, LLMTimeout, "timeout", None),
        (_raise_connect_error, LLMUnavailable, "connection", None),
        (lambda request: httpx2.Response(429, json={"error": {"message": "slow down"}}),
         LLMUnavailable, "rate_limited", 429),
        (_echo_key_401, LLMUnavailable, "auth", 401),
        (lambda request: httpx2.Response(403, json={"error": {"message": "forbidden"}}),
         LLMUnavailable, "auth", 403),
        (lambda request: httpx2.Response(500, json={"error": {"message": "boom"}}),
         LLMUnavailable, "http_status", 500),
        (lambda request: httpx2.Response(200, json=_ok_body("")), LLMUnavailable, "empty_response", None),
        (lambda request: httpx2.Response(200, json=_ok_body("   ")), LLMUnavailable, "empty_response", None),
        (lambda request: httpx2.Response(200, json={**_ok_body(), "choices": []}),
         LLMUnavailable, "empty_response", None),
    ],
)
def test_adapter_failures_become_named_errors_after_one_single_call(handler, error_class, kind, status_code):
    adapter, transport = _adapter(handler)
    with pytest.raises(error_class) as caught:
        adapter.complete(MESSAGES)
    assert (caught.value.kind, caught.value.status_code) == (kind, status_code)
    assert len(transport.requests) == 1  # max_retries=0: the SDK never tried again


@pytest.mark.parametrize("handler", [_echo_key_401, _raise_timeout, _raise_connect_error])
def test_adapter_error_is_not_chained_to_the_sdk_exception(handler):
    # Founder decision PR 7 (1): the LLMError is raised outside the except block.
    adapter, _ = _adapter(handler)
    with pytest.raises(LLMError) as caught:
        adapter.complete(MESSAGES)
    assert caught.value.__cause__ is None
    assert caught.value.__context__ is None


def test_key_never_shows_in_error_traceback_repr_or_log(caplog):
    adapter, transport = _adapter(_echo_key_401)
    caplog.set_level(logging.DEBUG)
    with pytest.raises(LLMError) as caught:
        adapter.complete(MESSAGES)
    # The test means something: the key really was sent, and the server really echoed it.
    assert transport.requests[0].headers["authorization"] == f"Bearer {FAKE_KEY}"
    error = caught.value
    traceback_text = "".join(traceback.format_exception(type(error), error, error.__traceback__))
    for text in (str(error), repr(error), traceback_text, repr(adapter), str(adapter), caplog.text):
        assert FAKE_KEY not in text
    assert "LLM provider refused the credentials (HTTP 401)" == str(error)


def test_key_never_shows_in_a_successful_call_log_or_reply(caplog):
    # A server that copies the key into its answer: the reply is redacted too.
    adapter, _ = _adapter(lambda request: httpx2.Response(200, json=_ok_body(f"key is {FAKE_KEY}")))
    caplog.set_level(logging.DEBUG)
    response = adapter.complete(MESSAGES)
    assert FAKE_KEY not in response.text
    assert FAKE_KEY not in caplog.text
    assert FAKE_KEY not in repr(response)


def test_adapter_repr_hides_key_and_base_url():
    settings = dataclasses.replace(SETTINGS, base_url="http://user:password@llm.invalid/v1")
    adapter, _ = _adapter(lambda request: httpx2.Response(200, json=_ok_body()), settings)
    assert repr(adapter) == "OpenAICompatibleClient(model='test-model')"


@pytest.mark.parametrize(
    ("field", "value", "name"),
    [("base_url", "", "LLM_BASE_URL"), ("model", "", "LLM_MODEL"), ("api_key", Secret(""), "LLM_API_KEY")],
)
def test_adapter_refuses_missing_settings_by_name_only(field, value, name):
    with pytest.raises(ValueError, match=name) as caught:
        OpenAICompatibleClient(dataclasses.replace(SETTINGS, **{field: value}), timeout_seconds=TIMEOUT)
    assert FAKE_KEY not in str(caught.value)


@pytest.mark.parametrize("timeout_seconds", [0, -1])
def test_adapter_refuses_a_non_positive_delay(timeout_seconds):
    with pytest.raises(ValueError, match="timeout_seconds"):
        OpenAICompatibleClient(SETTINGS, timeout_seconds=timeout_seconds)
