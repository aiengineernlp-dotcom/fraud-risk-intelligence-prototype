"""
SoC layer      : Tests
Responsibility : Test the bounded retries (retry.py, n° 62) and the review routing policy
                 (routing_policy.py, n° 54) (PR 9); the orchestrator (n° 63) and its use of the
                 update_case tool (PR 10)
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
import json
from src.agent import orchestrator
from src.agent.prompt_builder import PROMPT_VERSION
from src.agent.state_machine import InvalidTransitionError
from src.agent.tools import update_case
from src.config import AppConfig, LLMSettings, Paths, Secret, SplitSettings

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


# === Orchestrator (n° 63, PR 10) ====================================================================
ORCH_CASE = "CASE-0001"
ORCH_EVIDENCE = [
    {"case_id": ORCH_CASE, "source_id": "EV-0001", "text": "Transaction type: TRANSFER."},
    {"case_id": ORCH_CASE, "source_id": "EV-0002", "text": "The origin account is emptied."},
]
ORCHESTRATOR_SOURCE = REPO_ROOT / "src" / "agent" / "orchestrator.py"
# Tools that write: never inside run_with_retries (decision PR 9, risk 1; Q-28).
WRITING_TOOL_NAMES = {"write_audit_event", "_write_event", "intake_case", "update_case",
                      "transition_case", "save_step", "set_case_priority", "apply_transition"}


def _raw_case(case_id=ORCH_CASE, **changes):
    """A valid case input with invented values (no label, no identifier)."""
    raw = {"case_id": case_id, "step": 1, "type": "TRANSFER", "amount": 181.0,
           "oldbalanceOrg": 181.0, "newbalanceOrig": 0.0, "oldbalanceDest": 0.0,
           "newbalanceDest": 0.0, "case_note": "Synthetic note."}
    raw.update(changes)
    return raw


@pytest.fixture
def orch_config(tmp_path, tool_settings, llm_settings) -> AppConfig:
    """AppConfig built by hand (never load_config()); values from settings.yaml, files in tmp_path."""
    store = tmp_path / "evidence_store.json"
    store.write_text(json.dumps({"evidence": ORCH_EVIDENCE}), encoding="utf-8")
    paths = Paths(
        raw_data_dir=tmp_path, runtime_db=tmp_path / "unused.db", demo_cases=tmp_path / "unused.json",
        evidence_store=store, model_pipeline=tmp_path / "unused.joblib", mlp_state=tmp_path / "unused.pt",
        model_metadata=tmp_path / "unused_meta.json", metrics_dir=tmp_path, figures_dir=tmp_path,
        prohibited_terms=TERMS_PATH,
    )
    routing = _settings_yaml()["routing"]
    return AppConfig(
        tool_retries=tool_settings, llm_retries=llm_settings,
        near_threshold_margin=routing["near_threshold_margin"],
        review_capacity_per_day=routing["review_capacity_per_day"],
        split=SplitSettings(seed=42, val_size=0.15, test_size=0.15), paths=paths,
        llm=LLMSettings(provider="fake", base_url="", model="", api_key=Secret("")),
    )


class _FakeMaker:
    """make_llm_client for the tests: one FakeLLMClient per case, built from the official facts."""

    def __init__(self, scenario="valid"):
        self.scenario = scenario
        self.clients = []

    def __call__(self, case_id, score, evidence):
        client = FakeLLMClient(self.scenario, DraftFacts.from_official(case_id, score, evidence))
        self.clients.append(client)
        return client

    @property
    def calls(self):
        return sum(client.calls for client in self.clients)


class _Clock:
    """A simulated monotonic clock: `tick` seconds pass at each reading (no sleep)."""

    def __init__(self, tick=0.0):
        self.now, self.tick = 0.0, tick

    def __call__(self):
        self.now += self.tick
        return self.now


def _run(conn, config, model, maker=None, raw=None, clock=None):
    return orchestrator.run_case(
        raw if raw is not None else _raw_case(), conn=conn, config=config, scoring_model=model,
        make_llm_client=maker if maker is not None else _FakeMaker(), clock=clock or _Clock(),
    )


def _events(conn, case_id=ORCH_CASE):
    return [stored.event for stored in list_events(conn, case_id)]


def _transitions(conn, case_id=ORCH_CASE):
    return [(e.state_from, e.state_to) for e in _events(conn, case_id) if e.action == "transition"]


NORMAL_PATH = [
    (None, CaseState.RECEIVED),
    (CaseState.RECEIVED, CaseState.SCORED),
    (CaseState.SCORED, CaseState.EVIDENCE_READY),
    (CaseState.EVIDENCE_READY, CaseState.DRAFTED),
    (CaseState.DRAFTED, CaseState.VALIDATED),
    (CaseState.VALIDATED, CaseState.HUMAN_REVIEW),
]


@pytest.mark.validation_workflow
def test_normal_case_reaches_human_review(db_conn, orch_config, scoring_model):
    """G03: a normal case goes through the states in the order of §11.3; the audit keeps each step."""
    outcome = _run(db_conn, orch_config, scoring_model)
    assert outcome.state is CaseState.HUMAN_REVIEW
    assert _transitions(db_conn) == NORMAL_PATH
    events = {e.state_to: e for e in _events(db_conn) if e.action == "transition"}
    assert events[CaseState.SCORED].model_version == outcome.score.model_version
    assert events[CaseState.DRAFTED].prompt_version == PROMPT_VERSION
    assert events[CaseState.DRAFTED].actor == "llm"
    assert events[CaseState.VALIDATED].actor == "validator"
    assert outcome.draft is not None and outcome.priority in PRIORITIES
    assert update_case.get_case(db_conn, ORCH_CASE).priority == outcome.priority
    assert [e.result for e in _events(db_conn) if e.action == "tool_call"] == [RESULT_OK] * 3


@pytest.mark.validation_workflow
def test_rejected_after_bounded_retries(db_conn, orch_config, scoring_model, llm_settings):
    """H06, Flux 2a: every draft rejected -> VALIDATION_REJECTED after 1 + N attempts, no draft kept."""
    maker = _FakeMaker("score_mismatch")
    outcome = _run(db_conn, orch_config, scoring_model, maker)
    expected_attempts = 1 + llm_settings.max_retries
    assert outcome.state is CaseState.VALIDATION_REJECTED
    assert maker.calls == expected_attempts
    assert outcome.draft is None and outcome.validation_reasons
    assert update_case.get_step(db_conn, ORCH_CASE, orchestrator.STEP_DRAFT) is None
    assert _transitions(db_conn)[-2:] == [
        (CaseState.EVIDENCE_READY, CaseState.DRAFTED),
        (CaseState.DRAFTED, CaseState.VALIDATION_REJECTED),
    ]
    llm_attempts = [e for e in _events(db_conn) if e.action == "tool_call" and e.actor == "llm"]
    assert [e.result for e in llm_attempts] == [RESULT_REJECTED] * expected_attempts
    assert update_case.get_case(db_conn, ORCH_CASE).priority is None


def test_tool_timeout_leads_to_failed(db_conn, orch_config, scoring_model, tool_settings, monkeypatch):
    """Flux 2b: the evidence tool answers too late every time -> FAILED, bounded, cause logged."""
    clock = _Clock()

    def slow_evidence(store_path, case_id):
        clock.now += tool_settings.timeout_seconds + 1  # later than the delay of settings.yaml
        return []

    monkeypatch.setattr(orchestrator, "retrieve_case_evidence", slow_evidence)
    outcome = _run(db_conn, orch_config, scoring_model, clock=clock)
    assert outcome.state is CaseState.FAILED
    assert outcome.failure_cause == {"step": "evidence", "cause": "retrieve_case_evidence:timeout"}
    attempts = [e for e in _events(db_conn) if e.actor == "tool:retrieve_case_evidence"
                and e.action == "tool_call"]
    assert [e.result for e in attempts] == [RESULT_TIMEOUT] * (1 + tool_settings.max_retries)
    last = _events(db_conn)[-1]
    assert (last.state_from, last.state_to, last.result) == (
        CaseState.SCORED, CaseState.FAILED, RESULT_TIMEOUT)
    assert update_case.get_step(db_conn, ORCH_CASE, orchestrator.STEP_EVIDENCE) is None


def test_tool_unavailable_leads_to_failed(db_conn, orch_config, scoring_model, tool_settings, monkeypatch):
    from src.agent.tools.errors import ToolUnavailableError as Unavailable

    def broken(model, case_input):
        raise Unavailable("down")

    monkeypatch.setattr(orchestrator, "score_transaction", broken)
    outcome = _run(db_conn, orch_config, scoring_model)
    assert outcome.state is CaseState.FAILED and outcome.score is None
    assert outcome.failure_cause == {"step": "score", "cause": "score_transaction:failed"}
    assert _transitions(db_conn)[-1] == (CaseState.RECEIVED, CaseState.FAILED)


def test_llm_timeout_leads_to_failed(db_conn, orch_config, scoring_model, llm_settings):
    maker = _FakeMaker("timeout")
    outcome = _run(db_conn, orch_config, scoring_model, maker)
    assert outcome.state is CaseState.FAILED and outcome.draft is None
    assert maker.calls == 1 + llm_settings.max_retries
    assert outcome.failure_cause == {"step": "draft", "cause": "llm:timeout"}
    assert _transitions(db_conn)[-1] == (CaseState.EVIDENCE_READY, CaseState.FAILED)


def test_llm_auth_leads_to_failed_without_retry(db_conn, orch_config, scoring_model):
    class AuthRefused(_FakeMaker):
        def __call__(self, case_id, score, evidence):
            client = super().__call__(case_id, score, evidence)

            def refuse(messages):
                client.calls += 1
                raise LLMUnavailable("refused", kind="auth", status_code=401)
            client.complete = refuse
            return client

    maker = AuthRefused()
    outcome = _run(db_conn, orch_config, scoring_model, maker)
    assert outcome.state is CaseState.FAILED and maker.calls == 1
    assert outcome.failure_cause == {"step": "draft", "cause": "llm:auth"}


@pytest.mark.validation_workflow
@pytest.mark.parametrize("band, score_value, evidence, expected_priority, expected_info", [
    ("high", 0.95, ORCH_EVIDENCE, PRIORITY_HIGH, False),
    ("low", 0.01, ORCH_EVIDENCE, PRIORITY_NORMAL, False),
    ("low", 0.01, [], PRIORITY_NORMAL, True),
])
def test_validated_always_goes_to_review(db_conn, orch_config, scoring_model, monkeypatch,
                                         band, score_value, evidence, expected_priority, expected_info):
    """G11, §11.6: whatever the band or the evidence, a VALIDATED case goes to HUMAN_REVIEW."""
    official = ScoreResult(score=score_value, threshold=0.3, risk_band=band, model_version="test@1")
    monkeypatch.setattr(orchestrator, "score_transaction", lambda model, case_input: official)
    orch_config.paths.evidence_store.write_text(json.dumps({"evidence": evidence}), encoding="utf-8")
    outcome = _run(db_conn, orch_config, scoring_model)
    assert outcome.state is CaseState.HUMAN_REVIEW
    assert _transitions(db_conn)[-2:] == NORMAL_PATH[-2:]
    assert outcome.priority == expected_priority
    assert outcome.request_information is expected_info
    review = _events(db_conn)[-1]
    assert review.details["priority"] == expected_priority
    assert review.details["request_information"] is expected_info


def test_idempotent_step(db_conn, orch_config, scoring_model, monkeypatch):
    """G10: submitting the same case twice creates no second score, no second draft."""
    scored = []
    real_score = orchestrator.score_transaction

    def spy(model, case_input):
        scored.append(case_input.case_id)
        return real_score(model, case_input)

    monkeypatch.setattr(orchestrator, "score_transaction", spy)
    maker = _FakeMaker()
    first = _run(db_conn, orch_config, scoring_model, maker)
    events_after_first = len(_events(db_conn))
    second = _run(db_conn, orch_config, scoring_model, maker)
    assert scored == [ORCH_CASE] and maker.calls == 1
    assert second == first
    assert len(_events(db_conn)) == events_after_first


def test_interrupted_case_resumes_without_redoing_stored_steps(db_conn, orch_config, scoring_model,
                                                                monkeypatch):
    """G10: a case stopped after the score resumes at the evidence step; the score is not redone."""
    from src.agent.tools.score_transaction import score_transaction as real_score

    intake = _raw_case()
    from src.agent.tools.intake_case import intake_case
    intake_case(db_conn, intake)
    score = real_score(scoring_model, orchestrator._case_input_of(update_case.get_case(db_conn, ORCH_CASE)))
    update_case.save_step(db_conn, ORCH_CASE, "score", orchestrator._score_to_dict(score), 1)
    update_case.transition_case(db_conn, ORCH_CASE, CaseState.SCORED)

    def never(model, case_input):
        raise AssertionError("the score must not be computed again")

    monkeypatch.setattr(orchestrator, "score_transaction", never)
    outcome = _run(db_conn, orch_config, scoring_model, raw=intake)
    assert outcome.state is CaseState.HUMAN_REVIEW and outcome.score == score


def test_invalid_transition_audited(db_conn, orch_config, scoring_model):
    """Q-05, G02: a refused jump is not applied AND leaves an "invalid_transition" event."""
    from src.agent.tools.intake_case import intake_case
    intake_case(db_conn, _raw_case())
    with pytest.raises(InvalidTransitionError):
        orchestrator.apply_transition(db_conn, ORCH_CASE, CaseState.VALIDATED, actor="system")
    assert update_case.get_case(db_conn, ORCH_CASE).state is CaseState.RECEIVED
    event = _events(db_conn)[-1]
    assert (event.action, event.result, event.state_from, event.state_to) == (
        "invalid_transition", RESULT_FAILED, CaseState.RECEIVED, CaseState.VALIDATED)


def test_invalid_input_creates_nothing(db_conn, orch_config, scoring_model):
    with pytest.raises(ToolInputError):
        _run(db_conn, orch_config, scoring_model, raw=_raw_case(isFraud=1))
    assert update_case.get_case(db_conn, ORCH_CASE) is None


def test_orchestrator_never_touches_the_database():
    """Architecture §5, Q-28: the orchestrator imports no storage module, no sqlite3, no audit repo."""
    modules = set()
    for node in ast.walk(ast.parse(ORCHESTRATOR_SOURCE.read_text(encoding="utf-8"))):
        if isinstance(node, ast.Import):
            modules |= {alias.name for alias in node.names}
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module)
    forbidden = ("src.storage", "src.audit", "sqlite3")
    assert not [m for m in modules if any(m == f or m.startswith(f + ".") for f in forbidden)]


def test_retry_never_wraps_writing_tools():
    """Decision PR 9 (risk 1): no writing tool inside what run_with_retries retries.

    Scanned: the `call` and `check` given to run_with_retries, the `call` given to _run_tool_step
    (which passes it on to run_with_retries), and the body of any local function named there.
    """
    tree = ast.parse(ORCHESTRATOR_SOURCE.read_text(encoding="utf-8"))
    local_defs = {node.name: node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)}
    # Position of the retried callable: run_with_retries(step, call, ...),
    # _run_tool_step(conn, case_id, step, tool_name, call, ...).
    call_position = {"run_with_retries": 1, "_run_tool_step": 4}
    calls = [node for node in ast.walk(tree) if isinstance(node, ast.Call)
             and getattr(node.func, "id", None) in call_position]
    assert {getattr(c.func, "id") for c in calls} == set(call_position), "scan found nothing"
    for call in calls:
        position = call_position[call.func.id]
        wrapped = [call.args[position]] if len(call.args) > position else []
        # The `audit=` callback writes on purpose (one event per attempt, never retried itself).
        wrapped += [kw.value for kw in call.keywords if kw.arg in ("call", "check")]
        for part in wrapped:
            nodes = list(ast.walk(part))
            for name in [n.id for n in nodes if isinstance(n, ast.Name)]:
                if name in local_defs and name not in call_position and name != "_run_tool_step":
                    nodes += list(ast.walk(local_defs[name]))
            names = {n.id for n in nodes if isinstance(n, ast.Name)}
            names |= {n.attr for n in nodes if isinstance(n, ast.Attribute)}
            assert not names & WRITING_TOOL_NAMES, (call.func.id, names & WRITING_TOOL_NAMES)
