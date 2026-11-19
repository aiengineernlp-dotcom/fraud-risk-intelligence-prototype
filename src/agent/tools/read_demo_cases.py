"""
SoC layer      : 3 — Logic Engine
Responsibility : Tool read_demo_cases: read the synthetic demo cases (data/demo/cases.json) for the
                 UI case selection (brief §13 element 1, J03) — the list of case IDs, and one raw
                 case (7 fields, case_id, case_note) to hand to submit_case
Never does     : Write anything; score, band or decide; check the fields of a case (parse_case_input
                 does it at intake, labels included); call the LLM; retry; any financial action
Reference      : Architecture_Projet.md v1.5 — section 1.2, section 5, section 8 (n° 37, 38; this
                 file is outside the register, to be added by the founder); Features_Complet.md J03,
                 G12; PASSATION.md §6, decisions I73 (4)
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from src.agent.tools.errors import ToolInputError, ToolUnavailableError

# What this tool may change (G12 test): nothing, it only reads the demo file (I73 (4)).
TOOL_EFFECT = "read_only"

# Fixed message: never the text of the original error (it may carry a path or a value).
UNAVAILABLE_MESSAGE = "The demo cases file is missing or unreadable"


def _read_cases(path: Path) -> list[dict[str, Any]]:
    """Read and check the shape of the whole file; any problem -> ToolUnavailableError."""
    cases = None
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        cases = data.get("cases") if isinstance(data, dict) else None
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        cases = None
    # Checked outside the except: no chained error, no original text (same rule as start_app).
    if not isinstance(cases, list):
        raise ToolUnavailableError(UNAVAILABLE_MESSAGE)
    seen: set[str] = set()
    for case in cases:
        if not isinstance(case, dict) or not isinstance(case.get("case_id"), str):
            raise ToolUnavailableError(UNAVAILABLE_MESSAGE)
        if case["case_id"] in seen:  # two cases with one ID: which one to run is never guessed
            raise ToolUnavailableError(UNAVAILABLE_MESSAGE)
        seen.add(case["case_id"])
    return cases


def list_demo_case_ids(path: Path) -> list[str]:
    """Return the IDs of the demo cases, in the order of the file (shuffled with the seed, Q-16 (2))."""
    return [case["case_id"] for case in _read_cases(path)]


def get_demo_case(path: Path, case_id: str) -> dict[str, Any]:
    """Return a copy of one raw demo case. Unknown ID -> ToolInputError (nothing guessed)."""
    for case in _read_cases(path):
        if case["case_id"] == case_id:
            return dict(case)
    raise ToolInputError(f"Unknown demo case: {case_id}")
