"""
SoC layer      : Tests
Responsibility : Test the bounded retries (retry.py, n° 62) and the review routing policy
                 (routing_policy.py, n° 54) — the orchestrator itself (n° 63) comes at PR 10
Never does     : Open a network connection; call a real LLM; read .env or call load_config()
                 (the retry values are read from configs/settings.yaml with yaml.safe_load);
                 sleep (a simulated clock measures the attempts)
Reference      : Architecture_Projet.md v1.3 — section 3 (Flux 2a, 2b), section 4 (D-07, D-08),
                 section 8 (n° 54, 62, 64); Features_Complet.md G09, G11, H06; brief §11.3, §11.6,
                 §14; PASSATION.md §6, decisions PR 5 (a), PR 7 (4), PR 9 (a)-(d)
"""

from __future__ import annotations

import ast
import math
from pathlib import Path

import pytest
import yaml

from src.agent.domain import AuditEvent, CaseState, EvidenceItem, ScoreResult
from src.agent.llm.base import LLMMessage, LLMTimeout, LLMUnavailable
from src.agent.llm.fake_client import DraftFacts, FakeLLMClient
from src.agent.retry import (
    ERROR_TOO_SLOW,
    RESULT_FAILED,
    RESULT_OK,
    RESULT_REJECTED,
    RESULT_TIMEOUT,
    AttemptRecord,
    run_with_retries,
)
from src.agent.routing_policy import (
    PRIORITIES,
    PRIORITY_HIGH,
    PRIORITY_NORMAL,
    REASON_HIGH_BAND,
    REASON_NEAR_THRESHOLD,
    REASON_NO_EVIDENCE,
    route_case,
)
from src.agent.tools.errors import DuplicateSubmissionError, ToolInputError, ToolUnavailableError
from src.agent.tools.validate_investigation_json import validate_investigation_json
from src.agent.tools.write_audit_event import write_audit_event
from src.audit.audit_repository import list_events
from src.config import RetrySettings
from src.models.risk_bands import risk_band
from src.storage.case_repository import create_case, utc_now

REPO_ROOT = Path(__file__).resolve().parent.parent
SETTINGS_PATH = REPO_ROOT / "configs" / "settings.yaml"
TERMS_PATH = REPO_ROOT / "configs" / "prohibited_terms.yaml"
RETRY_SOURCE = REPO_ROOT / "src" / "agent" / "retry.py"

# An invented key: it must never show in an attempt record.
FAKE_KEY = "sk-test-INVENTED-0000000000000000"


# --- helpers -----------------------------------------------------------------------------------

def _settings_yaml() -> dict:
    """settings.yaml read directly (never load_config(), which would load .env)."""
    with SETTINGS_PATH.open(encoding="utf-8") as handle:
        return yaml.safe_load(handle)


@pytest.fixture
def tool_settings() -> RetrySettings:
    tools = _settings_yaml()["retries"]["tools"]
    return RetrySettings(max_retries=tools["max_retries"], timeout_seconds=float(tools["timeout_seconds"]))


@pytest.fixture
def llm_settings() -> RetrySettings:
    llm = _settings_yaml()["retries"]["llm"]
    # One budget for rejections and LLM failures: a single value in settings.yaml (decision PR 9).
    return RetrySettings(max_retries=llm["max_retries_after_rejection"],
                         timeout_seconds=float(llm["timeout_seconds"]))


class Recorder:
    """A stand-in audit function: keeps every record it is given."""

    def __init__(self) -> None:
        self.records: list[AttemptRecord] = []

    def __call__(self, record: AttemptRecord) -> None:
        self.records.append(record)

    @property
    def results(self) -> list[str]:
        return [record.result for record in self.records]


class Scripted:
    """A callable that raises or returns the next item of its script, and counts its calls."""

    def __init__(self, *script) -> None:
        self.script = list(script)
        self.calls = 0

    def __call__(self):
        self.calls += 1
        item = self.script.pop(0)
        if isinstance(item, Exception):
            raise item
        return item


