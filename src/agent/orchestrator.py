"""
SoC layer      : 4 — LLM Interpreter + orchestrator
Responsibility : Move one case from state to state in the fixed order of the brief §11.3
                 (intake -> score -> evidence -> draft -> validation -> human review), calling the
                 tools and the LLM; idempotence by stored step results (G10); review routing;
                 one audit event per transition and per attempt (G03)
                 — and the read-only API for the UI (J06): case view, review queue sorted by the
                 G11 priority, audit events and audit export, through read tools only
                 — and the write API for the UI (J05, J09): reviewer decision, case submission,
                 start-up checks (model loaded once) and one database connection per run
Never does     : Compute the score, the risk band, the priority or the validity of a draft (the
                 tools, routing_policy.py and the validator do); touch the database without a tool
                 (update_case, intake_case, write_audit_event — Q-28); wrap a writing tool in
                 retry.py; read .env; any financial action
Reference      : Architecture_Projet.md v1.3 — section 1.2, section 3 (Flux 1, 2a, 2b),
                 section 3bis, section 5, section 8 (n° 63), section 10.2; Features_Complet.md G03,
                 G10, G11; brief §11.3, §11.6; PASSATION.md §6, Q-05, Q-28, decisions PR 9 and PR 10
                 — read-only API (PR 12): Architecture §4 "Points d'entrée"; Features J03, J04, J06,
                 J08; decisions I67 (read_audit tool), I69
                 — write API (PR 13): Architecture §3 Flux 1, §3bis; Features J05, J09, I01;
                 decisions I71, Q-12, Q-19 (4), Q-38
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Callable, Sequence

from src.agent.domain import AuditEvent, CaseState, EvidenceItem, ScoreResult
from src.agent.llm.base import LLMClient, LLMError
from src.agent.prompt_builder import PROMPT_VERSION, PromptTemplateError, build_messages
from src.agent.retry import RESULT_REJECTED, AttemptRecord, run_with_retries
from src.agent.routing_policy import route_case
from src.agent.routing_policy import PRIORITY_HIGH, PRIORITY_NORMAL  # PR 12: review queue order
from src.agent.state_machine import InvalidTransitionError, is_terminal
from src.agent.tools import update_case
from src.agent.tools import read_audit, read_cases  # PR 12: read-only tools (I67, I69)
from src.agent.tools.errors import DuplicateSubmissionError, ToolError
from src.agent.tools.errors import ToolInputError  # PR 12: unknown case in get_case_view
from src.agent.tools.intake_case import intake_case
from src.agent.tools.retrieve_case_evidence import retrieve_case_evidence
from src.agent.tools.score_transaction import ScoringModel, score_transaction
from src.agent.tools.validate_investigation_json import validate_investigation_json
from src.agent.tools.write_audit_event import write_audit_event
from src.config import AppConfig
from src.data.case_input import CaseInput, parse_case_input
from src.data.case_input import FEATURE_FIELDS  # PR 12: the 7 verified fields of the view
from contextlib import contextmanager  # PR 13: open_connection
from typing import Iterator  # PR 13
from src.agent.llm.factory import create_llm_client  # PR 13: start_app builds make_llm_client
from src.agent.llm.fake_client import DraftFacts  # PR 13: facts given to the fake client
from src.agent.tools.score_transaction import load_scoring_model  # PR 13: start_app (Q-19 (4))
from src.agent.tools.errors import ToolUnavailableError  # PR 13: model missing at start-up

# Step names = the values allowed by the CHECK of step_results.step (section 10.2).
STEP_SCORE = "score"
STEP_EVIDENCE = "evidence"
STEP_DRAFT = "draft"
STEP_VALIDATION = "validation"
STEP_ROUTING = "routing"  # audit only: never stored as a step result

# A draft is shown only once a human has the case: never for a rejected or failed case (§11.6).
STATES_WITH_TRUSTED_DRAFT = frozenset(
    {CaseState.HUMAN_REVIEW, CaseState.CLOSED, CaseState.ESCALATED, CaseState.NEEDS_MORE_INFORMATION}
)

# Fixed reason when the validator says "failed" without a reason (should not happen).
REASON_VALIDATION_FAILED = "validation_failed"

MakeLLMClient = Callable[[str, ScoreResult, Sequence[EvidenceItem]], LLMClient]


class AuditUnavailableError(RuntimeError):
    """The audit trail could not be written: the workflow stops, it never goes on without a trace.

    Not a ToolError on purpose: a step failure is turned into FAILED, an audit failure is not
    (writing the FAILED event would fail the same way).
    """


@dataclass(frozen=True)
class CaseOutcome:
    """What the UI gets back. `draft` is set only when the case is in human review (or later)."""

    case_id: str
    state: CaseState
    priority: str | None
    request_information: bool | None
    routing_reasons: tuple[str, ...]
    score: ScoreResult | None
    evidence: tuple[EvidenceItem, ...] | None
    draft: str | None
    failure_cause: dict[str, str] | None  # {"step", "cause"} of THIS run; None otherwise
    validation_reasons: tuple[str, ...]


class _StepFailed(Exception):
    """Internal: a step could not finish (retries used up, bad input, provider refusal)."""

    def __init__(self, step: str, cause: str, result: str = "failed") -> None:
        super().__init__(f"{step}: {cause}")
        self.step = step
        self.cause = cause    # a fixed code, never the text of an error (it may carry a secret)
        self.result = result  # "failed" or "timeout" (audit_events.result)


# --- audit ----------------------------------------------------------------------------------------

def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _write_event(conn, event: AuditEvent) -> int:
    """Append one event with the audit tool. One attempt only: never wrapped in retry.py."""
    try:
        return write_audit_event(conn, event)
    except ToolError as error:
        raise AuditUnavailableError("The audit trail could not be written") from error


def _attempt_auditor(conn, case_id: str, actor: str) -> Callable[[AttemptRecord], None]:
    """The audit function given to retry.py: one "tool_call" event per attempt."""
    def audit(record: AttemptRecord) -> None:
        _write_event(conn, AuditEvent(
            case_id=case_id, timestamp=_now(), actor=actor, action="tool_call",
            result=record.result, details=record.details(),
        ))
    return audit


def _cause_code(error: Exception) -> str:
    """Same fixed codes as retry.py: the class name, or "llm:<kind>"; never str(error)."""
    if isinstance(error, LLMError):
        return f"llm:{error.kind}"
    return type(error).__name__


# --- transitions ----------------------------------------------------------------------------------

def apply_transition(
    conn,
    case_id: str,
    target: CaseState,
    *,
    actor: str,
    result: str = "ok",
    details: dict[str, Any] | None = None,
    model_version: str | None = None,
    prompt_version: str | None = None,
) -> CaseState:
    """Change the state through update_case (which asks state_machine.py first), then audit it.

    A refused transition is audited as "invalid_transition" and the error goes up (Q-05, G02):
    it is a bug in the order of the steps, never a normal path. Returns the new state.
    """
    try:
        previous = update_case.transition_case(conn, case_id, target)
    except InvalidTransitionError as error:
        _write_event(conn, AuditEvent(
            case_id=case_id, timestamp=_now(), actor=actor, action="invalid_transition",
            result="failed", state_from=error.current, state_to=error.target,
        ))
        raise
    _write_event(conn, AuditEvent(
        case_id=case_id, timestamp=_now(), actor=actor, action="transition", result=result,
        state_from=previous, state_to=target, details=details,
        model_version=model_version, prompt_version=prompt_version,
    ))
    return target


# --- stored step results (G10) --------------------------------------------------------------------

def _score_to_dict(score: ScoreResult) -> dict[str, Any]:
    return {"score": score.score, "threshold": score.threshold,
            "risk_band": score.risk_band, "model_version": score.model_version}


def _evidence_to_dict(evidence: Sequence[EvidenceItem]) -> dict[str, Any]:
    return {"evidence": [{"source_id": item.source_id, "text": item.text} for item in evidence]}


def _stored_score(conn, case_id: str) -> ScoreResult | None:
    stored = update_case.get_step(conn, case_id, STEP_SCORE)
    return ScoreResult(**stored.result) if stored is not None else None


def _stored_evidence(conn, case_id: str) -> list[EvidenceItem] | None:
    stored = update_case.get_step(conn, case_id, STEP_EVIDENCE)
    if stored is None:
        return None
    return [EvidenceItem(**item) for item in stored.result["evidence"]]


def _run_tool_step(conn, case_id: str, step: str, tool_name: str, call: Callable[[], Any],
                   config: AppConfig, clock: Callable[[], float]) -> tuple[Any, int]:
    """Run a READ-ONLY tool with bounded retries; return (value, attempts) or raise _StepFailed."""
    try:
        outcome = run_with_retries(
            step, call, settings=config.tool_retries,
            audit=_attempt_auditor(conn, case_id, f"tool:{tool_name}"), clock=clock,
        )
    except ToolError as error:  # ToolInputError: audited by retry.py, never retried
        raise _StepFailed(step, _cause_code(error)) from None
    if not outcome.ok:
        raise _StepFailed(step, f"{tool_name}:{outcome.cause}", result=outcome.cause)
    return outcome.value, outcome.attempts


# --- the workflow ---------------------------------------------------------------------------------

def _case_input_of(record) -> CaseInput:
    """Rebuild the checked input from the stored case (only the 7 verified fields and the note)."""
    return parse_case_input({**record.transaction, "case_id": record.case_id,
                             "case_note": record.case_note})


def run_case(
    raw_case: dict,
    *,
    conn,
    config: AppConfig,
    scoring_model: ScoringModel,
    make_llm_client: MakeLLMClient,
    clock: Callable[[], float] = time.monotonic,
) -> CaseOutcome:
    """Run one case as far as it can go, and return where it stopped.

    A second submission of the same case_id resumes the stored case: a stored step is never run
    again (no second score, no second draft — G10) and a final state is returned as it is.
    Raises ToolInputError for an invalid input (no case is created, nothing to audit).
    """
    try:
        record = intake_case(conn, raw_case)  # writes: one attempt only, never in retry.py
        case_id = record.case_id
        _write_event(conn, AuditEvent(
            case_id=case_id, timestamp=_now(), actor="tool:intake_case", action="transition",
            result="ok", state_from=None, state_to=CaseState.RECEIVED,
        ))
    except DuplicateSubmissionError as duplicate:
        case_id = duplicate.case_id
        record = update_case.get_case(conn, case_id)

    if is_terminal(record.state) or record.state in STATES_WITH_TRUSTED_DRAFT:
        return _outcome(conn, case_id, config)

    try:
        return _advance(conn, record, config, scoring_model, make_llm_client, clock)
    except _StepFailed as failure:
        # Any non-final state -> FAILED (brief §11.3 "Any step", I45); the cause is a fixed code.
        cause = {"step": failure.step, "cause": failure.cause}
        apply_transition(conn, case_id, CaseState.FAILED, actor="system",
                         result=failure.result, details=cause)
        return _outcome(conn, case_id, config, failure_cause=cause)


def _advance(conn, record, config: AppConfig, scoring_model: ScoringModel,
             make_llm_client: MakeLLMClient, clock: Callable[[], float]) -> CaseOutcome:
    case_id = record.case_id
    state = record.state
    case_input = _case_input_of(record)

    # 1. Score (read-only tool, retried). Stored once: never a second score (G10).
    score = _stored_score(conn, case_id)
    if score is None:
        score, attempts = _run_tool_step(
            conn, case_id, STEP_SCORE, "score_transaction",
            lambda: score_transaction(scoring_model, case_input), config, clock)
        update_case.save_step(conn, case_id, STEP_SCORE, _score_to_dict(score), attempts)
    if state is CaseState.RECEIVED:
        state = apply_transition(conn, case_id, CaseState.SCORED, actor="tool:score_transaction",
                                 model_version=score.model_version)

    # 2. Evidence (read-only tool, retried). An empty list is an answer, not a failure (G05).
    evidence = _stored_evidence(conn, case_id)
    if evidence is None:
        evidence, attempts = _run_tool_step(
            conn, case_id, STEP_EVIDENCE, "retrieve_case_evidence",
            lambda: retrieve_case_evidence(config.paths.evidence_store, case_id), config, clock)
        update_case.save_step(conn, case_id, STEP_EVIDENCE, _evidence_to_dict(evidence), attempts)
    if state is CaseState.SCORED:
        state = apply_transition(conn, case_id, CaseState.EVIDENCE_READY,
                                 actor="tool:retrieve_case_evidence",
                                 details={"evidence_count": len(evidence)})

    # 3. Draft + validation: the LLM call is retried; the validator (a tool) judges each text.
    stored_validation = update_case.get_step(conn, case_id, STEP_VALIDATION)
    if stored_validation is not None and not stored_validation.result["passed"]:
        return _reject(conn, case_id, state, tuple(stored_validation.result["reasons"]),
                       stored_validation.attempts, config)

    stored_draft = update_case.get_step(conn, case_id, STEP_DRAFT)
    attempts = stored_draft.attempts if stored_draft is not None else 0
    if stored_draft is None:
        try:
            messages = build_messages(case_input, score, evidence)
        except PromptTemplateError:
            raise _StepFailed(STEP_DRAFT, "PromptTemplateError") from None
        client = make_llm_client(case_id, score, evidence)

        def check(text: str) -> tuple[str, ...]:
            verdict = validate_investigation_json(
                text, score, case_id, evidence, config.paths.prohibited_terms)
            if verdict.passed:
                return ()
            return tuple(verdict.reasons) or (REASON_VALIDATION_FAILED,)

        try:
            outcome = run_with_retries(
                STEP_DRAFT, lambda: client.complete(messages).text, settings=config.llm_retries,
                audit=_attempt_auditor(conn, case_id, "llm"), check=check, clock=clock,
            )
        except (ToolError, LLMError) as error:
            # kind="auth" re-raised by retry.py, or the terms file is missing (ToolUnavailableError
            # from the validator): the case cannot be judged -> FAILED.
            raise _StepFailed(STEP_DRAFT, _cause_code(error)) from None

        if not outcome.ok and outcome.cause == RESULT_REJECTED:
            # Texts were received (DRAFTED) but none passed: rejected, nothing stored as trusted.
            return _reject(conn, case_id, state, outcome.last_reasons, outcome.attempts, config)
        if not outcome.ok:
            # Last attempt failed or timed out: the cause of the LAST attempt decides (risk 1).
            raise _StepFailed(STEP_DRAFT, f"llm:{outcome.cause}", result=outcome.cause)

        attempts = outcome.attempts
        update_case.save_step(conn, case_id, STEP_DRAFT,
                              {"text": outcome.value, "prompt_version": PROMPT_VERSION}, attempts)
        update_case.save_step(conn, case_id, STEP_VALIDATION, {"passed": True, "reasons": []}, attempts)

    if state is CaseState.EVIDENCE_READY:
        state = apply_transition(conn, case_id, CaseState.DRAFTED, actor="llm",
                                 details={"attempts": attempts}, prompt_version=PROMPT_VERSION)
    if state is CaseState.DRAFTED:
        state = apply_transition(conn, case_id, CaseState.VALIDATED, actor="validator",
                                 details={"attempts": attempts})

    # 4. Every VALIDATED case goes to human review (brief §11.6, G11), with its priority.
    try:
        decision = route_case(score, evidence, config.near_threshold_margin)
    except ValueError:
        raise _StepFailed(STEP_ROUTING, "routing_unavailable") from None
    update_case.set_case_priority(conn, case_id, decision.priority)
    apply_transition(conn, case_id, CaseState.HUMAN_REVIEW, actor="system", details={
        "priority": decision.priority,
        "request_information": decision.request_information,
        "reasons": list(decision.reasons),
    })
    return _outcome(conn, case_id, config)


def _reject(conn, case_id: str, state: CaseState, reasons: tuple[str, ...], attempts: int,
            config: AppConfig) -> CaseOutcome:
    """DRAFTED -> VALIDATION_REJECTED (final, brief §11.3 and state_machine.py): no draft is stored."""
    update_case.save_step(conn, case_id, STEP_VALIDATION,
                          {"passed": False, "reasons": list(reasons)}, attempts)
    if state is CaseState.EVIDENCE_READY:
        state = apply_transition(conn, case_id, CaseState.DRAFTED, actor="llm",
                                 details={"attempts": attempts}, prompt_version=PROMPT_VERSION)
    apply_transition(conn, case_id, CaseState.VALIDATION_REJECTED, actor="validator",
                     result=RESULT_REJECTED, details={"attempts": attempts, "reasons": list(reasons)})
    return _outcome(conn, case_id, config)


def _outcome(conn, case_id: str, config: AppConfig,
             failure_cause: dict[str, str] | None = None) -> CaseOutcome:
    """Build the view of the case from what is stored (read through the update_case tool)."""
    record = update_case.get_case(conn, case_id)
    score = _stored_score(conn, case_id)
    evidence = _stored_evidence(conn, case_id)
    validation = update_case.get_step(conn, case_id, STEP_VALIDATION)
    draft_step = update_case.get_step(conn, case_id, STEP_DRAFT)

    request_information, routing_reasons = None, ()
    if record.state in STATES_WITH_TRUSTED_DRAFT and score is not None and evidence is not None:
        # Pure function, recomputed for the view; the stored priority is the one that counts.
        decision = route_case(score, evidence, config.near_threshold_margin)
        request_information, routing_reasons = decision.request_information, decision.reasons

    draft = None
    if record.state in STATES_WITH_TRUSTED_DRAFT and draft_step is not None:
        draft = draft_step.result["text"]

    return CaseOutcome(
        case_id=case_id,
        state=record.state,
        priority=record.priority,
        request_information=request_information,
        routing_reasons=tuple(routing_reasons),
        score=score,
        evidence=tuple(evidence) if evidence is not None else None,
        draft=draft,
        failure_cause=failure_cause,
        validation_reasons=tuple(validation.result["reasons"]) if validation is not None else (),
    )


# --- read-only API for the UI (J06, PR 12, decisions I67, I69) --------------------------------------
# None of these functions writes: no state, no step result, no priority, no audit event (a read is
# not audited, it would be an INSERT). They read through update_case.get_case / get_step (like
# _outcome) and the read_only tools read_cases.py and read_audit.py — never src.storage or src.audit.

# Order of the review queue = the G11 priorities, from routing_policy.py constants (I60): nothing is
# recomputed, the stored priority is sorted. Same priority -> oldest first, then case_id (I69 (3)).
_QUEUE_RANK = {PRIORITY_HIGH: 0, PRIORITY_NORMAL: 1}


class MissingPriorityError(RuntimeError):
    """A case in HUMAN_REVIEW has no priority, or one outside the policy: its place in the queue is
    never guessed (I69 (4)). Should not happen: the priority is stored before the transition."""

    def __init__(self, case_id: str) -> None:
        super().__init__(f"Case in human review without a valid priority: {case_id}")
        self.case_id = case_id


@dataclass(frozen=True)
class CaseView:
    """What the case page shows (J03, J04): the same view as run_case, plus the 7 verified fields.

    `outcome` is built by _outcome(), the one way to build a case view (I69 (5)); its failure_cause
    is always None here (the cause of a failure is in the audit trail: J07, interface PR).
    The case note is NOT in the view: it is untrusted data (I55, I69 (6)).
    """

    outcome: CaseOutcome
    transaction: dict[str, Any]  # exactly FEATURE_FIELDS, in that order; never a label


@dataclass(frozen=True)
class QueueItem:
    """One line of the review queue (J08). No transaction and no case note."""

    case_id: str
    priority: str
    created_at: str


def get_case_view(case_id: str, *, conn, config: AppConfig) -> CaseView:
    """Return the view of a stored case. Raises ToolInputError for an unknown case (P1)."""
    record = update_case.get_case(conn, case_id)
    if record is None:
        raise ToolInputError(f"Unknown case: {case_id}")
    # Field by field from FEATURE_FIELDS, never a copy of the stored dict: a key that is not one of
    # the 7 verified fields (e.g. a label) cannot reach the view, even if it were stored.
    transaction = {name: record.transaction[name] for name in FEATURE_FIELDS}
    return CaseView(outcome=_outcome(conn, case_id, config), transaction=transaction)


def _queue_key(record) -> tuple[int, str, str]:
    """Sort key: G11 priority, then created_at (oldest first), then case_id (I69 (3), (4))."""
    if record.priority not in _QUEUE_RANK:
        raise MissingPriorityError(record.case_id)
    return (_QUEUE_RANK[record.priority], record.created_at, record.case_id)


def list_review_queue(*, conn) -> list[QueueItem]:
    """Return the cases in HUMAN_REVIEW, high priority first (G11, J08).

    Raises MissingPriorityError if one of them has no valid priority (I69 (4)).
    """
    records = read_cases.list_cases_in_state(conn, CaseState.HUMAN_REVIEW)
    return [QueueItem(case_id=r.case_id, priority=r.priority, created_at=r.created_at)
            for r in sorted(records, key=_queue_key)]


def get_audit_events(case_id: str | None = None, *, conn) -> list:
    """Return the audit events (audit_repository.StoredAuditEvent) of one case, or of every case if
    `case_id` is None, in event_id order. Checked like an export (I69 (7)): an event with a label,
    a secret-looking key or a non-finite number raises ToolInputError (the value is never shown)."""
    return read_audit.read_events(conn, case_id)


def export_audit(fmt: str, case_id: str | None = None, *, conn) -> str:
    """Return the audit of one case (or of every case) as CSV or JSON text (I02, J06)."""
    return read_audit.export_events(conn, fmt, case_id)


# --- write API for the UI (J05, J09, PR 13, decisions I71, Q-12, Q-19 (4)) --------------------------
# Every write goes through a tool (update_case, write_audit_event — Q-28) and is never wrapped in
# retry.py. Known limit kept (Q-38): the case and its audit event are two transactions.

# Fixed message: never the text of the original error (Q-19 (4)).
STARTUP_MODEL_MESSAGE = "The scoring model is missing or unusable: run python -m src.train"


class AppStartupError(RuntimeError):
    """The application cannot start (model missing or unusable): no database opened, no case."""


class ReviewAlreadyRecordedError(RuntimeError):
    """A decision was asked for a case that is no longer in HUMAN_REVIEW (already decided with
    ANOTHER decision, rejected, failed…). Nothing was written to the case; the refusal is audited."""

    def __init__(self, case_id: str, current: CaseState, requested: CaseState) -> None:
        super().__init__(f"Case {case_id} is {current.value}: decision {requested.value} refused")
        self.case_id = case_id
        self.current = current
        self.requested = requested


@dataclass(frozen=True)
class AppResources:
    """What the UI keeps for the whole application (loaded once by start_app)."""

    config: AppConfig
    scoring_model: ScoringModel
    make_llm_client: MakeLLMClient


def start_app(config: AppConfig) -> AppResources:
    """Load the scoring model once, BEFORE anything else (Q-19 (4)).

    Missing model or wrong band bounds -> AppStartupError with a fixed message: no database is
    opened, no case is created, nothing goes to FAILED.
    """
    try:
        scoring_model = load_scoring_model(config.paths.model_pipeline, config.paths.model_metadata)
    except ToolUnavailableError:
        scoring_model = None
    if scoring_model is None:  # raised outside the except: no chained error, no original text
        raise AppStartupError(STARTUP_MODEL_MESSAGE)

    def make_llm_client(case_id: str, score: ScoreResult,
                        evidence: Sequence[EvidenceItem]) -> LLMClient:
        # The fake client copies the official facts; the real one gets them in the prompt.
        return create_llm_client(config, fake_facts=DraftFacts.from_official(case_id, score, evidence))

    return AppResources(config=config, scoring_model=scoring_model, make_llm_client=make_llm_client)


@contextmanager
def open_connection(config: AppConfig) -> Iterator[Any]:
    """One database connection per run of the UI script, opened and closed in the same thread
    (Q-12): no connection is shared between threads, no check_same_thread=False, no lock."""
    conn = update_case.open_database(config.paths.runtime_db)
    try:
        yield conn
    finally:
        conn.close()


def submit_case(raw_case: dict, *, conn, app: AppResources) -> CaseOutcome:
    """Run a submitted case with the resources of start_app: run_case, nothing more.

    A double submission resumes the stored case (no second case, J09, G10).
    """
    return run_case(raw_case, conn=conn, config=app.config, scoring_model=app.scoring_model,
                    make_llm_client=app.make_llm_client)


def record_review_decision(case_id: str, decision: CaseState, comment: str | None = None, *,
                           conn, config: AppConfig) -> CaseView:
    """Record the reviewer decision (J05): HUMAN_REVIEW -> CLOSED / ESCALATED /
    NEEDS_MORE_INFORMATION, through update_case.record_review; return the case view.

    - recorded: one "review_decision" event; details = {"comment_length": n}, never the text (I71).
    - same decision already recorded: nothing written, no event (J09).
    - another decision, or a case not in HUMAN_REVIEW: "invalid_transition" event, then
      ReviewAlreadyRecordedError.
    - ToolInputError (decision outside the 3, FAILED included; bad comment; unknown case) and
      ToolUnavailableError (database) go up as they are: nothing audited, the case stays in
      HUMAN_REVIEW, never FAILED (I71 (1)).
    """
    try:
        previous, stored_comment, recorded = update_case.record_review(
            conn, case_id, decision, comment)
    except InvalidTransitionError as refused:
        _write_event(conn, AuditEvent(
            case_id=case_id, timestamp=_now(), actor="reviewer", action="invalid_transition",
            result="failed", state_from=refused.current, state_to=refused.target,
        ))
        raise ReviewAlreadyRecordedError(case_id, refused.current, refused.target) from None

    if recorded:
        _write_event(conn, AuditEvent(
            case_id=case_id, timestamp=_now(), actor="reviewer", action="review_decision",
            result="ok", state_from=previous, state_to=decision,
            details={"comment_length": len(stored_comment or "")},
        ))
    return get_case_view(case_id, conn=conn, config=config)
