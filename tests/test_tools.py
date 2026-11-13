"""
SoC layer      : Tests
Responsibility : Test the inputs of the agent tools: case input checks (n° 39), approved evidence
                 store (n° 36), demo cases and evidence builder (n° 37) (started at J4, PR 4;
                 the tools n° 44 to 47 are added at PR 5)
Never does     : Load the real PaySim file or the trained model; call the network or an LLM;
                 write outside tmp_path
Reference      : Architecture_Projet.md v1.3 — section 8 (n° 48, tests of n° 36, 37, 39), D-09, D-10;
                 Features_Complet.md G05, G08, F07; PASSATION.md §6, decisions PR 4
"""

from __future__ import annotations

import json
import re

import numpy as np
import pytest

from src.agent.domain import EvidenceItem
from src.data.case_input import CaseInput, CaseInputError, parse_case_input
from src.data.load_paysim import load_raw
from src.data.split import stratified_split
from src.storage.evidence_repository import EvidenceStoreError, get_evidence

from scripts import build_demo_cases


def _valid_input(**changes):
    """A valid case input (invented values); `changes` overrides or adds fields."""
    raw = {
        "case_id": "CASE-0001",
        "step": 1,
        "type": "TRANSFER",
        "amount": 181.0,
        "oldbalanceOrg": 181.0,
        "newbalanceOrig": 0.0,
        "oldbalanceDest": 0.0,
        "newbalanceDest": 0.0,
        "case_note": "Synthetic note.",
    }
    raw.update(changes)
    return raw


# --- n° 39 case_input.py ------------------------------------------------------------------------


def test_valid_input_accepted():
    case = parse_case_input(_valid_input())
    assert isinstance(case, CaseInput)
    assert case.case_id == "CASE-0001"
    assert case.transaction() == {
        "step": 1, "type": "TRANSFER", "amount": 181.0, "oldbalanceOrg": 181.0,
        "newbalanceOrig": 0.0, "oldbalanceDest": 0.0, "newbalanceDest": 0.0,
    }


def test_case_note_is_optional_and_unbounded():
    raw = _valid_input()
    del raw["case_note"]
    assert parse_case_input(raw).case_note is None
    assert parse_case_input(_valid_input(case_note=None)).case_note is None
    long_note = "x" * 100_000  # no length limit (founder decision, PR 4, Q2)
    assert parse_case_input(_valid_input(case_note=long_note)).case_note == long_note


def test_integer_amount_becomes_float():
    case = parse_case_input(_valid_input(amount=181))
    assert case.amount == 181.0 and isinstance(case.amount, float)


def _without(field):
    raw = _valid_input()
    del raw[field]
    return raw


@pytest.mark.parametrize(
    ("raw", "field_in_message"),
    [
        (["not", "a", "dict"], "dict"),
        (_valid_input(case_id="CASE-1"), "case_id"),
        (_valid_input(case_id="case-0001"), "case_id"),
        (_valid_input(case_id="CASE-00012"), "case_id"),
        (_valid_input(case_id=1), "case_id"),
        (_without("amount"), "amount"),
        (_without("case_id"), "case_id"),
        (_valid_input(extra_field=1), "extra_field"),
        (_valid_input(nameOrig="C123"), "nameOrig"),
        (_valid_input(nameDest="C456"), "nameDest"),
        (_valid_input(step=1.5), "step"),
        (_valid_input(step="1"), "step"),
        (_valid_input(step=True), "step"),
        (_valid_input(amount="181"), "amount"),
        (_valid_input(amount=True), "amount"),
        (_valid_input(amount=float("nan")), "amount"),
        (_valid_input(amount=float("inf")), "amount"),
        (_valid_input(amount=-1.0), "amount"),
        (_valid_input(oldbalanceDest=-0.01), "oldbalanceDest"),
        (_valid_input(type="WIRE"), "type"),
        (_valid_input(type=3), "type"),
        (_valid_input(case_note=42), "case_note"),
    ],
)
def test_invalid_input_rejected(raw, field_in_message):
    with pytest.raises(CaseInputError, match=field_in_message):
        parse_case_input(raw)


