"""
SoC layer      : 5 — UI
Responsibility : Home page: banner, choice of a synthetic case (list or typed ID), run of the case,
                 and the review queue sorted by the G11 priority (brief §13 element 1; J01, J02,
                 J03, J08, J09). Launched by: .venv/bin/python -m streamlit run app/Home.py (I74 P7)
Never does     : Import anything but streamlit, the orchestrator and ui_components (I72 D3); read
                 the configuration or .env (app.config is passed on, never read, I74 P3); build or
                 check a case, compute a score, a band or a priority; sort the queue again; show
                 str(error) or a trace
Reference      : Architecture_Projet.md v1.5 — section 1.2, section 4 "Points d'entrée", section 5,
                 section 8 (n° 67); Features_Complet.md J01, J02, J03, J08, J09; brief §13;
                 decisions I72, I73 (4), I74
"""

from __future__ import annotations

import streamlit as st

from app import ui_components as ui
from src.agent import orchestrator

st.set_page_config(page_title="Fraud Risk Intelligence — prototype", layout="wide")
ui.show_banner()
st.title("Case intake and review queue")

app = ui.get_app_or_stop(orchestrator.load_app)

try:
    with orchestrator.open_connection(app.config) as conn:  # one connection per run (Q-12)
        st.header("1. Select a synthetic case")
        demo_ids = orchestrator.list_demo_cases(app=app)  # IDs only (I73 (4))
        chosen = st.selectbox("Synthetic demo case", demo_ids, key="demo_case")
        typed = st.text_input("…or type a case ID (it wins over the list)", key="typed_case_id")
        if st.button("Run case", key="run_case"):
            case_id = typed.strip() or chosen
            # A second click on the same case resumes it: no second case (J09, G10).
            orchestrator.submit_demo_case(case_id, conn=conn, app=app)
            st.session_state[ui.CASE_KEY] = case_id
            st.switch_page("pages/1_Case_Review.py")

        st.header("Review queue — high priority first (G11)")
        queue = orchestrator.list_review_queue(conn=conn)  # already sorted by the orchestrator
        if not queue:
            st.info("No case is waiting for human review.")
        for item in queue:
            st.text(f"{item.case_id} · priority: {item.priority} · created: {item.created_at}")
            if st.button(f"Open {item.case_id}", key=f"open_{item.case_id}"):
                st.session_state[ui.CASE_KEY] = item.case_id
                st.switch_page("pages/1_Case_Review.py")
except Exception as error:  # st.stop / st.switch_page are BaseExceptions: never caught here
    ui.show_error(error)
