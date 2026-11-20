"""
SoC layer      : 4 — LLM Interpreter
Responsibility : Scripted fake LLM client (D-05) for the tests and the failure demo: one scenario per
                 client, a pre-written draft built from the official facts it is given
                 (valid, malformed, missing_field, score_mismatch, unsupported_evidence,
                 prohibited_claim, timeout)
Never does     : Open a network connection; read the messages to decide what to answer (it does not
                 depend on the prompt of n° 60); judge its own draft (the validator does); write a
                 label name (isFraud, isFlaggedFraud); wait (the timeout scenario raises at once)
Reference      : Architecture_Projet.md v1.3 — section 3 (Flux 2a), section 4 (D-05), section 8
                 (n° 56); Features_Complet.md F02; brief §10.2, §10.5; PASSATION.md §5 and §6,
                 decisions PR 6 (a), (c) and PR 7; I75 (2) (summary of a case without evidence)
"""

from __future__ import annotations

import json
from collections.abc import Sequence
from dataclasses import dataclass

from src.agent.domain import EvidenceItem, ScoreResult
from src.agent.llm.base import LLMClient, LLMMessage, LLMResponse, LLMTimeout

# The seven scenarios of D-05. Only "valid" must pass the validator.
SCENARIOS = (
    "valid",
    "malformed",
    "missing_field",
    "score_mismatch",
    "unsupported_evidence",
    "prohibited_claim",
    "timeout",
)

FAKE_MODEL_NAME = "fake-llm"

# Change applied to the official score in "score_mismatch". It only has to be far above the
# validator tolerance (1e-9); it is not a decision value. Subtracted when the score is above 0.9,
# so the wrong score always stays in [0, 1] (founder decision PR 7 (2)).
SCORE_MISMATCH_SHIFT = 0.1

# A source ID that is never given as evidence ("EV-" + 4 digits; the demo IDs start at EV-0001).
UNSUPPORTED_SOURCE_ID = "EV-9999"

# A definitive claim taken from configs/prohibited_terms.yaml (category "definitive").
# A test checks that the validator rejects it with this exact term.
PROHIBITED_TERM = "definitely"


@dataclass(frozen=True)
class DraftFacts:
    """The official facts the fake copies into its drafts (the real LLM gets them in the prompt)."""

    case_id: str
    risk_band: str
    model_score: float
    model_version: str
    source_ids: tuple[str, ...]

    @classmethod
    def from_official(cls, case_id: str, score: ScoreResult, evidence: Sequence[EvidenceItem]) -> DraftFacts:
        return cls(
            case_id=case_id,
            risk_band=score.risk_band,
            model_score=score.score,  # the same float, never rounded (decision PR 6 (a))
            model_version=score.model_version,
            source_ids=tuple(item.source_id for item in evidence),
        )


def _valid_draft(facts: DraftFacts) -> dict:
    """A draft that respects every validator rule, with or without evidence."""
    # I75 (2): never claim that evidence supports anything when no evidence item is listed.
    if facts.source_ids:
        evidence_sentence = (
            "The listed evidence supports a human review; it does not establish wrongdoing."
        )
    else:
        evidence_sentence = (
            "No evidence item is listed for this case; a human review is needed and the model "
            "score alone does not establish wrongdoing."
        )
    return {
        "case_id": facts.case_id,
        "risk_level": facts.risk_band,
        "model_score": facts.model_score,
        "model_version": facts.model_version,
        "evidence": [
            {"source_id": source_id, "note": "Approved evidence item considered by the reviewer."}
            for source_id in facts.source_ids
        ],
        "summary": (
            f"The model placed this case in the {facts.risk_band} risk band. " + evidence_sentence
        ),
        # Always one uncertainty and one review step: required when no evidence is supplied (F07).
        "uncertainties": ["The model score is an estimate and may be wrong for this case."],
        "recommended_review_steps": ["Review the transaction details and the evidence items listed."],
        "source_ids": list(facts.source_ids),
        "validation_status": "pending",  # the validator decides, never the LLM (decision PR 6 (i))
    }


def _wrong_score(score: float) -> float:
    """A score clearly different from the official one, still inside [0, 1]."""
    if score > 0.9:
        return score - SCORE_MISMATCH_SHIFT
    return score + SCORE_MISMATCH_SHIFT


def build_draft_text(scenario: str, facts: DraftFacts) -> str:
    """Return the raw text the fake answers for one scenario (not for "timeout", which raises)."""
    draft = _valid_draft(facts)
    if scenario == "valid":
        pass
    elif scenario == "malformed":
        return json.dumps(draft)[:40]  # cut in the middle: not readable JSON
    elif scenario == "missing_field":
        del draft["uncertainties"]
    elif scenario == "score_mismatch":
        draft["model_score"] = _wrong_score(facts.model_score)
    elif scenario == "unsupported_evidence":
        if UNSUPPORTED_SOURCE_ID in facts.source_ids:
            # Would not be "unsupported" any more: refuse rather than produce a passing draft.
            raise ValueError(f"{UNSUPPORTED_SOURCE_ID} is among the supplied evidence")
        draft["evidence"].append({"source_id": UNSUPPORTED_SOURCE_ID, "note": "Item not supplied."})
        draft["source_ids"].append(UNSUPPORTED_SOURCE_ID)
    elif scenario == "prohibited_claim":
        draft["summary"] = f"This transaction is {PROHIBITED_TERM} suspicious and needs review."
    else:
        raise ValueError(f"No draft for scenario '{scenario}'")
    return json.dumps(draft)


class FakeLLMClient(LLMClient):
    """Answers the pre-written draft of its scenario. No network, no cost, no wait."""

    def __init__(self, scenario: str, facts: DraftFacts) -> None:
        if scenario not in SCENARIOS:
            raise ValueError(f"Unknown fake scenario '{scenario}'; allowed: {', '.join(SCENARIOS)}")
        self.scenario = scenario
        self.facts = facts
        self.calls = 0                                  # for the tests and retry.py checks
        self.last_messages: tuple[LLMMessage, ...] = ()

    def complete(self, messages: Sequence[LLMMessage]) -> LLMResponse:
        self.calls += 1
        self.last_messages = tuple(messages)
        if self.scenario == "timeout":
            raise LLMTimeout("LLM provider did not answer in time (fake scenario)", kind="timeout")
        text = build_draft_text(self.scenario, self.facts)
        return LLMResponse(
            text=text,
            model=FAKE_MODEL_NAME,
            latency_seconds=0.0,
            input_tokens=None,
            output_tokens=None,
        )

    def __repr__(self) -> str:
        return f"FakeLLMClient(scenario='{self.scenario}')"
