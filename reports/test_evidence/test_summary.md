# Test summary and failure evidence

> Deliverable G (brief §14, R300, R301, R308). Register n° 72. Every number and output below was copied
> from a real run: nothing is invented. Temporary folders are written `<tmp>`. Nothing from
> `data/runtime/` is versioned (`.gitignore`). No secret: the LLM client is the fake one, with an empty key.

- Date of the runs: 2026-11-20, 21:30 (+04:00)
- Code: commit `c58eb6c` on branch `tache/K02-tests-preuves` (this file and `PASSATION.md` are the only files added after it)
- Machine: the founder's local machine, `.venv` (Python 3.13); offline. No network, no paid service, no real LLM: the tests use the fake client (n° 56) and a small model fitted in `tests/conftest.py`

## 1. Test run (R300, R301)

| Command | Run | Passed | Failed |
|---|---|---|---|
| `.venv/bin/python -m pytest -q` | 734 | 734 | 0 |
| `.venv/bin/python -m pytest -q -m validation_workflow` | 81 (653 deselected) | 81 | 0 |

Real output (last lines):

```text
$ .venv/bin/python -m pytest -q
..............                                                           [100%]
734 passed in 24.13s

$ .venv/bin/python -m pytest -q -m validation_workflow
81 passed, 653 deselected in 5.40s
```

The counts are pytest items (a parametrized test counts once per parameter). The brief asks for at least 15 tests, at least
5 of them on the agent / LLM validation workflow: 734 and 81.

## 2. Coverage of the 26 example tests of brief §14 (R302–R307, K02)

Each test named below was run **on its own** (`.venv/bin/python -m pytest -q <file>::<name>`) on 2026-11-20 and passed.
"New" = added in this pull request (PR 16).

| # | Example (brief §14) | Test(s) | Status |
|---|---|---|---|
| 1 | Required columns exist | `tests/test_data_schema.py::test_load_raw_columns`, `::test_load_raw_invalid` | covered |
| 2 | Target has valid values | `tests/test_data_schema.py::test_validate_frame_target` (missing target) ; **new** `tests/test_s14_examples.py::test_target_value_outside_zero_one_refused` (2 and -1 refused) | covered |
| 3 | Missing data is handled | `tests/test_data_schema.py::test_validate_frame_target` (missing target refused) ; `tests/test_tools.py::test_invalid_input_rejected` (NaN / infinite amount refused in a case input) ; **new** `tests/test_s14_examples.py::test_missing_feature_value_is_not_refused_at_load` | covered — see limit 1 |
| 4 | The target is excluded from predictors | `tests/test_features.py::test_target_flag_and_ids_never_in_x` | covered |
| 5 | The train and test split is reproducible | `tests/test_split.py::test_same_seed_gives_same_rows` | covered |
| 6 | The training pipeline completes | `tests/test_models.py::test_four_candidates_give_valid_scores` (the 4 candidates trained on an invented set) | covered — see limit 2 |
| 7 | The model returns valid scores in the expected range | `tests/test_models.py::test_four_candidates_give_valid_scores` ; `tests/test_tools.py::test_untrustworthy_score_is_unavailable` | covered |
| 8 | A saved model can be loaded | `tests/test_models.py::test_save_then_reload_gives_same_scores` | covered |
| 9 | Metrics are calculated on held-out data | **new** `tests/test_s14_examples.py::test_test_metrics_use_only_held_out_rows` | covered |
| 10 | Valid tool arguments work | `tests/test_tools.py::test_intake_creates_case_received`, `::test_retrieve_known_case_returns_evidence` | covered |
| 11 | Unknown case IDs are handled safely | `tests/test_tools.py::test_retrieve_unknown_case_returns_empty` ; `tests/test_orchestrator.py::test_case_view_unknown_case` ; `tests/test_app.py::test_home_unknown_typed_id_shows_input_message` ; **new** `tests/test_app.py::test_review_page_unknown_typed_id_shows_fixed_message` | covered |
| 12 | Tool timeouts are handled and failures are logged | `tests/test_orchestrator.py::test_tool_timeout_leads_to_failed`, `::test_max_delay_recorded` | covered |
| 13 | Invalid state transitions are rejected | `tests/test_state_machine.py::test_invalid_transition_rejected` ; `tests/test_orchestrator.py::test_invalid_transition_audited` | covered |
| 14 | Valid JSON passes | `tests/test_validator.py::test_valid_draft_passes` | covered |
| 15 | Malformed JSON fails | `tests/test_validator.py::test_malformed_json_rejected` | covered |
| 16 | A missing required field causes rejection | `tests/test_validator.py::test_missing_field_rejected` (one per field) | covered |
| 17 | An invalid risk label causes rejection | `tests/test_validator.py::test_invalid_risk_label_rejected` | covered |
| 18 | Unsupported evidence IDs cause rejection | `tests/test_validator.py::test_unsupported_evidence_id_rejected` | covered |
| 19 | A model-score mismatch is detected | `tests/test_validator.py::test_model_score_mismatch_detected` | covered |
| 20 | A prohibited or unsupported claim is rejected or flagged | `tests/test_validator.py::test_prohibited_claim_rejected` | covered |
| 21 | Prompt injection in a case note is treated as untrusted input | `tests/test_security.py::test_prompt_injection_untrusted` | covered |
| 22 | Secrets are not written to logs | `tests/test_llm_client.py::test_key_never_shows_in_error_traceback_repr_or_log` ; **new** `tests/test_security.py::test_secrets_not_logged` | covered |
| 23 | No tool can execute a real financial action | `tests/test_tools.py::test_no_tool_offers_a_financial_action`, `::test_g12_checks_catch_a_planted_tool` | covered |
| 24 | Human review decisions are recorded | `tests/test_review_and_audit.py::test_review_decision_recorded` | covered |
| 25 | Validation failures are visible | `tests/test_app.py::test_rejected_case_shows_reasons_and_no_draft` ; `tests/test_orchestrator.py::test_case_view_rejected_case_shows_reasons_not_draft` | covered |
| 26 | Duplicate submissions are handled or documented | `tests/test_review_and_audit.py::test_duplicate_submission` ; `tests/test_app.py::test_home_typed_id_wins_and_double_click_creates_one_case` | covered |