class FakeClock:
    """Returns the given times one after the other (two readings per attempt: start, end)."""

    def __init__(self, *times: float) -> None:
        self.times = list(times)

    def __call__(self) -> float:
        return self.times.pop(0)


def _official() -> tuple[ScoreResult, list[EvidenceItem]]:
    # Invented test facts; the band is the one the validator will compare with.
    score = ScoreResult(score=0.8123456789012345, threshold=0.3, risk_band="high",
                        model_version="test_logistic@2026-11-13")
    evidence = [EvidenceItem(source_id="EV-0001", text="Invented evidence for the test.")]
    return score, evidence


def _draft_check(score: ScoreResult, evidence: list[EvidenceItem]):
    """The `check` the orchestrator will pass: it calls the real validator tool, never judges itself."""
    def check(response) -> tuple[str, ...]:
        result = validate_investigation_json(response.text, score, "CASE-T1", evidence, TERMS_PATH)
        return () if result.passed else result.reasons
    return check


# --- retry.py (n° 62) --------------------------------------------------------------------------

def test_success_first_attempt(tool_settings):
    audit, call = Recorder(), Scripted("value")
    outcome = run_with_retries("score", call, settings=tool_settings, audit=audit)
    assert outcome.ok and outcome.value == "value" and outcome.attempts == 1
    assert call.calls == 1
    assert audit.results == [RESULT_OK]


def test_unavailable_then_success(tool_settings):
    audit, call = Recorder(), Scripted(ToolUnavailableError("down"), "value")
    outcome = run_with_retries("evidence", call, settings=tool_settings, audit=audit)
    assert outcome.ok and outcome.value == "value" and outcome.attempts == 2
    assert audit.results == [RESULT_FAILED, RESULT_OK]
    assert audit.records[0].error == "ToolUnavailableError"


@pytest.mark.parametrize("max_retries", ["from_settings", 0])
def test_tool_retries_are_bounded(tool_settings, max_retries):
    settings = tool_settings if max_retries == "from_settings" else RetrySettings(0, tool_settings.timeout_seconds)
    expected = 1 + settings.max_retries
    audit = Recorder()
    call = Scripted(*[ToolUnavailableError("down") for _ in range(expected + 5)])
    outcome = run_with_retries("evidence", call, settings=settings, audit=audit)
    assert call.calls == expected
    assert not outcome.ok and outcome.value is None and outcome.cause == RESULT_FAILED
    assert outcome.attempts == expected
    assert [r.attempt for r in audit.records] == list(range(1, expected + 1))
    assert all(r.max_attempts == expected for r in audit.records)


def test_input_error_never_retried(tool_settings):
    original = ToolInputError("bad input")
    audit, call = Recorder(), Scripted(original, "never reached")
    with pytest.raises(ToolInputError) as raised:
        run_with_retries("score", call, settings=tool_settings, audit=audit)
    assert raised.value is original
    assert call.calls == 1
    assert audit.results == [RESULT_FAILED]
    assert audit.records[0].error == "ToolInputError"


def test_duplicate_submission_never_retried(tool_settings):
    original = DuplicateSubmissionError("CASE-T1")
    audit, call = Recorder(), Scripted(original, "never reached")
    with pytest.raises(DuplicateSubmissionError) as raised:
        run_with_retries("intake", call, settings=tool_settings, audit=audit)
    assert raised.value is original and raised.value.case_id == "CASE-T1"
    assert call.calls == 1
    assert audit.results == [RESULT_FAILED]


@pytest.mark.parametrize("status_code", [401, 403])
def test_llm_auth_never_retried(llm_settings, status_code):
    original = LLMUnavailable("LLM provider refused the credentials", kind="auth", status_code=status_code)
    audit, call = Recorder(), Scripted(original, "never reached")
    with pytest.raises(LLMUnavailable) as raised:
        run_with_retries("draft", call, settings=llm_settings, audit=audit)
    assert raised.value is original
    assert call.calls == 1
    assert audit.results == [RESULT_FAILED]
    assert audit.records[0].error == "llm:auth"