@pytest.mark.parametrize("label", ["isFraud", "isFlaggedFraud"])
def test_label_in_case_input_rejected(label):
    with pytest.raises(CaseInputError, match="Labels are not allowed"):
        parse_case_input(_valid_input(**{label: 0}))


def test_case_input_is_read_only():
    case = parse_case_input(_valid_input())
    with pytest.raises(AttributeError):
        case.amount = 0.0  # frozen dataclass


# --- n° 36 evidence_repository.py ---------------------------------------------------------------

def _write_store(path, items):
    path.write_text(json.dumps({"generated_by": "test", "evidence": items}), encoding="utf-8")
    return path


@pytest.fixture
def evidence_store(tmp_path):
    """A small invented store: CASE-0001 has two items (written out of order), CASE-0002 one."""
    return _write_store(tmp_path / "evidence_store.json", [
        {"source_id": "EV-0002", "case_id": "CASE-0001", "text": "Simulated hour of day: 1 (step 1)."},
        {"source_id": "EV-0001", "case_id": "CASE-0001", "text": "Transaction type: TRANSFER."},
        {"source_id": "EV-0003", "case_id": "CASE-0002", "text": "Transaction type: PAYMENT."},
    ])


def test_known_case_returns_its_evidence_sorted(evidence_store):
    assert get_evidence(evidence_store, "CASE-0001") == [
        EvidenceItem("EV-0001", "Transaction type: TRANSFER."),
        EvidenceItem("EV-0002", "Simulated hour of day: 1 (step 1)."),
    ]


@pytest.mark.parametrize("case_id", ["CASE-9999", "CASE-0003", "not-an-id", "", None, 42])
def test_unknown_case_returns_empty(evidence_store, case_id):
    # CASE-0003 stands for a case with no evidence: absent from the store -> explicit empty list.
    assert get_evidence(evidence_store, case_id) == []


def test_empty_store_returns_empty(tmp_path):
    assert get_evidence(_write_store(tmp_path / "s.json", []), "CASE-0001") == []


def test_missing_store_raises(tmp_path):
    with pytest.raises(EvidenceStoreError, match="not found"):
        get_evidence(tmp_path / "absent.json", "CASE-0001")


@pytest.mark.parametrize(
    "content",
    [
        "{not json",
        json.dumps([]),
        json.dumps({"items": []}),
        json.dumps({"evidence": [{"source_id": "EV-0001", "case_id": "CASE-0001"}]}),
        json.dumps({"evidence": [{"source_id": "EV-0001", "case_id": "CASE-0001", "text": 1}]}),
        json.dumps({"evidence": [{"source_id": "EV-1", "case_id": "CASE-0001", "text": "t"}]}),
        json.dumps({"evidence": [
            {"source_id": "EV-0001", "case_id": "CASE-0001", "text": "t"},
            {"source_id": "EV-0001", "case_id": "CASE-0002", "text": "u"},
        ]}),
        json.dumps({"evidence": [
            {"source_id": "EV-0001", "case_id": "CASE-0001", "text": "t", "isFraud": 0},
        ]}),
    ],
)
def test_broken_store_raises(tmp_path, content):
    path = tmp_path / "broken.json"
    path.write_text(content, encoding="utf-8")
    with pytest.raises(EvidenceStoreError):
        get_evidence(path, "CASE-0001")


def test_get_evidence_never_writes(evidence_store):
    before = evidence_store.read_bytes()
    get_evidence(evidence_store, "CASE-0001")
    assert evidence_store.read_bytes() == before


# --- n° 37 scripts/build_demo_cases.py (small invented CSV, fake scorer: no model, no PaySim) ---

