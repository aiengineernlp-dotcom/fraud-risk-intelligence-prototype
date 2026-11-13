"""
SoC layer      : 3 — Logic Engine
Responsibility : Decide, with deterministic rules only, whether an LLM investigation draft may be shown:
                 readable JSON, schema (n° 50), same case, validation_status "pending", risk_level =
                 official band, model_score and model_version = official ScoreResult, every source ID
                 among the supplied evidence, uncertainty when no evidence (F07), no prohibited term
                 → ValidationResult(passed, reasons)
Never does     : Call the LLM; read the database or the case note; compute or correct a score or a band
                 (it only compares with the official ScoreResult); raise for a rejected draft (a
                 rejection is a result, passed=False); retry (retry.py, n° 62); write anything
Reference      : Architecture_Projet.md v1.3 — section 3 (Flux 2a), section 5, section 8 (n° 51);
                 Features_Complet.md H01 to H05, F07; brief §10.2, §10.4, §12.2, §14;
                 PASSATION.md §6, decisions PR 6 (i), (ii), (a) to (d)
"""

from __future__ import annotations

import json
import math
import re
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

import yaml
from pydantic import ValidationError

from src.agent.domain import EvidenceItem, ScoreResult
from src.agent.validators.investigation_schema import InvestigationDraft

# Founder decision PR 6 (a): the draft score must equal the official score; 1e-9 only absorbs a
# float written and read back, never a rounding (a rounded score could cross the threshold or a
# band bound). The prompt (PR 7) must therefore give the score at full precision.
MODEL_SCORE_ABS_TOLERANCE = 1e-9


class ProhibitedTermsError(ValueError):
    """The prohibited-terms file is missing, unreadable or has an empty category."""


@dataclass(frozen=True)
class ProhibitedTerms:
    """The terms of configs/prohibited_terms.yaml, ready to search: (category, term, pattern)."""

    rules: tuple[tuple[str, str, re.Pattern[str]], ...]


@dataclass(frozen=True)
class ValidationResult:
    """The verdict of the validator. `draft` is the parsed draft when the schema was respected."""

    passed: bool
    reasons: tuple[str, ...]
    draft: InvestigationDraft | None = None


def _term_pattern(term: str) -> re.Pattern[str]:
    # Whole word or phrase, any case. Not \b: it fails next to "%" ("100% sure").
    return re.compile(r"(?<!\w)" + re.escape(term) + r"(?!\w)", re.IGNORECASE)


def load_prohibited_terms(path: Path) -> ProhibitedTerms:
    """Read the terms file (path given by the caller, decision (ii)).

    Raises ProhibitedTermsError: an unusable list must stop the validation, never let all pass.
    """
    try:
        content = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as error:
        raise ProhibitedTermsError(f"Prohibited terms file unusable: {error}") from error

    categories = content.get("categories") if isinstance(content, dict) else None
    if not isinstance(categories, dict) or not categories:
        raise ProhibitedTermsError("Prohibited terms file has no 'categories'")

    rules = []
    for category, terms in categories.items():
        if not isinstance(terms, list) or not terms:
            raise ProhibitedTermsError(f"Category '{category}' must be a non-empty list")
        for term in terms:
            if not isinstance(term, str) or not term.strip():
                raise ProhibitedTermsError(f"Category '{category}' has an empty or non-text term")
            rules.append((str(category), term, _term_pattern(term.strip())))
    return ProhibitedTerms(rules=tuple(rules))


def _schema_reasons(error: ValidationError) -> tuple[str, ...]:
    """One readable reason per schema problem, e.g. "schema: summary: Field required"."""
    reasons = []
    for problem in error.errors():
        where = ".".join(str(part) for part in problem["loc"]) or "draft"
        reasons.append(f"schema: {where}: {problem['msg']}")
    return tuple(reasons)


def _texts_to_check(draft: InvestigationDraft) -> list[tuple[str, str]]:
    """The free-text fields searched for prohibited terms, with their names for the reasons."""
    texts = [("summary", draft.summary)]
    texts += [(f"uncertainties[{i}]", text) for i, text in enumerate(draft.uncertainties)]
    texts += [
        (f"recommended_review_steps[{i}]", text)
        for i, text in enumerate(draft.recommended_review_steps)
    ]
    texts += [(f"evidence[{i}].note", item.note) for i, item in enumerate(draft.evidence)]
    return texts


def validate_investigation(
    raw_json: str,
    official: ScoreResult,
    case_id: str,
    evidence: Sequence[EvidenceItem],
    terms: ProhibitedTerms,
) -> ValidationResult:
    """Check one draft against the official facts. Never raises for a bad draft.

    Order: readable JSON, then schema (stop there if either fails: the other rules need the
    fields), then every other rule, all reasons kept.
    """
    # H01 — readable JSON.
    if not isinstance(raw_json, str):
        return ValidationResult(False, ("draft is not JSON text",))
    try:
        json.loads(raw_json)
    except ValueError as error:
        return ValidationResult(False, (f"malformed JSON: {error.msg} (position {error.pos})",))

    # H01, H02 — schema: 10 required fields, types, allowed values.
    try:
        draft = InvestigationDraft.model_validate_json(raw_json)
    except ValidationError as error:
        return ValidationResult(False, _schema_reasons(error))

    reasons: list[str] = []

    if draft.case_id != case_id:
        reasons.append(f"case_id '{draft.case_id}' is not the case under review '{case_id}'")

    # Decision (i): only the validator decides; the LLM must leave "pending".
    if draft.validation_status != "pending":
        reasons.append(
            f"validation_status must be 'pending' (the validator decides), got '{draft.validation_status}'"
        )

    # H02 — the band is the official one, computed by risk_bands.py (never by the LLM).
    if draft.risk_level != official.risk_band:
        reasons.append(
            f"risk_level '{draft.risk_level}' differs from the official band '{official.risk_band}'"
        )

    # H03 — score and version identical to the official ScoreResult (decision (a)).
    if not math.isclose(
        draft.model_score, official.score, rel_tol=0.0, abs_tol=MODEL_SCORE_ABS_TOLERANCE
    ):
        reasons.append(
            f"model_score {draft.model_score!r} differs from the official score {official.score!r}"
        )
    if draft.model_version != official.model_version:
        reasons.append(
            f"model_version '{draft.model_version}' differs from the official "
            f"'{official.model_version}'"
        )

    # H04 — every cited source ID belongs to the evidence supplied for this case.
    supplied = {item.source_id for item in evidence}
    cited = list(draft.source_ids) + [item.source_id for item in draft.evidence]
    unknown = sorted(set(cited) - supplied)
    if unknown:
        reasons.append(f"source IDs not in the supplied evidence: {', '.join(unknown)}")

    # F07, decision (c) — no evidence: the gap must be stated, not filled.
    if not supplied and (not draft.uncertainties or not draft.recommended_review_steps):
        reasons.append(
            "no evidence supplied: at least one uncertainty and one review step required"
        )

    # H05 — prohibited or definitive wording, decisions (b) and (d).
    for field_name, text in _texts_to_check(draft):
        for category, term, pattern in terms.rules:
            if pattern.search(text):
                reasons.append(f"prohibited term '{term}' ({category}) in {field_name}")

    return ValidationResult(passed=not reasons, reasons=tuple(reasons), draft=draft)
