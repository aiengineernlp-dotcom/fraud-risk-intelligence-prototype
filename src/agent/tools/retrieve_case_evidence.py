"""
SoC layer      : 3 — Logic Engine
Responsibility : Tool retrieve_case_evidence: return the approved synthetic evidence of a case
                 (evidence_repository.py), sorted by source ID; an unknown case or a case without
                 evidence gives an explicit empty list (G05); a broken store raises
                 ToolUnavailableError, never an empty list (decision (b), Q-17)
Never does     : Call the LLM; write or change the store; invent or rewrite an item; hide a store
                 failure behind "no evidence"; retry (retry.py, n° 62); any financial action
Reference      : Architecture_Projet.md v1.3 — section 3 (Flux 1), section 5, section 8 (n° 46), D-09;
                 Features_Complet.md G05, G12; brief §11.4; PASSATION.md §6, Q-17, decisions PR 5
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from src.agent.domain import EvidenceItem
from src.agent.tools.errors import ToolUnavailableError
from src.storage.evidence_repository import EvidenceStoreError, get_evidence

# What this tool may change (G12 test): nothing, it only reads the store.
TOOL_EFFECT = "read_only"


def retrieve_case_evidence(store_path: Path, case_id: Any) -> list[EvidenceItem]:
    """Return the evidence of `case_id`, or [] if the case is unknown or has none. One attempt only.

    Raises ToolUnavailableError if the store is missing, unreadable or inconsistent: a broken store
    is a failure (retried, then FAILED), not "no evidence" (decision (b)).
    """
    try:
        return get_evidence(Path(store_path), case_id)
    except EvidenceStoreError as error:
        raise ToolUnavailableError(f"Evidence store unavailable: {error}") from error
