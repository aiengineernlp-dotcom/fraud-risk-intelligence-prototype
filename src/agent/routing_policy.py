"""
SoC layer      : 3 — Logic Engine
Responsibility : The written review-routing policy (G11, brief §11.6): from the official score and
                 the evidence, decide the review priority ("high" or "normal") and whether more
                 information should be requested, with the reasons for the audit
Never does     : Call the LLM; import Streamlit; read config.py or a file (the margin is passed by
                 the caller); hard-code the threshold (it comes from ScoreResult, read from
                 model_metadata.json, I20); compute the score or the band; write to the database
Reference      : Architecture_Projet.md v1.3 — section 1.2, section 5, section 8 (n° 54), section 10.2
                 (cases.priority); Features_Complet.md G11; brief §11.6; configs/settings.yaml
                 (routing.near_threshold_margin, I08); PASSATION.md §6, decisions PR 9 (a)
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass

from src.agent.domain import EvidenceItem, ScoreResult
from src.models.risk_bands import BAND_HIGH

# Decision PR 9 (a): the only two values written in cases.priority.
# case_repository.ALLOWED_PRIORITIES holds the same set (a test checks they are equal).
PRIORITY_HIGH = "high"
PRIORITY_NORMAL = "normal"
PRIORITIES = frozenset({PRIORITY_HIGH, PRIORITY_NORMAL})

# Reasons, written in the audit event (never in cases.priority).
REASON_HIGH_BAND = "high_risk_band"
REASON_NEAR_THRESHOLD = "near_threshold"
REASON_NO_EVIDENCE = "no_evidence"


@dataclass(frozen=True)
class RoutingDecision:
    """The routing of one case. Only `priority` goes to the database; the rest goes to the audit."""

    priority: str
    request_information: bool
    reasons: tuple[str, ...]


def _is_real_number(value: object) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def is_near_threshold(score: float, threshold: float, margin: float) -> bool:
    """True when threshold - margin <= score < threshold (settings.yaml, I08: "[threshold - 0.05,
    threshold)"): just below the threshold, where the model was almost alerting."""
    return threshold - margin <= score < threshold


def route_case(
    score: ScoreResult,
    evidence: Sequence[EvidenceItem],
    near_threshold_margin: float | None,
) -> RoutingDecision:
    """Apply the written policy. The rules add up: a case can be "high" AND need more information.

    - high risk band, or score close to the threshold -> priority "high";
    - otherwise -> priority "normal";
    - no evidence at all -> request_information=True (decision PR 9 (a)).
    """
    if near_threshold_margin is None:
        # settings.yaml allows an empty margin; routing without one would be a guess.
        raise ValueError("routing.near_threshold_margin is empty: the routing policy cannot run")
    if not _is_real_number(near_threshold_margin) or near_threshold_margin < 0:
        raise ValueError("near_threshold_margin must be a finite number >= 0")
    if not _is_real_number(score.score) or not _is_real_number(score.threshold):
        raise ValueError("score and threshold must be finite numbers")

    reasons = []
    if score.risk_band == BAND_HIGH:
        reasons.append(REASON_HIGH_BAND)
    if is_near_threshold(score.score, score.threshold, near_threshold_margin):
        reasons.append(REASON_NEAR_THRESHOLD)
    priority = PRIORITY_HIGH if reasons else PRIORITY_NORMAL

    request_information = len(evidence) == 0
    if request_information:
        reasons.append(REASON_NO_EVIDENCE)

    return RoutingDecision(priority=priority, request_information=request_information,
                           reasons=tuple(reasons))
