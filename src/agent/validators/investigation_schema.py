"""
SoC layer      : 3 — Logic Engine
Responsibility : Describe the shape of the LLM investigation draft (the 10 fields of brief §10.2) as
                 a strict Pydantic model: required fields, types and allowed values only
Never does     : Call the LLM; compare the draft with the official score, band or evidence, or look
                 for prohibited terms (investigation_validator.py, n° 51, does); convert types silently
                 (strict mode: "0.5" written as text is not a number)
Reference      : Architecture_Projet.md v1.3 — section 8 (n° 50); Features_Complet.md F06, H01, H02;
                 brief §10.2; PASSATION.md §6, decisions PR 6
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

# Allowed values, as written in brief §10.2.
RiskLevel = Literal["low", "medium", "high"]
# The three values are accepted by the schema so that the validator can give a clear reason
# when the LLM writes "passed" or "failed" itself (founder decision PR 6 (i): must be "pending").
ValidationStatus = Literal["pending", "passed", "failed"]

# Shared settings: unknown fields refused, no silent type conversion, no NaN / infinity.
_STRICT = ConfigDict(extra="forbid", strict=True, allow_inf_nan=False, frozen=True)


class DraftEvidence(BaseModel):
    """One evidence line of the draft: which approved item it relies on, and a short note."""

    model_config = _STRICT

    source_id: str = Field(min_length=1)
    note: str = Field(min_length=1)


class InvestigationDraft(BaseModel):
    """The 10 fields of brief §10.2. A draft that does not fit is rejected by H01."""

    model_config = _STRICT

    case_id: str = Field(min_length=1)
    risk_level: RiskLevel
    model_score: float
    model_version: str = Field(min_length=1)
    evidence: list[DraftEvidence]
    summary: str = Field(min_length=1)
    uncertainties: list[str]
    recommended_review_steps: list[str]
    source_ids: list[str]
    validation_status: ValidationStatus


# The 10 required field names, in the order of brief §10.2 (used by the tests).
REQUIRED_FIELDS = tuple(InvestigationDraft.model_fields)
