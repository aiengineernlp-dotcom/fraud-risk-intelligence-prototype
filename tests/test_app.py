"""
SoC layer      : Tests
Responsibility : Test the Streamlit pages (n° 66 to 69) with streamlit.testing.v1.AppTest: banner on
                 every page (J02), start-up refusal (Q-19 (4)), fixed error messages (J07, I72 D4),
                 note and comment as plain text (I72 D1, D2), elements 1 to 12 of brief §13,
                 decision recorded end to end (J05), double click (J09), queue order (J08), audit
                 table = export (J06, I02), imports of app/ (I72 D3, I74 P3)
Never does     : Load the real model, call load_config() or read .env (orchestrator.load_app is
                 replaced by test resources: small model, fake LLM client, files in tmp_path); open
                 a network connection; write outside tmp_path
Reference      : Architecture_Projet.md v1.5 — section 1.2, section 5, section 8 (n° 66 to 69; this
                 file is outside the register, number given by the founder); Features_Complet.md
                 J01 to J09; brief §13; decisions I72, I73 (5), I74, Q-41
"""

from __future__ import annotations

import ast
import csv
import io
import json
import sqlite3
from pathlib import Path

import pytest
import streamlit as st
import yaml
from streamlit.testing.v1 import AppTest

from app import ui_components as ui
from src.agent import orchestrator
from src.agent.domain import CaseState
from src.agent.llm.fake_client import DraftFacts, FakeLLMClient
from src.agent.tools.errors import DuplicateSubmissionError, ToolInputError, ToolUnavailableError
from src.config import AppConfig, LLMSettings, Paths, RetrySettings, Secret, SplitSettings

REPO_ROOT = Path(__file__).resolve().parent.parent
APP_DIR = REPO_ROOT / "app"
HOME = str(APP_DIR / "Home.py")
REVIEW = str(APP_DIR / "pages" / "1_Case_Review.py")
AUDIT = str(APP_DIR / "pages" / "2_Audit_Trail.py")
PAGES = [HOME, REVIEW, AUDIT]
TERMS_PATH = REPO_ROOT / "configs" / "prohibited_terms.yaml"
SETTINGS_PATH = REPO_ROOT / "configs" / "settings.yaml"
TIMEOUT = 30

# Invented demo cases (no label, no identifier). The note of CASE-0901 tries Markdown and HTML.
TRAP_NOTE = "**TRAP-NOTE-77** <b>bold</b> [link](http://example.invalid)"
COMMENT = "Checked **TRAP-COMMENT-55** <i>x</i>"
SECRET = "SECRET-XYZ-0042"


def _case(case_id, note="Synthetic note."):
    return {"case_id": case_id, "step": 1, "type": "TRANSFER", "amount": 181.0,
            "oldbalanceOrg": 181.0, "newbalanceOrig": 0.0, "oldbalanceDest": 0.0,
            "newbalanceDest": 0.0, "case_note": note}


DEMO_CASES = [_case("CASE-0901", TRAP_NOTE), _case("CASE-0902"), _case("CASE-0903")]
EVIDENCE = [
    {"case_id": "CASE-0901", "source_id": "EV-0901", "text": "Transaction type: TRANSFER."},
    {"case_id": "CASE-0901", "source_id": "EV-0902", "text": "The origin account is emptied."},
    {"case_id": "CASE-0902", "source_id": "EV-0903", "text": "Transaction type: TRANSFER."},
]


class _Maker:
    """make_llm_client for the tests: one fake client per case; the scenario can be changed."""

    def __init__(self):
        self.scenario = "valid"

    def __call__(self, case_id, score, evidence):
        return FakeLLMClient(self.scenario, DraftFacts.from_official(case_id, score, evidence))


class _Env:
    def __init__(self, config, maker):
        self.config, self.maker = config, maker

    def connect(self):
        conn = sqlite3.connect(self.config.paths.runtime_db)
        conn.row_factory = sqlite3.Row
        return conn


