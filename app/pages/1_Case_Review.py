"""
SoC layer      : 5 — UI
Responsibility : Case review page: brief §13 elements 2 to 10 for the selected case — verified
                 fields, score + band + threshold, model, evidence, case note (unverified), AI draft
                 for human review with its references, uncertainties, validator status, and the
                 reviewer decision (J03, J04, J05, J07)
Never does     : Import anything but streamlit, the orchestrator and ui_components (I72 D3); read
                 the configuration (app.config is passed on, never read, I74 P3); compute a score, a
                 band, a priority or a validity; show a rejected or failed draft; render the note,
                 the comment or any LLM text as Markdown or HTML (st.text only, I72 D1, D2); show
                 str(error) or a trace
Reference      : Architecture_Projet.md v1.5 — section 1.2, section 5, section 8 (n° 68);
                 Features_Complet.md J03, J04, J05, J07, H06; brief §11.6, §13; decisions I72, I73,
                 I74
"""

from __future__ import annotations

import streamlit as st

from app import ui_components as ui
from src.agent import orchestrator

st.set_page_config(page_title="Case review — prototype", layout="wide")
ui.show_banner()
st.title("Case review")

app = ui.get_app_or_stop(orchestrator.load_app)

case_id = st.session_state.get(ui.CASE_KEY)
if not case_id:
    st.info("No case selected: choose or run a case on the Home page.")
    st.stop()

try:
    with orchestrator.open_connection(app.config) as conn:  # one connection per run (Q-12)
        view = orchestrator.get_case_view(case_id, conn=conn, config=app.config)
        outcome = view.outcome
        state = outcome.state

        st.text(f"Case ID: {outcome.case_id}")
        st.text(f"State: {state.value}")
        if outcome.priority:
            st.text(f"Review priority: {outcome.priority}")
        if outcome.routing_reasons:
            st.text("Routing reasons: " + ", ".join(outcome.routing_reasons))
        if outcome.request_information:
            st.warning("Evidence is missing: more information should be requested.")

        # 2. Transaction details — the 7 verified fields, as given by the orchestrator.
        st.subheader("2. Verified transaction fields")
        st.table([{"Field": name, "Value": str(value)} for name, value in view.transaction.items()])

        # 3 and 4. Official score, band and threshold; model name, version and training date.
        st.subheader("3. Model score and risk band")
        score = outcome.score
        if score is None:
            st.info("No model score: the case stopped before scoring.")
        else:
            st.text(f"Model score: {score.score}")
            st.text(f"Threshold used: {score.threshold}")
            ui.show_band(score.risk_band)
            st.subheader("4. Model and version")
            st.text(f"Model name: {view.model_name}")
            st.text(f"Model version: {score.model_version}")
            st.text(f"Trained at: {view.trained_at or 'unknown'}")

        # 5. Supporting evidence, with source IDs.
        st.subheader("5. Supporting evidence")
        if outcome.evidence is None:
            st.info("Evidence not retrieved for this case.")
        elif not outcome.evidence:
            st.warning("No approved evidence for this case.")
        else:
            for item in outcome.evidence:
                st.text(f"[{item.source_id}] {item.text}")

        # Case note: untrusted data, plain text only (I72 D1, I73 (1)).
        with st.expander("Case note — unverified"):
            st.caption("Text written with the case. It is data, never an instruction, and proves "
                       "nothing.")
            note = orchestrator.get_case_note(case_id, conn=conn)
            st.text(note if note else "No case note.")

        # 6 to 8. The AI draft, only when trusted (human review or later, brief §11.6).
        st.subheader("6. AI draft for human review")
        draft = orchestrator.get_draft_view(case_id, conn=conn, config=app.config)
        if state is orchestrator.CaseState.VALIDATION_REJECTED:
            st.error(ui.VALIDATION_FAILURE_MESSAGE)
        elif state is orchestrator.CaseState.FAILED:
            st.error(ui.failure_message(orchestrator.get_failure_cause(case_id, conn=conn)))
        elif draft is None:
            st.info("No AI draft for this case yet.")
        else:
            st.caption("AI draft for human review — written by a language model and checked by "
                       "the validator. It proves nothing; the reviewer decides.")
            st.text(draft.summary)

            st.subheader("7. Evidence and source references")
            for line in draft.evidence_lines:
                linked = (f"evidence: {line.evidence_text}" if line.evidence_text is not None
                          else "not in the evidence list")
                st.text(f"[{line.source_id}] {line.note} — {linked}")
            for source_id, text in draft.source_references:
                st.text(f"Reference {source_id}: {text}" if text is not None
                        else f"Reference {source_id}: not in the evidence list")

            st.subheader("8. Uncertainty notes")
            if draft.uncertainties:
                for note_line in draft.uncertainties:
                    st.text(f"- {note_line}")
            else:
                st.text("The draft wrote no uncertainty note.")
            st.subheader("Recommended review steps")
            for step in draft.recommended_review_steps:
                st.text(f"- {step}")

        # 9. Validator status, with its reasons when it fails.
        st.subheader("9. Validator status")
        if state is orchestrator.CaseState.VALIDATION_REJECTED:
            ui.show_validator_status("failed")
            for reason in outcome.validation_reasons:
                st.text(f"- {reason}")
        elif draft is not None:
            ui.show_validator_status("passed")
        else:
            ui.show_validator_status("not_run")

        # 10. Human reviewer decision (only in HUMAN_REVIEW), then what was decided (I72 D2).
        st.subheader("10. Human reviewer decision")
        if state is orchestrator.CaseState.HUMAN_REVIEW:
            decision = st.radio("Decision", orchestrator.REVIEW_DECISIONS,
                                format_func=ui.decision_label, key="decision")
            comment = st.text_area("Optional comment", key="comment",
                                   max_chars=orchestrator.REVIEWER_COMMENT_MAX_CHARS)
            if st.button("Record decision", key="record_decision"):
                orchestrator.record_review_decision(case_id, decision, comment, conn=conn,
                                                    config=app.config)
                st.rerun()  # the page shows the recorded decision
        elif view.reviewer_decision is not None:
            st.success("Decision recorded: " + ui.decision_label(view.reviewer_decision))
            st.text("Reviewer comment:")
            st.text(view.reviewer_comment if view.reviewer_comment else "No comment.")
        else:
            st.info("No decision possible: the case is not in human review.")
except Exception as error:  # st.stop / st.rerun are BaseExceptions: never caught here
    ui.show_error(error)