Each new test was checked against a deliberately broken version of the code (mutation): the test fails when the
protection it checks is removed. For protected (frozen) modules the broken version was applied in memory with
`monkeypatch`, from a throwaway test outside the repository; no frozen file was opened.

## 3. Proof 1 — a malformed draft is rejected (R308)

Output of the script of section 5 (proof 1). The first block calls the validation tool (n° 52) directly; the second runs
the demo case `CASE-0001` through the orchestrator with the fake client scenario `malformed` on every attempt
(1 + 2 retries from `configs/settings.yaml`); the third is copied from the audit export of that case (JSON).

```text
=== PROOF 1: malformed draft rejected ===
-- 1a. direct call of the validation tool (n° 52) on a malformed draft
passed=False reasons=['malformed JSON: Expecting value (position 36)'] draft=None
-- 1b. run_case with the fake client scenario 'malformed' on every attempt
case_id=CASE-0001 state=VALIDATION_REJECTED draft=None
validation_reasons=['malformed JSON: Unterminated string starting at (position 39)']
-- 1c. audit export (JSON) of CASE-0001: LLM attempts and final transition
{"action": "tool_call", "actor": "llm", "details": {"attempt": 1, "duration_seconds": 4.070898285135627e-05, "error": null, "max_attempts": 3, "reasons": ["malformed JSON: Unterminated string starting at (position 39)"], "step": "draft", "timeout_seconds": 30.0}, "event_id": 6, "result": "rejected", "state_from": null, "state_to": null}
{"action": "tool_call", "actor": "llm", "details": {"attempt": 2, "duration_seconds": 3.720802487805486e-05, "error": null, "max_attempts": 3, "reasons": ["malformed JSON: Unterminated string starting at (position 39)"], "step": "draft", "timeout_seconds": 30.0}, "event_id": 7, "result": "rejected", "state_from": null, "state_to": null}
{"action": "tool_call", "actor": "llm", "details": {"attempt": 3, "duration_seconds": 2.6958005037158728e-05, "error": null, "max_attempts": 3, "reasons": ["malformed JSON: Unterminated string starting at (position 39)"], "step": "draft", "timeout_seconds": 30.0}, "event_id": 8, "result": "rejected", "state_from": null, "state_to": null}
{"action": "transition", "actor": "llm", "details": {"attempts": 3}, "event_id": 9, "result": "ok", "state_from": "EVIDENCE_READY", "state_to": "DRAFTED"}
{"action": "transition", "actor": "validator", "details": {"attempts": 3, "reasons": ["malformed JSON: Unterminated string starting at (position 39)"]}, "event_id": 10, "result": "rejected", "state_from": "DRAFTED", "state_to": "VALIDATION_REJECTED"}
```