@pytest.fixture
def ui_env(tmp_path, scoring_model, monkeypatch):
    """Test resources instead of orchestrator.load_app (I73 (5)); cache emptied before and after."""
    settings = yaml.safe_load(SETTINGS_PATH.read_text(encoding="utf-8"))
    demo = tmp_path / "demo_cases.json"
    demo.write_text(json.dumps({"cases": DEMO_CASES}), encoding="utf-8")
    store = tmp_path / "evidence_store.json"
    store.write_text(json.dumps({"evidence": EVIDENCE}), encoding="utf-8")
    paths = Paths(
        raw_data_dir=tmp_path, runtime_db=tmp_path / "runtime" / "capstone.db", demo_cases=demo,
        evidence_store=store, model_pipeline=tmp_path / "unused.joblib",
        mlp_state=tmp_path / "unused.pt", model_metadata=tmp_path / "unused_meta.json",
        metrics_dir=tmp_path, figures_dir=tmp_path, prohibited_terms=TERMS_PATH,
    )
    retries = settings["retries"]
    config = AppConfig(
        tool_retries=RetrySettings(retries["tools"]["max_retries"],
                                   float(retries["tools"]["timeout_seconds"])),
        llm_retries=RetrySettings(retries["llm"]["max_retries_after_rejection"],
                                  float(retries["llm"]["timeout_seconds"])),
        near_threshold_margin=settings["routing"]["near_threshold_margin"],
        review_capacity_per_day=settings["routing"]["review_capacity_per_day"],
        split=SplitSettings(seed=42, val_size=0.15, test_size=0.15), paths=paths,
        llm=LLMSettings(provider="fake", base_url="", model="", api_key=Secret("")),
    )
    maker = _Maker()
    resources = orchestrator.AppResources(config=config, scoring_model=scoring_model,
                                          make_llm_client=maker)
    monkeypatch.setattr(orchestrator, "load_app", lambda: resources)
    st.cache_resource.clear()
    yield _Env(config, maker)
    st.cache_resource.clear()


def _run(page, case_id=None):
    at = AppTest.from_file(page)
    if case_id is not None:
        at.session_state[ui.CASE_KEY] = case_id
    return at.run(timeout=TIMEOUT)


def _submit(env, case_id):
    """Run a demo case as the Home page does (test setup for the review and audit pages)."""
    with orchestrator.open_connection(env.config) as conn:
        return orchestrator.submit_demo_case(case_id, conn=conn, app=orchestrator.load_app())


def _values(elements):
    return [element.value for element in elements]


def _screen(at):
    """Every text shown on the page, whatever the element (for "never shown" checks)."""
    shown = []
    for kind in ("title", "header", "subheader", "text", "markdown", "caption", "error",
                 "warning", "info", "success", "code", "json"):
        shown += [str(value) for value in _values(getattr(at, kind))]
    for exception in at.exception:
        shown += [str(exception.message), str(exception.stack_trace)]
    return "\n".join(shown)


# --- every page: banner, start-up refusal, no raw error --------------------------------------------

@pytest.mark.parametrize("page", PAGES, ids=["home", "review", "audit"])
def test_banner_on_every_page(ui_env, page):
    """J02: the banner is visible on every page, also when nothing else can be shown."""
    at = _run(page)
    assert ui.BANNER_TEXT in _values(at.warning)
    assert "The score and the summary prove nothing" in ui.BANNER_TEXT
    assert not at.exception


@pytest.mark.parametrize("message", [orchestrator.STARTUP_MODEL_MESSAGE,
                                     orchestrator.STARTUP_CONFIG_MESSAGE])
@pytest.mark.parametrize("page", PAGES, ids=["home", "review", "audit"])
def test_startup_error_stops_without_database(ui_env, monkeypatch, page, message):
    """Q-19 (4), I74 P4: AppStartupError -> banner, the fixed message, then st.stop(): no database
    file, no other element; the text of the error is never shown (Q-41)."""
    def refuse():
        raise orchestrator.AppStartupError(message)
    monkeypatch.setattr(orchestrator, "load_app", refuse)
    at = _run(page, case_id="CASE-0901")
    assert _values(at.error) == [ui.ERROR_MESSAGES["AppStartupError"]]
    assert not ui_env.config.paths.runtime_db.exists()
    assert not at.text and not at.selectbox and not at.button and not at.subheader
    assert message not in _screen(at)
    assert not at.exception