def test_other_llm_errors_are_retried(llm_settings):
    audit = Recorder()
    call = Scripted(LLMUnavailable("rate limited", kind="rate_limited", status_code=429), "reply")
    outcome = run_with_retries("draft", call, settings=llm_settings, audit=audit)
    assert outcome.ok and call.calls == 2
    assert audit.records[0].error == "llm:rate_limited"


def test_llm_timeout_retried_then_exhausted(llm_settings):
    score, evidence = _official()
    fake = FakeLLMClient("timeout", DraftFacts.from_official("CASE-T1", score, evidence))
    messages = [LLMMessage("system", "s"), LLMMessage("user", "u")]
    audit = Recorder()
    outcome = run_with_retries("draft", lambda: fake.complete(messages), settings=llm_settings, audit=audit)
    assert fake.calls == 1 + llm_settings.max_retries
    assert not outcome.ok and outcome.value is None and outcome.cause == RESULT_TIMEOUT
    assert audit.results == [RESULT_TIMEOUT] * (1 + llm_settings.max_retries)
    assert all(r.error == "llm:timeout" for r in audit.records)


def test_slow_success_counts_as_timeout(tool_settings):
    limit = tool_settings.timeout_seconds
    # Attempt 1 lasts just over the limit, attempt 2 well under it.
    clock = FakeClock(0.0, limit + 0.001, 100.0, 100.0 + limit / 2)
    audit, call = Recorder(), Scripted("late value", "value")
    outcome = run_with_retries("score", call, settings=tool_settings, audit=audit, clock=clock)
    assert outcome.ok and outcome.value == "value" and outcome.attempts == 2
    assert audit.results == [RESULT_TIMEOUT, RESULT_OK]
    assert audit.records[0].error == ERROR_TOO_SLOW


def test_slow_success_every_time_is_exhausted(tool_settings):
    limit = tool_settings.timeout_seconds
    attempts = 1 + tool_settings.max_retries
    times = []
    for i in range(attempts):
        times += [10.0 * i, 10.0 * i + limit + 1.0]
    audit, call = Recorder(), Scripted(*["late"] * attempts)
    outcome = run_with_retries("score", call, settings=tool_settings, audit=audit, clock=FakeClock(*times))
    assert not outcome.ok and outcome.value is None and outcome.cause == RESULT_TIMEOUT
    assert call.calls == attempts


def test_max_delay_recorded(tool_settings, db_conn):
    """Registry test (decision PR 5 (a)): each attempt records its duration and the maximum delay."""
    create_case(db_conn, "CASE-T1", CaseState.EVIDENCE_READY, {"amount": 1.0})

    def audit(record: AttemptRecord) -> None:
        # What the orchestrator (PR 10) will do: one audit event per attempt, through tool n° 47.
        write_audit_event(db_conn, AuditEvent(
            case_id="CASE-T1", timestamp=utc_now(), actor="system", action="retry",
            result=record.result, details=record.details(),
        ))

    limit = tool_settings.timeout_seconds
    clock = FakeClock(0.0, limit + 0.5, 50.0, 50.25)
    call = Scripted("late", "value")
    outcome = run_with_retries("evidence", call, settings=tool_settings, audit=audit, clock=clock)
    assert outcome.ok

    events = list_events(db_conn, "CASE-T1")
    assert [e.event.result for e in events] == [RESULT_TIMEOUT, RESULT_OK]
    details = [e.event.details for e in events]
    assert details[0]["duration_seconds"] == pytest.approx(limit + 0.5)
    assert details[1]["duration_seconds"] == pytest.approx(0.25)
    assert all(d["timeout_seconds"] == limit for d in details)
    assert [d["attempt"] for d in details] == [1, 2]


@pytest.mark.validation_workflow
def test_rejected_draft_retried_then_exhausted(llm_settings):
    score, evidence = _official()
    fake = FakeLLMClient("prohibited_claim", DraftFacts.from_official("CASE-T1", score, evidence))
    messages = [LLMMessage("system", "s"), LLMMessage("user", "u")]
    audit = Recorder()
    outcome = run_with_retries("draft", lambda: fake.complete(messages), settings=llm_settings,
                               audit=audit, check=_draft_check(score, evidence))
    attempts = 1 + llm_settings.max_retries
    assert fake.calls == attempts
    assert not outcome.ok and outcome.cause == RESULT_REJECTED
    assert outcome.value is None  # no rejected draft is handed back as trusted (H06)
    assert outcome.last_reasons and any("definitely" in reason for reason in outcome.last_reasons)
    assert audit.results == [RESULT_REJECTED] * attempts
    assert all(r.reasons for r in audit.records)