The same rule, as an automated test:

```text
$ .venv/bin/python -m pytest -v tests/test_validator.py::test_malformed_json_rejected
tests/test_validator.py::test_malformed_json_rejected PASSED             [100%]
============================== 1 passed in 0.10s ===============================
```

## 4. Proof 2 — an audit entry showing a tool failure (R308)

Output of the script of section 5 (proof 2). The demo case `CASE-0004` is run with the evidence store pointing to a file that
does not exist (`<tmp>/missing.json`): `retrieve_case_evidence` raises a real `ToolUnavailableError` (no test double, no
monkeypatch). The lines are copied from the audit export (`orchestrator.export_audit("json", "CASE-0004")`, which reads
`audit_export.py`, n° 65).

```text
=== PROOF 2: audit entry of a tool failure ===
-- evidence store = <tmp>/missing.json (file absent): a real ToolUnavailableError
case_id=CASE-0004 state=FAILED failure_cause={'step': 'evidence', 'cause': 'retrieve_case_evidence:failed'}
-- audit export (JSON) of CASE-0004: evidence tool attempts and the transition to FAILED
{"action": "tool_call", "actor": "tool:retrieve_case_evidence", "details": {"attempt": 1, "duration_seconds": 5.1540962886065245e-05, "error": "ToolUnavailableError", "max_attempts": 3, "reasons": [], "step": "evidence", "timeout_seconds": 5.0}, "event_id": 4, "result": "failed", "state_from": null, "state_to": null}
{"action": "tool_call", "actor": "tool:retrieve_case_evidence", "details": {"attempt": 2, "duration_seconds": 3.925000783056021e-05, "error": "ToolUnavailableError", "max_attempts": 3, "reasons": [], "step": "evidence", "timeout_seconds": 5.0}, "event_id": 5, "result": "failed", "state_from": null, "state_to": null}
{"action": "tool_call", "actor": "tool:retrieve_case_evidence", "details": {"attempt": 3, "duration_seconds": 2.9125018045306206e-05, "error": "ToolUnavailableError", "max_attempts": 3, "reasons": [], "step": "evidence", "timeout_seconds": 5.0}, "event_id": 6, "result": "failed", "state_from": null, "state_to": null}
{"action": "transition", "actor": "system", "details": {"cause": "retrieve_case_evidence:failed", "step": "evidence"}, "event_id": 7, "result": "failed", "state_from": "SCORED", "state_to": "FAILED"}
```

The audit stores the error class name only (`ToolUnavailableError`), never the error text.

## 5. How proofs 1 and 2 were produced

Save the script below **outside the repository** as `capture_failures.py`, create an empty folder `<tmp>`, then run from the
repository root:

```bash
.venv/bin/python - <tmp> < capture_failures.py
```

Requirements: the trained model in `artifacts/models/` (`python -m src.train`, J3; the two files the app loads are versioned since J6). The script builds its
configuration by hand from `configs/settings.yaml`: it never calls `load_config()` and never reads `.env`; the LLM client is
the fake one. It writes only into `<tmp>` (one SQLite file per proof). Durations (`duration_seconds`) change from run to run.

