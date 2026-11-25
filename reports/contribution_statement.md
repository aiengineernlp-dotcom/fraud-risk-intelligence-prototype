# Contribution and Originality Statement

**Project:** Fraud Risk Intelligence Prototype — Capstone Project 1. **Team:** one member, Erman (GitHub: aiengineernlp-dotcom).

## 1. Member contribution
Erman worked alone and held every role: requirements, data documentation and EDA, features, models and threshold, agent
workflow, tools, LLM prompt and validator, Streamlit application, tests, report, slides and video. He made every recorded
design decision, reviewed and merged every pull request, ran the training, tests, dry run and screenshots, and
is responsible for all the work submitted.

## 2. External data and code sources
- **Dataset:** PaySim, "Synthetic Financial Datasets For Fraud Detection", E. Lopez-Rojas, Kaggle (Lopez-Rojas, Elmir &
  Axelsson, 2016), CC BY-SA 4.0, downloaded 2026-10-27, not redistributed. Demo cases and evidence were built from held-out
  PaySim test rows.
- **Code:** no third-party source code was copied; the code was written in this project with AI assistance (section 3).
  Common design patterns: repository, finite state machine, OpenAI-compatible client, scikit-learn `Pipeline`.

## 3. AI tool usage
We used Claude (Anthropic) as a chat assistant for planning, explanations, early code proposals (retyped and checked by the
author), reviews and drafting documents, including the report and this statement; Claude Code as a coding agent from the
agent phase, only in separate branches, each pull request checked by the author, continuous integration and comprehension
questions before merging; and ChatGPT (OpenAI) to understand course concepts, proofread or rephrase text, and check code.
We reviewed, tested, and modified the output. All reported results were generated from our documented experiments.
External sources and reused material are cited. Individual team-member contributions are listed above.

## 4. Reused libraries and third-party assets
NumPy, pandas, scikit-learn, joblib, seaborn, PyTorch, python-dotenv (BSD-3-Clause); Matplotlib (PSF-based); Streamlit,
openai SDK as a client only (Apache-2.0); pydantic, PyYAML, pytest (MIT); for documentation only, Graphviz (EPL), docx and
pptxgenjs (MIT). Versions: `requirements.txt`. No third-party images, fonts or assets.

## 5. Sign-off
Complete and honest to the best of my knowledge. Signed: Erman — 25 November 2026