@pytest.mark.validation_workflow
def test_rejected_then_valid_draft(llm_settings):
    score, evidence = _official()
    facts = DraftFacts.from_official("CASE-T1", score, evidence)
    clients = iter([FakeLLMClient("malformed", facts), FakeLLMClient("valid", facts)])
    messages = [LLMMessage("system", "s"), LLMMessage("user", "u")]
    audit = Recorder()
    outcome = run_with_retries("draft", lambda: next(clients).complete(messages), settings=llm_settings,
                               audit=audit, check=_draft_check(score, evidence))
    assert outcome.ok and outcome.attempts == 2
    assert audit.results == [RESULT_REJECTED, RESULT_OK]
    assert audit.records[1].reasons == ()


def test_attempt_record_never_copies_error_text(llm_settings):
    audit = Recorder()
    call = Scripted(ToolUnavailableError(f"store failed with key {FAKE_KEY}"),
                    LLMTimeout(f"timeout {FAKE_KEY}", kind="timeout"),
                    LLMUnavailable(f"refused {FAKE_KEY}", kind="auth", status_code=401))
    with pytest.raises(LLMUnavailable):
        run_with_retries("draft", call, settings=llm_settings, audit=audit)
    assert len(audit.records) == 3
    for record in audit.records:
        assert FAKE_KEY not in repr(record)
        assert FAKE_KEY not in repr(record.details())


def test_unexpected_error_not_retried(tool_settings):
    audit, call = Recorder(), Scripted(RuntimeError("bug"), "never reached")
    with pytest.raises(RuntimeError):
        run_with_retries("score", call, settings=tool_settings, audit=audit)
    assert call.calls == 1


@pytest.mark.parametrize("settings", [
    RetrySettings(max_retries=-1, timeout_seconds=5.0),
    RetrySettings(max_retries=True, timeout_seconds=5.0),
    RetrySettings(max_retries=2, timeout_seconds=0.0),
    RetrySettings(max_retries=2, timeout_seconds=float("nan")),
])
def test_bad_retry_settings_refused(settings):
    call = Scripted("value")
    with pytest.raises(ValueError):
        run_with_retries("score", call, settings=settings, audit=Recorder())
    assert call.calls == 0


def test_retry_has_no_thread_nor_sleep():
    tree = ast.parse(RETRY_SOURCE.read_text(encoding="utf-8"))
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported |= {alias.name.split(".")[0] for alias in node.names}
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[0])
    assert not imported & {"threading", "concurrent", "signal", "asyncio", "multiprocessing"}
    called = {node.func.attr for node in ast.walk(tree)
              if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)}
    assert "sleep" not in called


# --- routing_policy.py (n° 54) -----------------------------------------------------------------

ROUTING_SOURCE = REPO_ROOT / "src" / "agent" / "routing_policy.py"
EVIDENCE = [EvidenceItem(source_id="EV-0001", text="Invented evidence for the test.")]


@pytest.fixture
def margin() -> float:
    """routing.near_threshold_margin from settings.yaml (I08), never a value written in the test."""
    return float(_settings_yaml()["routing"]["near_threshold_margin"])


@pytest.fixture
def test_model_facts(scoring_model_files) -> tuple[float, dict]:
    """Threshold and band bounds of the small test model (invented for the tests, conftest.py)."""
    written = scoring_model_files["written"]
    return written["threshold"], written["risk_band_bounds"]


def _score(value: float, threshold: float, bounds: dict) -> ScoreResult:
    # The band is computed by the real risk_bands.py, as score_transaction.py does.
    return ScoreResult(score=value, threshold=threshold, risk_band=risk_band(value, bounds),
                       model_version="test_logistic@2026-11-13")