```python
# Failure evidence for reports/test_evidence/test_summary.md (R308). Run from the repository root:
#   .venv/bin/python - <tmp> < capture_failures.py
# Builds the AppConfig by hand: never load_config(), never .env (fake LLM client, empty key).
# Uses the local trained model (artifacts/models/, read only) and the versioned demo files.
# Writes only into <tmp>: a fresh SQLite database; nothing in data/runtime/.
import json
import sys
from pathlib import Path

import yaml

from src.agent import orchestrator
from src.agent.llm.fake_client import DraftFacts, FakeLLMClient
from src.agent.tools.score_transaction import load_scoring_model
from src.agent.tools.validate_investigation_json import validate_investigation_json
from src.config import AppConfig, LLMSettings, Paths, RetrySettings, Secret, SplitSettings

tmp = Path(sys.argv[1])
s = yaml.safe_load(Path("configs/settings.yaml").read_text(encoding="utf-8"))
p = {name: Path(value) for name, value in s["paths"].items()}


def make_config(evidence_store: Path, db: Path) -> AppConfig:
    return AppConfig(
        tool_retries=RetrySettings(s["retries"]["tools"]["max_retries"],
                                   float(s["retries"]["tools"]["timeout_seconds"])),
        llm_retries=RetrySettings(s["retries"]["llm"]["max_retries_after_rejection"],
                                  float(s["retries"]["llm"]["timeout_seconds"])),
        near_threshold_margin=s["routing"]["near_threshold_margin"],
        review_capacity_per_day=s["routing"]["review_capacity_per_day"],
        split=SplitSettings(**s["split"]),
        paths=Paths(raw_data_dir=p["raw_data_dir"], runtime_db=db, demo_cases=p["demo_cases"],
                    evidence_store=evidence_store, model_pipeline=p["model_pipeline"],
                    mlp_state=p["mlp_state"], model_metadata=p["model_metadata"],
                    metrics_dir=p["metrics_dir"], figures_dir=p["figures_dir"],
                    prohibited_terms=p["prohibited_terms"]),
        llm=LLMSettings(provider="fake", base_url="", model="", api_key=Secret("")),
    )


model = load_scoring_model(p["model_pipeline"], p["model_metadata"])


def run(case_id, scenario, evidence_store, db):
    config = make_config(evidence_store, db)
    app = orchestrator.AppResources(
        config=config, scoring_model=model,
        make_llm_client=lambda cid, score, ev: FakeLLMClient(scenario,
                                                             DraftFacts.from_official(cid, score, ev)))
    with orchestrator.open_connection(config) as conn:
        outcome = orchestrator.submit_demo_case(case_id, conn=conn, app=app)
        audit = json.loads(orchestrator.export_audit("json", case_id, conn=conn))
    return outcome, audit


def show(events, keep):
    for e in events:
        if keep(e):
            print(json.dumps({k: e[k] for k in ("event_id", "actor", "action", "state_from",
                                                 "state_to", "result", "details")}, sort_keys=True))


print("=== PROOF 1: malformed draft rejected ===")
print("-- 1a. direct call of the validation tool (n° 52) on a malformed draft")
outcome, audit = run("CASE-0001", "malformed", p["evidence_store"], tmp / "proof1.db")
result = validate_investigation_json('{"case_id": "CASE-0001", "summary": ', outcome.score,
                                     "CASE-0001", outcome.evidence or [], p["prohibited_terms"])
print(f"passed={result.passed} reasons={list(result.reasons)} draft={result.draft}")
print("-- 1b. run_case with the fake client scenario 'malformed' on every attempt")
print(f"case_id={outcome.case_id} state={outcome.state.value} draft={outcome.draft}")
print(f"validation_reasons={list(outcome.validation_reasons)}")
print("-- 1c. audit export (JSON) of CASE-0001: LLM attempts and final transition")
show(audit, lambda e: e["action"] in ("tool_call", "transition") and
     (e["actor"].startswith("llm") or e["state_to"] in ("DRAFTED", "VALIDATION_REJECTED")))

print()
print("=== PROOF 2: audit entry of a tool failure ===")
print("-- evidence store = <tmp>/missing.json (file absent): a real ToolUnavailableError")
outcome, audit = run("CASE-0004", "valid", tmp / "missing.json", tmp / "proof2.db")
print(f"case_id={outcome.case_id} state={outcome.state.value} failure_cause={outcome.failure_cause}")
print("-- audit export (JSON) of CASE-0004: evidence tool attempts and the transition to FAILED")
show(audit, lambda e: e["actor"] == "tool:retrieve_case_evidence" or e["state_to"] == "FAILED")
```