@pytest.mark.parametrize("error", [ToolUnavailableError(SECRET), RuntimeError(SECRET)],
                         ids=["known", "unknown"])
@pytest.mark.parametrize("page, function", [(HOME, "list_review_queue"), (REVIEW, "get_case_view"),
                                            (AUDIT, "get_audit_rows")],
                         ids=["home", "review", "audit"])
def test_errors_never_show_raw_text(ui_env, monkeypatch, page, function, error):
    """J07, I72 D4: a known error -> its fixed message, an unknown one -> the general message; never
    str(error), never a trace."""
    def broken(*args, **kwargs):
        raise error
    monkeypatch.setattr(orchestrator, function, broken)
    at = _run(page, case_id="CASE-0901")
    expected = (ui.ERROR_MESSAGES["ToolUnavailableError"] if isinstance(error, ToolUnavailableError)
                else ui.GENERAL_ERROR_MESSAGE)
    assert expected in _values(at.error)
    assert SECRET not in _screen(at)
    assert not at.exception


# --- Home: element 1, J08, J09 ----------------------------------------------------------------------

def test_home_runs_the_chosen_case(ui_env):
    """Element 1: a case chosen in the list is run, then the review page shows it."""
    at = _run(HOME)
    assert at.selectbox(key="demo_case").options == [c["case_id"] for c in DEMO_CASES]
    at.selectbox(key="demo_case").set_value("CASE-0902")
    at.button(key="run_case").click().run(timeout=TIMEOUT)
    assert at.session_state[ui.CASE_KEY] == "CASE-0902"
    with ui_env.connect() as conn:
        row = conn.execute("SELECT state FROM cases WHERE case_id = 'CASE-0902'").fetchone()
    assert row["state"] == CaseState.HUMAN_REVIEW.value
    assert not at.exception


def test_home_typed_id_wins_and_double_click_creates_one_case(ui_env):
    """J09: two clicks on the same case -> one case, one intake event (G10)."""
    for _ in range(2):
        at = _run(HOME)
        at.text_input(key="typed_case_id").input("CASE-0901")
        at.button(key="run_case").click().run(timeout=TIMEOUT)
        assert not at.exception
    with ui_env.connect() as conn:
        assert conn.execute("SELECT COUNT(*) FROM cases").fetchone()[0] == 1
        intakes = conn.execute("SELECT COUNT(*) FROM audit_events WHERE action = 'transition' "
                               "AND state_from IS NULL").fetchone()[0]
    assert intakes == 1


def test_home_unknown_typed_id_shows_input_message(ui_env):
    """J07 "invalid input": unknown ID -> fixed message, nothing created."""
    at = _run(HOME)
    at.text_input(key="typed_case_id").input("CASE-9999")
    at.button(key="run_case").click().run(timeout=TIMEOUT)
    assert ui.ERROR_MESSAGES["ToolInputError"] in _values(at.error)
    assert "CASE-9999" not in "\n".join(_values(at.error))
    with ui_env.connect() as conn:
        assert conn.execute("SELECT COUNT(*) FROM cases").fetchone()[0] == 0


def test_home_queue_high_priority_first(ui_env):
    """J08: the queue is shown in the order of the orchestrator (G11), high priority first."""
    _submit(ui_env, "CASE-0901")
    _submit(ui_env, "CASE-0902")
    with ui_env.connect() as conn:  # plain SQL: one normal (older), one high (newer)
        conn.execute("UPDATE cases SET priority = 'normal', created_at = '2026-01-01T00:00:00+00:00' "
                     "WHERE case_id = 'CASE-0901'")
        conn.execute("UPDATE cases SET priority = 'high', created_at = '2026-01-02T00:00:00+00:00' "
                     "WHERE case_id = 'CASE-0902'")
    at = _run(HOME)
    lines = [text for text in _values(at.text) if text.startswith("CASE-")]
    assert [line.split(" ")[0] for line in lines] == ["CASE-0902", "CASE-0901"]
    assert "priority: high" in lines[0]


# --- Case review: elements 2 to 10 --------------------------------------------------------------------