@pytest.mark.parametrize("case", [
    "high_band",
    "at_lower_bound",
    "just_below_lower_bound",
    "just_below_threshold",
    "at_threshold_medium_band",
    "low_band_far_from_threshold",
])
def test_review_priority(case, margin, test_model_facts):
    """Registry test: high band or score close to the threshold -> "high"; otherwise "normal"."""
    threshold, bounds = test_model_facts
    lower = threshold - margin
    value, expected_priority, expected_reasons = {
        "high_band": (bounds["high"], PRIORITY_HIGH, (REASON_HIGH_BAND,)),
        "at_lower_bound": (lower, PRIORITY_HIGH, (REASON_NEAR_THRESHOLD,)),
        "just_below_lower_bound": (math.nextafter(lower, 0.0), PRIORITY_NORMAL, ()),
        "just_below_threshold": (math.nextafter(threshold, 0.0), PRIORITY_HIGH, (REASON_NEAR_THRESHOLD,)),
        "at_threshold_medium_band": (threshold, PRIORITY_NORMAL, ()),
        "low_band_far_from_threshold": (lower / 2, PRIORITY_NORMAL, ()),
    }[case]
    decision = route_case(_score(value, threshold, bounds), EVIDENCE, margin)
    assert decision.priority == expected_priority
    assert decision.reasons == expected_reasons
    assert decision.request_information is False
    assert decision.priority in PRIORITIES


def test_review_priority_missing_evidence(margin, test_model_facts):
    threshold, bounds = test_model_facts
    decision = route_case(_score(threshold, threshold, bounds), [], margin)
    assert decision.priority == PRIORITY_NORMAL
    assert decision.request_information is True
    assert decision.reasons == (REASON_NO_EVIDENCE,)


def test_review_priority_high_and_missing_evidence(margin, test_model_facts):
    """Decision PR 9 (a): a case can be "high" AND need more information."""
    threshold, bounds = test_model_facts
    decision = route_case(_score(bounds["high"], threshold, bounds), [], margin)
    assert decision.priority == PRIORITY_HIGH
    assert decision.request_information is True
    assert decision.reasons == (REASON_HIGH_BAND, REASON_NO_EVIDENCE)


def test_routing_uses_the_score_threshold(margin):
    """The threshold comes from ScoreResult (model_metadata.json, I20), never from the code."""
    # Same score and band, two invented thresholds: only the threshold changes the priority.
    value = 0.28
    near = ScoreResult(score=value, threshold=value + margin / 2, risk_band="low", model_version="v")
    far = ScoreResult(score=value, threshold=value + 2 * margin, risk_band="low", model_version="v")
    assert route_case(near, EVIDENCE, margin).priority == PRIORITY_HIGH
    assert route_case(far, EVIDENCE, margin).priority == PRIORITY_NORMAL


@pytest.mark.parametrize("bad", ["no_margin", "negative_margin", "nan_margin", "nan_score", "inf_threshold"])
def test_routing_refuses_missing_margin_or_non_finite(bad, margin):
    score = ScoreResult(score=0.2, threshold=0.3, risk_band="low", model_version="v")
    used_margin = margin
    if bad == "no_margin":
        used_margin = None
    elif bad == "negative_margin":
        used_margin = -margin
    elif bad == "nan_margin":
        used_margin = float("nan")
    elif bad == "nan_score":
        score = ScoreResult(score=float("nan"), threshold=0.3, risk_band="low", model_version="v")
    else:
        score = ScoreResult(score=0.2, threshold=float("inf"), risk_band="low", model_version="v")
    with pytest.raises(ValueError):
        route_case(score, EVIDENCE, used_margin)


def test_routing_policy_layer_rules():
    """Layer 3 (Architecture §5): no LLM, no Streamlit, no config read (the margin is passed in)."""
    tree = ast.parse(ROUTING_SOURCE.read_text(encoding="utf-8"))
    modules = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules |= {alias.name for alias in node.names}
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module)
    forbidden = ("src.agent.llm", "openai", "streamlit", "src.config", "os", "yaml")
    assert not [m for m in modules if any(m == f or m.startswith(f + ".") for f in forbidden)]
