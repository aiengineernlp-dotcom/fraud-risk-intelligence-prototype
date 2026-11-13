"""
SoC layer      : 4 — LLM Interpreter + orchestrator
Responsibility : Move one case from state to state in the fixed order of the brief §11.3
                 (intake -> score -> evidence -> draft -> validation -> human review), calling the
                 tools and the LLM; idempotence by stored step results (G10); review routing;
                 one audit event per transition and per attempt (G03)
Never does     : Compute the score, the risk band, the priority or the validity of a draft (the
                 tools, routing_policy.py and the validator do); touch the database without a tool
                 (update_case, intake_case, write_audit_event — Q-28); wrap a writing tool in
                 retry.py; read .env; any financial action
Reference      : Architecture_Projet.md v1.3 — section 1.2, section 3 (Flux 1, 2a, 2b),
                 section 3bis, section 5, section 8 (n° 63), section 10.2; Features_Complet.md G03,
                 G10, G11; brief §11.3, §11.6; PASSATION.md §6, Q-05, Q-28, decisions PR 9 and PR 10
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
from src.agent.state_machine import InvalidTransitionError, is_terminal
from src.agent.tools import update_case
from src.agent.tools.errors import DuplicateSubmissionError, ToolError
from src.agent.tools.intake_case import intake_case
from src.agent.tools.retrieve_case_evidence import retrieve_case_evidence
from src.agent.tools.score_transaction import ScoringModel, score_transaction
from src.agent.tools.validate_investigation_json import validate_investigation_json
from src.agent.tools.write_audit_event import write_audit_event
from src.config import AppConfig
from src.data.case_input import CaseInput, parse_case_input

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