def test_review_page_without_case(ui_env):
    at = _run(REVIEW)
    assert any("No case selected" in value for value in _values(at.info))
    assert not at.exception


def test_review_page_shows_elements_2_to_9(ui_env):
    """J03, J04: transaction fields, score + band + threshold, model, evidence, AI draft labelled for
    human review, references linked to the evidence, uncertainties, validator status."""
    _submit(ui_env, "CASE-0901")
    at = _run(REVIEW, case_id="CASE-0901")
    with orchestrator.open_connection(ui_env.config) as conn:
        view = orchestrator.get_case_view("CASE-0901", conn=conn, config=ui_env.config)
        draft = orchestrator.get_draft_view("CASE-0901", conn=conn, config=ui_env.config)
    texts = _values(at.text)
    subheaders = _values(at.subheader)
    table = at.table[0].value
    assert list(table["Field"]) == list(view.transaction)
    assert f"Model score: {view.outcome.score.score}" in texts
    assert f"Threshold used: {view.outcome.score.threshold}" in texts
    assert ui.BAND_BADGES[view.outcome.score.risk_band] in _values(at.markdown)
    assert f"Model name: {view.model_name}" in texts and f"Trained at: {view.trained_at}" in texts
    assert f"Model version: {view.outcome.score.model_version}" in texts
    assert "[EV-0901] Transaction type: TRANSFER." in texts
    assert "6. AI draft for human review" in subheaders
    assert any(c.startswith("AI draft for human review") for c in _values(at.caption))
    assert draft.summary in texts
    for line in draft.evidence_lines:  # element 7: each reference linked to the evidence list
        assert f"[{line.source_id}] {line.note} — evidence: {line.evidence_text}" in texts
    assert all(f"Reference {sid}: {text}" in texts for sid, text in draft.source_references)
    assert draft.evidence_lines and all(t is not None for _, t in draft.source_references)
    assert "8. Uncertainty notes" in subheaders
    assert all(f"- {note}" in texts for note in draft.uncertainties) and draft.uncertainties
    assert ui.VALIDATOR_BADGES["passed"] in _values(at.markdown)
    assert at.radio(key="decision").options == [ui.decision_label(d)
                                               for d in orchestrator.REVIEW_DECISIONS]
    assert not at.exception


def test_case_note_shown_as_plain_text(ui_env):
    """I72 D1, I73 (1): the note is in the folded box "Case note — unverified", with st.text only:
    its Markdown and HTML are never interpreted."""
    _submit(ui_env, "CASE-0901")
    at = _run(REVIEW, case_id="CASE-0901")
    assert [e.label for e in at.expander] == ["Case note — unverified"]
    assert TRAP_NOTE in _values(at.expander[0].text)
    others = [str(v) for kind in ("markdown", "caption", "error", "warning", "info", "success",
                                  "title", "header", "subheader") for v in _values(getattr(at, kind))]
    assert not [v for v in others if "TRAP-NOTE-77" in v]


@pytest.mark.validation_workflow
@pytest.mark.parametrize("decision", orchestrator.REVIEW_DECISIONS, ids=lambda d: d.value)
def test_review_decision_recorded_from_page(ui_env, decision):
    """J05 end to end: the decision chosen on the page is recorded (state, one audit event with the
    comment length only), then the page shows it, the comment as plain text (I72 D2)."""
    _submit(ui_env, "CASE-0901")
    at = _run(REVIEW, case_id="CASE-0901")
    at.radio(key="decision").set_value(decision)
    at.text_area(key="comment").input(COMMENT)
    at.button(key="record_decision").click().run(timeout=TIMEOUT)
    assert not at.exception
    with ui_env.connect() as conn:
        row = conn.execute("SELECT state, reviewer_decision, reviewer_comment FROM cases "
                           "WHERE case_id = 'CASE-0901'").fetchone()
        events = conn.execute("SELECT details_json FROM audit_events "
                              "WHERE action = 'review_decision'").fetchall()
    assert row["state"] == decision.value == row["reviewer_decision"]
    assert row["reviewer_comment"] == COMMENT
    assert [json.loads(e["details_json"]) for e in events] == [{"comment_length": len(COMMENT)}]
    assert "Decision recorded: " + ui.decision_label(decision) in _values(at.success)
    assert COMMENT in _values(at.text)
    assert "TRAP-COMMENT-55" not in "\n".join(str(v) for v in _values(at.markdown))
    assert not at.radio and not at.text_area  # no second decision from the page


