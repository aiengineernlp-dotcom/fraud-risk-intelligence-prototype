"""
SoC layer      : Transverse (shared types, imported by layers 2, 3 and 4)
Responsibility : Name the shared vocabulary of the agent: the 11 case states and the frozen
                 records passed between tools, orchestrator, validator, review and audit
Never does     : Any logic (no transition rules, no scoring, no banding, no storage, no LLM call)
Reference      : Architecture_Projet.md v1.1 — section 3bis, section 8 (n° 32), section 10.2;
                 Features_Complet.md G01; brief §11.3, §11.4
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class CaseState(str, Enum):
    """The 11 states of an investigation case (brief §11.3, Architecture §3bis).

    A str-based Enum: the value is stored as-is in `cases.state` (section 10.2).
    Which transitions are allowed is decided in state_machine.py, not here.
    """

    RECEIVED = "RECEIVED"
    SCORED = "SCORED"
    EVIDENCE_READY = "EVIDENCE_READY"
    DRAFTED = "DRAFTED"
    VALIDATED = "VALIDATED"
    VALIDATION_REJECTED = "VALIDATION_REJECTED"
    HUMAN_REVIEW = "HUMAN_REVIEW"
    CLOSED = "CLOSED"
    ESCALATED = "ESCALATED"
    NEEDS_MORE_INFORMATION = "NEEDS_MORE_INFORMATION"
    FAILED = "FAILED"


# The three outcomes a human reviewer can record (brief §11.3; column
# `cases.reviewer_decision`, section 10.2). Kept as data, checked by the review step.
REVIEWER_OUTCOMES = frozenset(
    {CaseState.CLOSED, CaseState.ESCALATED, CaseState.NEEDS_MORE_INFORMATION}
)


@dataclass(frozen=True)
class ScoreResult:
    """Official model output for one case (brief §11.4, score_transaction).

    Produced only by the scoring tool. The LLM reads it, never computes it (D-03).
    """

    score: float
    threshold: float  # from model_metadata.json, never hard-coded (I20)
    risk_band: str  # computed by risk_bands.py; bounds still to be decided (n° 40)
    model_version: str


@dataclass(frozen=True)
class EvidenceItem:
    """One piece of approved synthetic evidence (brief §11.4, retrieve_case_evidence).

    Derived from the transaction variables, never from isFraud / isFlaggedFraud (D-09).
    """

    source_id: str  # unique source ID, "EV-xxxx" (D-09)
    text: str


@dataclass(frozen=True)
class ReviewDecision:
    """The decision recorded by the human reviewer (brief §11.3, HUMAN_REVIEW step).

    `decision` must be one of REVIEWER_OUTCOMES; the review step checks it.
    """

    case_id: str
    decision: CaseState
    comment: str | None = None


@dataclass(frozen=True)
class AuditEvent:
    """One structured audit event, field for field the `audit_events` table (section 10.2).

    `event_id` is not here: the database assigns it when the event is appended.
    Events are append-only (never modified, never deleted).
    """

    case_id: str
    timestamp: str  # ISO 8601, UTC
    actor: str  # "system", "tool:<name>", "llm", "validator", "reviewer"
    action: str  # e.g. "transition", "tool_call", "retry", "review_decision", "invalid_transition"
    result: str  # "ok", "failed", "rejected", "timeout"
    state_from: CaseState | None = None
    state_to: CaseState | None = None
    details: dict[str, Any] | None = None  # never a secret
    model_version: str | None = None
    prompt_version: str | None = None
