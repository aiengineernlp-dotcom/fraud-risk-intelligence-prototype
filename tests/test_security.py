"""
SoC layer      : Tests
Responsibility : Security checks: no label nor PaySim identifier in the demo files, one injected note
                 only (started at J4, PR 4; secrets in logs, prompt fields, financial tools and
                 prompt injection end to end are added at J5)
Never does     : Load the real PaySim file or the trained model; call the network or an LLM
Reference      : Architecture_Projet.md v1.3 — section 8 (n° 71, tests of n° 37, 38), D-09, D-10, D-15;
                 Features_Complet.md G08, F05, K03; PASSATION.md §6, decisions PR 4
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import numpy as np

from src.data.case_input import parse_case_input
from src.storage.evidence_repository import get_evidence

from scripts import build_demo_cases

FORBIDDEN_KEYS = ("isFraud", "isFlaggedFraud", "nameOrig", "nameDest")
# PaySim identifiers look like C1231006815 / M1979787155: a letter C or M and many digits.
PAYSIM_ID_PATTERN = re.compile(r"\b[CM]\d{5,}\b")


def assert_no_label_nor_identifier(text: str) -> None:
    """The raw JSON text must not contain a forbidden field name nor an identifier-like value."""
    for key in FORBIDDEN_KEYS:
        assert key not in text, f"{key} found in a demo file"
    assert not PAYSIM_ID_PATTERN.search(text), "PaySim identifier found in a demo file"


def _build_small(csv_path):
    def scorer(features):
        return np.resize(np.array([0.9, 0.6, 0.47, 0.1]), len(features))

    return build_demo_cases.build_from_csv(
        csv_path, scorer, seed=42, val_size=0.15, test_size=0.15,
        threshold=0.5, bounds={"medium": 0.5, "high": 0.8}, margin=0.05,  # test values only
        model_name="test_model", model_saved_at="2026-01-01T00:00:00+00:00",
    )


def test_built_demo_files_have_no_label(small_paysim_csv, tmp_path):
    # The invented CSV has labels AND identifiers (C + 7 digits): none of them may come out.
    cases_doc, evidence_doc = _build_small(small_paysim_csv)
    for name, doc in (("cases.json", cases_doc), ("evidence_store.json", evidence_doc)):
        path = tmp_path / name
        build_demo_cases.write_json(doc, path)
        assert_no_label_nor_identifier(path.read_text(encoding="utf-8"))


def test_built_demo_files_have_one_injected_note_only(small_paysim_csv):
    cases_doc, evidence_doc = _build_small(small_paysim_csv)
    notes = [case["case_note"] for case in cases_doc["cases"]]
    assert notes.count(build_demo_cases.TRAP_NOTE) == 1
    assert "EV-9999" not in json.dumps(evidence_doc)  # the note cites a source that does not exist


# --- The versioned demo files themselves (n° 38): checked in CI, where there is no model ---------

DEMO_DIR = Path(__file__).resolve().parent.parent / "data" / "demo"


def test_demo_files_have_no_label():
    for name in ("cases.json", "evidence_store.json"):
        assert_no_label_nor_identifier((DEMO_DIR / name).read_text(encoding="utf-8"))


def test_demo_files_are_consistent():
    cases = json.loads((DEMO_DIR / "cases.json").read_text(encoding="utf-8"))["cases"]
    store = DEMO_DIR / "evidence_store.json"
    case_ids = [parse_case_input(case).case_id for case in cases]  # every case is a valid input
    assert len(case_ids) == 10 and len(set(case_ids)) == 10  # founder decision (a)
    assert [c["case_note"] for c in cases].count(build_demo_cases.TRAP_NOTE) == 1  # decision (c)
    without_evidence = [cid for cid in case_ids if get_evidence(store, cid) == []]
    assert len(without_evidence) == 1  # decision (d); get_evidence also checks unique EV- IDs
    assert "EV-9999" not in store.read_text(encoding="utf-8")