TEST_THRESHOLD = 0.5  # test values only: the real ones come from model_metadata.json / settings.yaml
TEST_BOUNDS = {"medium": 0.5, "high": 0.8}
TEST_MARGIN = 0.05
TEST_SEED = 42


def fake_scorer(features):
    """Cycles high / medium / near threshold / low scores over the rows (deterministic)."""
    return np.resize(np.array([0.9, 0.6, 0.47, 0.1]), len(features))


def _build(csv_path, seed=TEST_SEED, score_fn=fake_scorer):
    return build_demo_cases.build_from_csv(
        csv_path, score_fn, seed=seed, val_size=0.15, test_size=0.15,
        threshold=TEST_THRESHOLD, bounds=TEST_BOUNDS, margin=TEST_MARGIN,
        model_name="test_model", model_saved_at="2026-01-01T00:00:00+00:00",
    )


def _selected(csv_path):
    raw = load_raw(csv_path)
    parts = stratified_split(raw, val_size=0.15, test_size=0.15, seed=TEST_SEED)
    return build_demo_cases.select_rows(
        build_demo_cases.feature_rows(parts.test), fake_scorer,
        threshold=TEST_THRESHOLD, bounds=TEST_BOUNDS, margin=TEST_MARGIN, seed=TEST_SEED,
    )


def test_same_seed_gives_same_demo_files(small_paysim_csv):
    assert _build(small_paysim_csv) == _build(small_paysim_csv)


def test_selection_follows_group_quotas(small_paysim_csv):
    selected = _selected(small_paysim_csv)
    assert selected["_group"].value_counts().to_dict() == build_demo_cases.GROUP_QUOTAS
    assert len(selected) == 10  # founder decision (a)


def test_selection_never_sees_labels_or_identifiers(small_paysim_csv):
    seen_columns = []

    def spy_scorer(features):
        seen_columns.append(tuple(features.columns))
        return fake_scorer(features)

    _build(small_paysim_csv, score_fn=spy_scorer)
    assert seen_columns == [build_demo_cases.FEATURE_FIELDS]
    assert not set(seen_columns[0]) & build_demo_cases.FORBIDDEN_KEYS


def test_demo_cases_come_from_the_test_part(small_paysim_csv):
    raw = load_raw(small_paysim_csv)
    parts = stratified_split(raw, val_size=0.15, test_size=0.15, seed=TEST_SEED)
    selected = _selected(small_paysim_csv)
    assert set(selected.index) <= set(parts.test.index)


def test_every_demo_case_is_a_valid_case_input(small_paysim_csv):
    cases_doc, _ = _build(small_paysim_csv)
    ids = [parse_case_input(case).case_id for case in cases_doc["cases"]]
    assert ids == [f"CASE-{n:04d}" for n in range(1, 11)]


def test_every_evidence_has_a_unique_source_id(small_paysim_csv):
    cases_doc, evidence_doc = _build(small_paysim_csv)
    source_ids = [item["source_id"] for item in evidence_doc["evidence"]]
    assert len(source_ids) == len(set(source_ids))
    assert all(re.fullmatch(r"EV-\d{4}", sid) for sid in source_ids)
    assert "EV-9999" not in source_ids  # reserved for the injected note
    case_ids = {case["case_id"] for case in cases_doc["cases"]}
    assert {item["case_id"] for item in evidence_doc["evidence"]} <= case_ids


def test_trap_note_on_first_high_case_and_no_evidence_on_first_medium(small_paysim_csv, tmp_path):
    selected = _selected(small_paysim_csv)
    cases_doc, evidence_doc = build_demo_cases.build_documents(
        selected, seed=TEST_SEED, model_name="m", model_saved_at="t"
    )
    groups = list(selected["_group"])
    first_high = f"CASE-{groups.index('high') + 1:04d}"
    first_medium = f"CASE-{groups.index('medium') + 1:04d}"

    notes = {case["case_id"]: case["case_note"] for case in cases_doc["cases"]}
    assert [cid for cid, note in notes.items() if note == build_demo_cases.TRAP_NOTE] == [first_high]

    store = tmp_path / "evidence_store.json"
    build_demo_cases.write_json(evidence_doc, store)
    with_evidence = [cid for cid in notes if get_evidence(store, cid)]
    assert sorted(set(notes) - set(with_evidence)) == [first_medium]  # one case, no evidence