@pytest.mark.validation_workflow
def test_rejected_case_shows_reasons_and_no_draft(ui_env):
    """H06, J04, J07 "validation failure": the reasons are shown, no draft, no decision form."""
    ui_env.maker.scenario = "prohibited_claim"
    outcome = _submit(ui_env, "CASE-0901")
    assert outcome.state is CaseState.VALIDATION_REJECTED
    at = _run(REVIEW, case_id="CASE-0901")
    assert ui.VALIDATION_FAILURE_MESSAGE in _values(at.error)
    assert ui.VALIDATOR_BADGES["failed"] in _values(at.markdown)
    assert all(f"- {reason}" in _values(at.text) for reason in outcome.validation_reasons)
    assert outcome.validation_reasons
    assert not any(c.startswith("AI draft for human review") for c in _values(at.caption))
    assert "8. Uncertainty notes" not in _values(at.subheader)
    assert not at.radio and not at.button
    assert not at.exception


def test_failed_case_shows_readable_tool_failure(ui_env):
    """J07 "tool failure": a FAILED case -> the message of its step, read in the audit (I72 D4);
    the fixed cause code is not shown on this page (it is in the audit trail)."""
    ui_env.maker.scenario = "timeout"
    outcome = _submit(ui_env, "CASE-0901")
    assert outcome.state is CaseState.FAILED
    at = _run(REVIEW, case_id="CASE-0901")
    assert ui.FAILURE_MESSAGES["draft"] in _values(at.error)
    assert outcome.failure_cause["cause"] not in _screen(at)
    assert ui.VALIDATOR_BADGES["not_run"] in _values(at.markdown)
    assert not at.radio
    assert not at.exception


def test_already_decided_elsewhere_shows_fixed_message(ui_env, monkeypatch):
    """J07: ReviewAlreadyRecordedError (another decision recorded in between, by another session)
    -> fixed message. The race is simulated: the orchestrator raises the error it would raise."""
    _submit(ui_env, "CASE-0901")
    at = _run(REVIEW, case_id="CASE-0901")

    def already(case_id, decision, comment=None, **kwargs):
        raise orchestrator.ReviewAlreadyRecordedError(case_id, CaseState.CLOSED, decision)
    monkeypatch.setattr(orchestrator, "record_review_decision", already)
    at.radio(key="decision").set_value(CaseState.ESCALATED)
    at.button(key="record_decision").click().run(timeout=TIMEOUT)
    assert ui.ERROR_MESSAGES["ReviewAlreadyRecordedError"] in _values(at.error)
    assert not at.exception


def test_comment_limit_is_the_repository_limit(ui_env):
    """I74 P8: max_chars of the text area = the single source in case_repository.py."""
    from src.storage.case_repository import REVIEWER_COMMENT_MAX_CHARS
    _submit(ui_env, "CASE-0901")
    at = _run(REVIEW, case_id="CASE-0901")
    assert at.text_area(key="comment").max_chars == REVIEWER_COMMENT_MAX_CHARS


# --- Audit trail: element 11 ------------------------------------------------------------------------

@pytest.mark.parametrize("case_id", [None, "CASE-0901"], ids=["all_cases", "one_case"])
def test_audit_page_rows_match_the_export(ui_env, case_id):
    """J06, I02: the table shows as many events as the CSV and JSON exports."""
    _submit(ui_env, "CASE-0901")
    _submit(ui_env, "CASE-0902")
    at = AppTest.from_file(AUDIT).run(timeout=TIMEOUT)
    if case_id is not None:
        at.text_input(key="audit_case_id").input(case_id).run(timeout=TIMEOUT)
    with orchestrator.open_connection(ui_env.config) as conn:
        csv_rows = list(csv.reader(io.StringIO(orchestrator.export_audit("csv", case_id, conn=conn))))
        json_rows = json.loads(orchestrator.export_audit("json", case_id, conn=conn))
    shown = len(at.dataframe[0].value)
    assert shown == len(csv_rows) - 1 == len(json_rows) > 0
    assert f"{shown} audit events" in _values(at.text)
    assert list(at.dataframe[0].value.columns) == csv_rows[0]
    assert not at.exception