The script is read on standard input (`-`) so that the repository root is on the import path.

## 6. Application screenshots (founder)

Captured by the founder on 2026-11-25 (dry run, +04:00) after a real launch: `.venv/bin/python -m streamlit run app/Home.py`,
real local model, **no `.env` file → fake LLM client** (`src/config.py`: `DEFAULT_PROVIDER = "fake"`; `LLM_PROVIDER` empty in the
shell). Fresh runtime database at the start of the run. The banner is visible on every page. Files are in
[`screenshots/`](screenshots/); a long page is split into several images (a, b, c…).

| # | Page | Case / action | What must be visible | File(s) |
|---|---|---|---|---|
| 1 | Home | Start of the app | Banner "Educational prototype — synthetic data only…"; demo case list; review queue (high priority first) | `s1_home.png` |
| 2 | Case review | CASE-0006, validated, high band (score 0.99986), in human review | Verified fields, score + band + threshold, model version, evidence `EV-0019`…`EV-0023`, "AI draft for human review" with its references, uncertainty notes, validator status "passed", decision buttons | `s2a`…`s2e_case_review_case0006.png` |
| 3 | Case review | CASE-0006 after the decision "Escalate" with a comment | "Decision recorded: Escalate" and the comment as plain text | `s3_decision_case0006.png` |
| 4 | Case review | CASE-0001, rejected draft (fake client scenario `malformed`, see note) | Validation failure message, the reason ("malformed JSON…"), **no** draft shown, validator status "failed" | `s4a`…`s4c_rejected_case0001.png` |
| 5 | Case review | CASE-0004 in FAILED after a tool failure (evidence store unavailable, see note) | The fixed failure message of the step; no trace; validator "not run"; no decision possible | `s5a`, `s5b_failed_case0004.png` |
| 6 | Case review | Opened from the menu without a case; unknown ID `CASE-9999` typed | The fixed "input was refused" message; the typed ID is not repeated in the message | `s6_unknown_case_id.png` |
| 7 | Audit trail | The FAILED case of screenshot 5 | 3 `tool_call` rows of `tool:retrieve_case_evidence` with result `failed` (`ToolUnavailableError`), then the transition SCORED → FAILED; number of events; CSV and JSON export buttons | `s7a`, `s7b_audit_case0004.png` |
| 8 | Audit trail | The rejected case of screenshot 4 | 3 `tool_call` rows of `llm` with result `rejected`, then DRAFTED → VALIDATION_REJECTED | `s8a`, `s8b_audit_case0001.png` |

**How the two failures were produced (provoked on purpose, no code changed).** The running app always uses the fake client
scenario `valid`, so a failure never happens on its own: it was injected, and only its cause is simulated.

- **Screenshots 4 and 8 — malformed draft.** *Simulated:* the LLM answer only (malformed JSON on every attempt). *Real:* the
  model score, the evidence, the validator that rejects, the 2 new attempts, the state machine (`VALIDATION_REJECTED`), the audit
  and the screen without a draft. Produced by the script below, kept outside the repository and run once, app stopped, from the
  repository root: `.venv/bin/python - < seed_rejected_case.py`. Output: `case_id=CASE-0001 state=VALIDATION_REJECTED draft=None`,
  `validation_reasons=['malformed JSON: Unterminated string starting at (position 39)']`.
- **Screenshots 5 and 7 — tool failure.** *Simulated:* the absence of the evidence file only
  (`mv data/demo/evidence_store.json data/demo/evidence_store.json.off`, CASE-0004 submitted in the app, then the file moved back;
  `git status` clean afterwards). *Real:* the `ToolUnavailableError` raised by `retrieve_case_evidence`, the 3 attempts, `FAILED`,
  the audit and the fixed message.
- During the dry run, CASE-0003 (no evidence, medium band) was escalated by mistake with a comment meant for CASE-0006; no
  screenshot uses it, and the demo video is recorded from a fresh database.

<details><summary>Script used for screenshots 4 and 8 (<code>seed_rejected_case.py</code>)</summary>