def test_too_few_rows_in_a_group_is_refused(small_paysim_csv):
    def all_low(features):
        return np.full(len(features), 0.1)

    with pytest.raises(build_demo_cases.DemoBuildError, match="high"):
        _build(small_paysim_csv, score_fn=all_low)


def test_forbidden_key_blocks_the_documents():
    for leaked in ("isFraud", "isFlaggedFraud", "nameOrig", "nameDest"):
        cases_doc = {"cases": [{"case_id": "CASE-0001", leaked: 0}]}
        with pytest.raises(build_demo_cases.DemoBuildError, match=leaked):
            build_demo_cases.check_documents(cases_doc, {"evidence": []})


def test_find_raw_csv_needs_exactly_one_file(tmp_path):
    with pytest.raises(build_demo_cases.DemoBuildError):
        build_demo_cases.find_raw_csv(tmp_path)
    (tmp_path / "a.csv").write_text("x")
    assert build_demo_cases.find_raw_csv(tmp_path).name == "a.csv"
    (tmp_path / "b.csv").write_text("x")
    with pytest.raises(build_demo_cases.DemoBuildError):
        build_demo_cases.find_raw_csv(tmp_path)


def _row(**changes):
    row = {"step": 27, "type": "TRANSFER", "amount": 181.0, "oldbalanceOrg": 181.0,
           "newbalanceOrig": 0.0, "oldbalanceDest": 0.0, "newbalanceDest": 0.0}
    row.update(changes)
    return row


def test_evidence_rules_e1_to_e6():
    assert build_demo_cases.evidence_texts(_row()) == [
        "Transaction type: TRANSFER.",
        "The amount (181.00) is 100.0% of the origin account balance before the transaction (181.00).",
        "The origin account balance after the transaction is 0.00.",
        "The destination account balance is recorded as 0.00 before and after the transaction.",
        "Simulated hour of day: 3 (step 27).",
    ]


def test_evidence_rules_e2bis_and_e4():
    texts = build_demo_cases.evidence_texts(
        _row(oldbalanceOrg=0.0, newbalanceOrig=0.0, oldbalanceDest=50.0, newbalanceDest=231.0)
    )
    assert texts == [
        "Transaction type: TRANSFER.",
        "The origin account balance recorded before the transaction is 0.00.",
        "The origin balance change (0.00) differs from the amount (181.00) by 181.00.",
        "Simulated hour of day: 3 (step 27).",
    ]


def test_evidence_amounts_compared_to_the_cent():
    # 0.004 of difference disappears at the cent (founder decision, PR 4, Q3): no E4 sentence.
    texts = build_demo_cases.evidence_texts(
        _row(amount=100.004, oldbalanceOrg=300.0, newbalanceOrig=200.0, oldbalanceDest=1.0)
    )
    assert not any("differs" in text for text in texts)


NON_NEUTRAL_WORDS = ("fraud", "suspicious", "suspect", "launder", "criminal")


def test_evidence_texts_are_neutral(small_paysim_csv):
    _, evidence_doc = _build(small_paysim_csv)
    for item in evidence_doc["evidence"]:
        assert not any(word in item["text"].lower() for word in NON_NEUTRAL_WORDS), item


def test_written_json_is_stable(tmp_path):
    path = tmp_path / "out" / "doc.json"
    build_demo_cases.write_json({"b": 1, "a": [1, 2]}, path)
    assert path.read_text(encoding="utf-8") == '{\n  "a": [\n    1,\n    2\n  ],\n  "b": 1\n}\n'
