"""
SoC layer      : 2 — Ingestion/Parser
Responsibility : Read the approved synthetic evidence store (evidence_store.json, path given by the
                 caller) and return the evidence items of one case, sorted by source ID; an unknown
                 case or a case without evidence gives an explicit empty list (G05)
Never does     : Write or change the store; decide anything from the evidence; invent an item;
                 hide a broken store behind an empty list (a broken store raises EvidenceStoreError)
Reference      : Architecture_Projet.md v1.3 — section 1.2, section 5, section 8 (n° 36), D-09;
                 Features_Complet.md G05, G08, F07; brief §11.4 retrieve_case_evidence
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from src.agent.domain import EvidenceItem

# Unique source ID: "EV-" + 4 digits (D-09 notation "EV-xxxx").
SOURCE_ID_PATTERN = re.compile(r"EV-\d{4}")
ITEM_FIELDS = frozenset({"source_id", "case_id", "text"})


class EvidenceStoreError(Exception):
    """Raised when the store is missing, unreadable or inconsistent.

    This is a failure of the store, NOT "no evidence": the caller (tool n° 46) decides what to do.
    """


def get_evidence(store_path: Path, case_id: Any) -> list[EvidenceItem]:
    """Return the evidence items of `case_id`, sorted by source ID.

    Unknown, malformed or evidence-less case ID -> [] (explicit empty result, never an exception).
    """
    items = _read_store(Path(store_path))
    found = [
        EvidenceItem(source_id=item["source_id"], text=item["text"])
        for item in items
        if item["case_id"] == case_id
    ]
    return sorted(found, key=lambda evidence: evidence.source_id)


def _read_store(path: Path) -> list[dict[str, str]]:
    """Read and check the whole store: every item well formed, every source ID unique."""
    if not path.is_file():
        raise EvidenceStoreError(f"Evidence store not found: {path}")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise EvidenceStoreError(f"Evidence store unreadable: {path} ({error})") from error

    items = data.get("evidence") if isinstance(data, dict) else None
    if not isinstance(items, list):
        raise EvidenceStoreError("Evidence store: expected an object with an 'evidence' list")

    seen: set[str] = set()
    for position, item in enumerate(items):
        if not isinstance(item, dict) or set(item) != ITEM_FIELDS:
            raise EvidenceStoreError(
                f"Evidence store: item {position} must have exactly {sorted(ITEM_FIELDS)}"
            )
        if not all(isinstance(item[name], str) for name in ITEM_FIELDS):
            raise EvidenceStoreError(f"Evidence store: item {position} has a non-text field")
        source_id = item["source_id"]
        if not SOURCE_ID_PATTERN.fullmatch(source_id):
            raise EvidenceStoreError(f"Evidence store: bad source ID {source_id!r}")
        if source_id in seen:
            raise EvidenceStoreError(f"Evidence store: duplicate source ID {source_id}")
        seen.add(source_id)
    return items
