"""
SoC layer      : 3 — Logic Engine
Responsibility : Tool validate_investigation_json: check its arguments, load the prohibited terms from
                 the path given by the caller (decision (ii)), and call the deterministic validator
                 (n° 51) with the official ScoreResult and the supplied evidence; a rejected draft is a
                 ValidationResult with passed=False, never an exception
Never does     : Call the LLM; judge a draft itself (the validator does); compute a score or a band;
                 read the case note; retry (retry.py, n° 62); write anything; any financial action
Reference      : Architecture_Projet.md v1.3 — section 3 (Flux 2a), section 5, section 8 (n° 52);
                 Features_Complet.md G06, G12, H01 to H05; PASSATION.md §6, decisions PR 5 (e), PR 6
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from src.agent.domain import EvidenceItem, ScoreResult
from src.agent.tools.errors import ToolInputError, ToolUnavailableError
from src.agent.validators.investigation_validator import (
    ProhibitedTermsError,
    ValidationResult,
    load_prohibited_terms,
    validate_investigation,
)

# What this tool may change (G12 test): nothing, it only reads its arguments and the terms file.
TOOL_EFFECT = "read_only"


def validate_investigation_json(
    raw_json: str,
    official: ScoreResult,
    case_id: str,
    evidence: Sequence[EvidenceItem],
    terms_path: Path,
) -> ValidationResult:
    """Validate one LLM draft. One attempt only.

    Raises ToolInputError (wrong arguments from the caller) or ToolUnavailableError (the terms file
    is missing or broken: validating without the list would let every wording pass).
    """
    if not isinstance(official, ScoreResult):
        raise ToolInputError("validate_investigation_json needs the official ScoreResult")
    if not isinstance(case_id, str) or not case_id:
        raise ToolInputError("validate_investigation_json needs a case_id")
    if not isinstance(evidence, (list, tuple)) or not all(
        isinstance(item, EvidenceItem) for item in evidence
    ):
        raise ToolInputError("validate_investigation_json needs a list of EvidenceItem")

    try:
        terms = load_prohibited_terms(Path(terms_path))
    except ProhibitedTermsError as error:
        raise ToolUnavailableError(str(error)) from error

    # A bad draft (including a draft that is not text) is a result, not an error.
    return validate_investigation(raw_json, official, case_id, list(evidence), terms)