def test_audit_page_unknown_case(ui_env):
    _submit(ui_env, "CASE-0901")
    at = AppTest.from_file(AUDIT).run(timeout=TIMEOUT)
    at.text_input(key="audit_case_id").input("CASE-9999").run(timeout=TIMEOUT)
    assert "0 audit events" in _values(at.text)
    assert "No audit event for this selection." in _values(at.info)
    assert not at.exception


# --- ui_components ----------------------------------------------------------------------------------

def test_error_table_names_are_real_errors():
    """I72 D4: every key of the table is an error class known to the orchestrator."""
    for name in ui.ERROR_MESSAGES:
        assert isinstance(getattr(orchestrator, name), type), name
        assert issubclass(getattr(orchestrator, name), Exception)


def test_error_messages_are_fixed():
    """Q-41: one message for AppStartupError, citing both fixes; never built from str(error);
    a subclass gets the message of its parent; anything else gets the general message."""
    startup = ui.ERROR_MESSAGES["AppStartupError"]
    assert "python -m src.train" in startup and "settings.yaml" in startup
    assert ui.error_message(orchestrator.AppStartupError(SECRET)) == startup
    assert ui.error_message(DuplicateSubmissionError(SECRET)) \
        == ui.ERROR_MESSAGES["ToolInputError"]
    assert ui.error_message(ToolInputError(SECRET)) == ui.ERROR_MESSAGES["ToolInputError"]
    assert ui.error_message(KeyError(SECRET)) == ui.GENERAL_ERROR_MESSAGE