```python
# Dry run (J6, step 4): put ONE rejected case into the app's own database, so that the Streamlit app can
# show a malformed-output example (video element 4, screenshots 4 and 8 of test_summary.md §6).
# Adapted from capture_failures.py (test_summary.md §5). Kept OUTSIDE the repository; changes no code.
# Run from the repository root, app stopped:
#   .venv/bin/python - < ../../01_sessions/J6_essai/seed_rejected_case.py
# What it does: submits CASE-0001 with the fake LLM client forced to the scenario "malformed" on every
# attempt (1 + 2 retries from configs/settings.yaml), using the real local model and the versioned demo files.
# It builds the configuration by hand from configs/settings.yaml: never load_config(), never .env
# (fake client, empty key). It writes only into data/runtime/capstone.db (git-ignored).
import sys
from pathlib import Path

import yaml

from src.agent import orchestrator
from src.agent.llm.fake_client import DraftFacts, FakeLLMClient
from src.agent.tools.score_transaction import load_scoring_model
from src.config import AppConfig, LLMSettings, Paths, RetrySettings, Secret, SplitSettings

CASE_ID = "CASE-0001"
SCENARIO = "malformed"

s = yaml.safe_load(Path("configs/settings.yaml").read_text(encoding="utf-8"))
p = {name: Path(value) for name, value in s["paths"].items()}
db = p["runtime_db"]  # data/runtime/capstone.db, the database the app reads
db.parent.mkdir(parents=True, exist_ok=True)

config = AppConfig(
    tool_retries=RetrySettings(s["retries"]["tools"]["max_retries"],
                               float(s["retries"]["tools"]["timeout_seconds"])),
    llm_retries=RetrySettings(s["retries"]["llm"]["max_retries_after_rejection"],
                              float(s["retries"]["llm"]["timeout_seconds"])),
    near_threshold_margin=s["routing"]["near_threshold_margin"],
    review_capacity_per_day=s["routing"]["review_capacity_per_day"],
    split=SplitSettings(**s["split"]),
    paths=Paths(raw_data_dir=p["raw_data_dir"], runtime_db=db, demo_cases=p["demo_cases"],
                evidence_store=p["evidence_store"], model_pipeline=p["model_pipeline"],
                mlp_state=p["mlp_state"], model_metadata=p["model_metadata"],
                metrics_dir=p["metrics_dir"], figures_dir=p["figures_dir"],
                prohibited_terms=p["prohibited_terms"]),
    llm=LLMSettings(provider="fake", base_url="", model="", api_key=Secret("")),
)
model = load_scoring_model(p["model_pipeline"], p["model_metadata"])
app = orchestrator.AppResources(
    config=config, scoring_model=model,
    make_llm_client=lambda cid, score, ev: FakeLLMClient(SCENARIO, DraftFacts.from_official(cid, score, ev)))

with orchestrator.open_connection(config) as conn:
    outcome = orchestrator.submit_demo_case(CASE_ID, conn=conn, app=app)

print(f"database={db}")
print(f"case_id={outcome.case_id} state={outcome.state.value} draft={outcome.draft}")
print(f"validation_reasons={list(outcome.validation_reasons)}")
if outcome.state.value != "VALIDATION_REJECTED":
    sys.exit("UNEXPECTED: the case did not end in VALIDATION_REJECTED — stop and show this output")
```
</details>

## 7. Known limits

1. **Missing feature values**: no imputation exists. PaySim has 0 missing values (nb02 R063); the written rule (data/README.md §4,
   R081) refuses a missing target and does not refuse a missing feature at load time. The behaviour of the model step on a
   missing feature value is not defined; a missing amount in a case input is refused (`parse_case_input`).
2. **Training pipeline**: the tests train the 4 candidates on an invented set; the full `python -m src.train` on PaySim cannot run in
   CI (`data/raw/` is not versioned).
3. **Proofs 1 and 2** need the trained model: they are run locally, not in CI.
4. **Fake client, case without evidence (Q-52, open)**: the summary now says that no evidence item is listed (I75 (2)), but the
   recommended review step of the fake "valid" draft still reads "Review the transaction details and the evidence items listed."
   Left unchanged by decision of the founder.
5. **No real LLM** was used in any test or proof; drafts of a real model may be rejected more often (prohibited terms).
