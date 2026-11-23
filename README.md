# fraud-risk-intelligence-prototype

> **Educational prototype. Synthetic data only. No real payment rails and no financial actions.**
> Northstar Payments is a fictional company. This project uses synthetic data only, never connects to
> real payment rails, and never freezes accounts, blocks transactions, accuses customers or initiates
> any financial action. Every risk output is a recommendation for a human investigator, who decides.

## 1. Project overview

Northstar Payments (fictional) wants its fraud investigators to spend their limited review time on the
right transactions. This prototype combines four parts:

1. **A fraud-risk model** trained on the PaySim synthetic dataset. It scores a transaction and assigns a
   risk band (low / medium / high) using a decision threshold chosen for a review capacity of
   300 cases per day.
2. **An agentic investigation workflow** with an explicit state machine
   (`RECEIVED → SCORED → EVIDENCE_READY → DRAFTED → VALIDATED` or `VALIDATION_REJECTED`
   `→ HUMAN_REVIEW →` the reviewer's outcome `CLOSED`, `ESCALATED` or `NEEDS_MORE_INFORMATION`;
   `FAILED` when a step cannot complete). Callable tools score the case, retrieve approved evidence,
   ask the LLM for a draft and validate it. Retries and timeouts are bounded.
3. **An LLM drafting step with a validator.** The LLM writes a structured investigation draft (JSON)
   from verified facts and approved evidence only. A deterministic validator rejects malformed JSON,
   missing fields, invalid risk labels, unsupported evidence IDs, score mismatches and prohibited claims.
   A rejected draft is never shown as reliable.
4. **A Streamlit application** for the human reviewer: case intake and review queue (`app/Home.py`),
   case review with the decision form (`app/pages/1_Case_Review.py`) and the audit trail with CSV / JSON
   export (`app/pages/2_Audit_Trail.py`). Every step is written to an append-only audit log (SQLite).

**LLM: hosted API or local model?** By default the prototype uses **neither**: `LLM_PROVIDER=fake`
runs an offline scripted client (no network, no cost). All tests, the failure evidence and the demo
video use this client. The same interface also accepts any provider or local server that speaks the
OpenAI-compatible protocol (`LLM_PROVIDER=openai_compatible`, see section 2).

**What data leaves the machine?** With the default `fake` client, nothing. With a hosted provider, only
the synthetic facts of the case under review are sent: verified transaction fields, model score and
version, approved evidence items, and the case note, marked as untrusted data. The target label
(`isFraud`), secrets and raw files are never sent. The data are synthetic, so no real
customer data can leave the machine.

Main results (test set, evaluated once, after the model and the threshold were fixed on validation):

| Model | PR-AUC | ROC-AUC | Precision | Recall | F1 | Threshold |
|---|---|---|---|---|---|---|
| Random Forest (final) | 0.908 | 0.999 | 0.776 | 0.863 | 0.817 | 0.5492 |

Source: `artifacts/metrics/test_results.json` (954,393 test rows, 1,232 frauds: 1,063 caught, 169 missed,
307 false alerts). Candidate comparison on validation: `artifacts/metrics/comparison_table.csv`.

## 2. Environment setup and environment variables

