# fraud-risk-intelligence-prototype

> **Educational prototype. Synthetic data only. No real payment rails and no financial actions.**
> Northstar Payments is a fictional company. This project uses synthetic data only, never connects to
> real payment rails, and never freezes accounts, blocks transactions, accuses customers or initiates
> any financial action.

## 1. Project overview
_To be completed at J6 (final README)._

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

Non-secret operating settings (bounded retries, timeouts, file paths) live in `configs/settings.yaml`.
The decision threshold and risk-band bounds are produced by training and stored with the model.

## 3. Dataset acquisition
_To be completed at J2. Raw data is never redistributed in this repository._

## 4. Training, evaluation and model artefact generation
_To be completed at J3._

## 5. Application launch and test execution
_To be completed at J5._

## 6. Known limitations
_To be completed at J3 → J6._