def test_ui_components_never_use_the_error_text():
    """I72 D4, Q-41: no str(...), repr(...), format or f-string of the error in ui_components.py."""
    tree = ast.parse((APP_DIR / "ui_components.py").read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and getattr(node.func, "id", None) in {"str", "repr", "format"}:
            assert not any(isinstance(arg, ast.Name) and arg.id == "error" for arg in node.args)
        if isinstance(node, ast.FormattedValue):
            assert not (isinstance(node.value, ast.Name) and node.value.id == "error")
    assert "st.exception" not in (APP_DIR / "ui_components.py").read_text(encoding="utf-8")


def test_failure_message():
    assert ui.failure_message({"step": "score", "cause": "x"}) == ui.FAILURE_MESSAGES["score"]
    assert ui.failure_message({"step": "other", "cause": "x"}) == ui.GENERAL_FAILURE_MESSAGE
    assert ui.failure_message(None) == ui.GENERAL_FAILURE_MESSAGE


def test_get_app_loads_once_and_never_caches_a_failure():
    """I72 D3, I74 P6: one load per process; a failed load is tried again on the next run."""
    st.cache_resource.clear()
    calls = []

    def failing():
        calls.append("fail")
        raise orchestrator.AppStartupError("x")
    for _ in range(2):
        with pytest.raises(orchestrator.AppStartupError):
            ui.get_app(failing)
    assert calls == ["fail", "fail"]

    st.cache_resource.clear()
    sentinel = object()
    loaded = []
    assert ui.get_app(lambda: loaded.append(1) or sentinel) is sentinel
    assert ui.get_app(lambda: loaded.append(2) or object()) is sentinel
    assert loaded == [1]
    st.cache_resource.clear()


# --- imports and layers of app/ (I72 D3, I74 P3) ----------------------------------------------------

ALLOWED_APP_IMPORTS = {"__future__", "__future__.annotations", "streamlit","src.agent.orchestrator", "app.ui_components",
                       "app", "src.agent"}
APP_FILES = sorted(APP_DIR.rglob("*.py"))
PAGE_FILES = [path for path in APP_FILES if path.name != "ui_components.py"]


def _imports(tree):
    found = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            found |= {alias.name for alias in node.names}
        elif isinstance(node, ast.ImportFrom):
            found.add(node.module)
            found |= {f"{node.module}.{alias.name}" for alias in node.names}
    return found


def test_app_files_found():
    assert {path.name for path in APP_FILES} == {"ui_components.py", "Home.py", "1_Case_Review.py",
                                                 "2_Audit_Trail.py"}


@pytest.mark.parametrize("path", APP_FILES, ids=lambda path: path.name)
def test_app_imports_only_orchestrator(path):
    """I72 D3: app/ imports only streamlit, the orchestrator and ui_components (Architecture §1.2)."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    imports = _imports(tree)
    assert imports <= ALLOWED_APP_IMPORTS | {"typing", "typing.Any", "typing.Callable"}, imports
    if path.name == "ui_components.py":  # I74 P6: never the orchestrator
        assert not [m for m in imports if m.startswith("src")]
    else:
        assert "typing" not in imports


@pytest.mark.parametrize("path", PAGE_FILES, ids=lambda path: path.name)
def test_pages_never_read_the_configuration(path):
    """I74 P3: app.config is passed on as it is, never read (no .config.<field>, no .paths, .llm,
    no load_config)."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute):
            assert node.attr not in {"paths", "llm", "api_key", "load_config", "start_app"}
            assert not (isinstance(node.value, ast.Attribute) and node.value.attr == "config")
        if isinstance(node, ast.Name):
            assert node.id not in {"load_config", "open", "json"}


@pytest.mark.parametrize("path", PAGE_FILES, ids=lambda path: path.name)
def test_pages_never_render_markdown_or_html(path):
    """I72 D1, D2: no data can be interpreted — the pages never call st.markdown, st.write, st.html,
    and never pass unsafe_allow_html (the fixed badges are in ui_components)."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            assert node.func.attr not in {"markdown", "write", "html", "exception"}
            assert not [k for k in node.keywords if k.arg == "unsafe_allow_html"]


# --- J5, PR 16 — I75 (1): "Case ID" field on the review page opened without a case ---------------

def test_review_page_opens_a_case_by_typed_id(ui_env):
    """I75 (1): opened from the menu without a case, a typed existing ID opens that case."""
    _submit(ui_env, "CASE-0901")
    at = _run(REVIEW)
    at.text_input(key="open_case_id").input("  CASE-0901  ")  # spaces around are ignored
    at.button(key="open_case").click().run(timeout=TIMEOUT)
    assert not at.exception
    assert at.session_state[ui.CASE_KEY] == "CASE-0901"
    assert "Case ID: CASE-0901" in _values(at.text)
    assert "2. Verified transaction fields" in _values(at.subheader)


@pytest.mark.parametrize("typed", ["CASE-0999", "not-a-case <b>x</b>"])
def test_review_page_unknown_typed_id_shows_fixed_message(ui_env, typed):
    """Unknown or malformed ID -> the fixed ToolInputError message, no trace, the ID never shown
    and never kept, no case created."""
    _submit(ui_env, "CASE-0901")  # a database with one other case
    at = _run(REVIEW)
    at.text_input(key="open_case_id").input(typed)
    at.button(key="open_case").click().run(timeout=TIMEOUT)
    assert not at.exception
    assert _values(at.error) == [ui.ERROR_MESSAGES["ToolInputError"]]
    assert typed not in _screen(at)
    assert ui.CASE_KEY not in at.session_state
    with ui_env.connect() as conn:
        assert conn.execute("SELECT COUNT(*) FROM cases").fetchone()[0] == 1


@pytest.mark.parametrize("typed", ["", "   "])
def test_review_page_empty_typed_id_shows_fixed_message(ui_env, typed):
    """Empty ID -> fixed warning, nothing called (the database is not even opened)."""
    at = _run(REVIEW)
    at.text_input(key="open_case_id").input(typed)
    at.button(key="open_case").click().run(timeout=TIMEOUT)
    assert not at.exception
    assert "Enter a case ID to open a case." in _values(at.warning)
    assert not at.error
    assert ui.CASE_KEY not in at.session_state
    assert not ui_env.config.paths.runtime_db.exists()