Python 3.13 (the pinned versions in `requirements.txt` also support Python 3.11). From the repository root:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # then edit .env; it is git-ignored and must never be committed
```

| Variable | Purpose | Required |
|---|---|---|
| `LLM_PROVIDER` | `fake` (default: offline scripted client, no network, no cost) or `openai_compatible` | No — defaults to `fake` |
| `LLM_BASE_URL` | Base URL of any provider or local server that speaks the OpenAI protocol | Only with `openai_compatible` |
| `LLM_MODEL` | Model name, as the provider expects it | Only with `openai_compatible` |
| `LLM_API_KEY` | Secret key — kept in `.env` only, never printed or logged | Only with `openai_compatible` |

Non-secret operating settings (bounded retries, timeouts, review routing, data split, file paths) live in
`configs/settings.yaml`. The decision threshold and the risk-band bounds are produced by training and
stored with the model in `artifacts/models/model_metadata.json`.

## 3. Dataset acquisition

The raw data is **not** redistributed in this repository (`data/raw/` is git-ignored).

1. Download the PaySim dataset from Kaggle: <https://www.kaggle.com/datasets/ealaxi/paysim1>
   ("Synthetic Financial Datasets For Fraud Detection", Edgar Lopez-Rojas, licence CC BY-SA 4.0).
   A free Kaggle account is required.
2. Place the CSV file in `data/raw/` under its original name:
   `data/raw/PS_20174392719_1491204439457_log.csv` (6,362,620 rows, 11 columns).
3. Do not modify the file. All access goes through `load_raw()` (`src/data/load_paysim.py`), which checks
   the schema.

The dataset record, the data dictionary, the 12 known limitations and the data-quality decisions are in
[`data/README.md`](data/README.md). The full exploratory analysis is in `notebooks/02_eda_complete.ipynb`
(the first exploration is `notebooks/01_eda.ipynb`).

## 4. Training, evaluation and model artefact generation

```bash
python -m src.train
```

One command runs the whole chain: load and validate the data → stratified split 70 / 15 / 15 with seed 42
(`configs/settings.yaml`) → train the candidates (prior baseline, logistic regression, Random Forest, MLP
in PyTorch) → choose the final model and the threshold on **validation** → explanation (permutation
importance) on validation → **one** evaluation on the test set → save the artefacts.
The classical models are trained on a stratified sample of 1,000,000 training rows.
On the author's laptop the full run took about 4 minutes.

Generated artefacts:

| Path | Content | Versioned |
|---|---|---|
| `artifacts/models/final_pipeline.joblib`, `mlp_state.pt` | Saved model pipeline and MLP weights | No (regenerate with the command above) |
| `artifacts/models/model_metadata.json` | Model name, input columns, split, threshold, risk-band bounds | No (regenerated) |
| `artifacts/metrics/` | `comparison_table.csv`, `threshold_analysis.csv`, `error_analysis.csv`, `test_results.json` | Yes |
| `artifacts/figures/` | `fig01`–`fig06` (EDA, notebook 01), `fig07`–`fig10` (training), `eda2_*` (notebook 02) | Yes |

Changing a value in the `split` section of `configs/settings.yaml` is a new experiment: retrain and report
the new numbers.

## 5. Application launch and test execution

**Launch the application** (the trained model from section 4 must exist; otherwise the app shows a fixed
message and stops):

```bash
.venv/bin/python -m streamlit run app/Home.py
```

The app opens in the browser. The demo cases (`data/demo/cases.json`) and the approved evidence store
(`data/demo/evidence_store.json`) are versioned. The SQLite database `data/runtime/capstone.db` is
created at launch and is not versioned. Delete it to start from an empty audit log.

**Run the tests:**

```bash
.venv/bin/python -m pytest -q                         # all tests
.venv/bin/python -m pytest -q -m validation_workflow  # agent / LLM validation workflow only
```

Last recorded run (2026-11-20): 734 passed; 81 passed for `validation_workflow`. The tests run offline with
the fake LLM client and a small model fitted in `tests/conftest.py`, so they do not need the PaySim file or
the trained model. Test evidence (coverage of the 26 example tests of the brief, failure proofs, how they were
produced): [`reports/test_evidence/test_summary.md`](reports/test_evidence/test_summary.md).

Continuous integration (`.github/workflows/ci.yml`) runs the tests on every pull request to `main` and on every push to `main`.

To re-execute the notebooks, `nbconvert` and `ipykernel` are also needed (not in `requirements.txt`):
`pip install nbconvert ipykernel`.

## 6. Known limitations

1. **Synthetic data, synthetic results.** The model learns the PaySim simulator, not real customers. Its
   scores on PaySim likely overestimate performance on real transactions of any bank.
2. **Simulator artefacts in the features.** `error_balance_orig` / `error_balance_dest` capture balance
   inconsistencies that separate fraud almost perfectly in PaySim, and `hour_of_day` partly learns the
   simulator's fraud-injection rhythm (`data/README.md`, limitations 3 and 4). Part of the reported
   PR-AUC comes from these shortcuts.
3. **Random split across simulated time.** The split is stratified and random, not chronological. With the
   strong volume changes across steps, it can leak future behaviour into training.
4. **Fraud only in TRANSFER and CASH_OUT.** A fraud pattern on another transaction type would not be learned.
5. **Fairness cannot be measured.** The dataset has no customer attribute, only synthetic identifiers.
6. **No real LLM was tested.** All tests and proofs use the fake client. A real model may have its drafts
   rejected more often (prohibited terms, format).
7. **State and audit are written in two separate transactions.** A crash between the two writes could leave
   a state change without its audit line, or the reverse.
8. **Fake client wording for a case without evidence.** The recommended review step of the fake draft still
   says "Review the transaction details and the evidence items listed" when no evidence is listed.
9. **Training is not run in CI.** The PaySim file and the trained model are not versioned, so the full
   training and the two failure proofs can only be reproduced locally.
10. **Local prototype.** No authentication, single user, SQLite. Not designed for production or for any
    real decision.

## Licence and attribution

Dataset: PaySim (Edgar Lopez-Rojas), Kaggle, CC BY-SA 4.0. Main libraries: pandas, NumPy, scikit-learn,
PyTorch, Streamlit, pydantic, openai (client only), PyYAML, python-dotenv, pytest — exact versions in
`requirements.txt`.
