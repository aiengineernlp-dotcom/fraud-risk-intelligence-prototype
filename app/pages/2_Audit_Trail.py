"""
SoC layer      : 5 — UI
Responsibility : Audit trail page: the audit events of one case or of every case, visible in a
                 table and exportable as CSV and JSON, with the same events as the export (brief
                 §13 element 11; J06, I02)
Never does     : Import anything but streamlit, the orchestrator and ui_components (I72 D3); read
                 the configuration (app.config is passed on, never read, I74 P3); filter, sort or
                 change an event; write a file on the server; show str(error) or a trace
Reference      : Architecture_Projet.md v1.5 — section 1.2, section 5, section 8 (n° 69);
                 Features_Complet.md I02, J06, J07; brief §13 element 11; decisions I72, I74 P2
"""

from __future__ import annotations

import streamlit as st

from app import ui_components as ui
from src.agent import orchestrator

st.set_page_config(page_title="Audit trail — prototype", layout="wide")
ui.show_banner()
st.title("Audit trail")

app = ui.get_app_or_stop(orchestrator.load_app)

try:
    with orchestrator.open_connection(app.config) as conn:  # one connection per run (Q-12)
        typed = st.text_input("Case ID (leave empty for every case)", key="audit_case_id")
        case_id = typed.strip() or None
        rows = orchestrator.get_audit_rows(case_id, conn=conn)  # same events as the export
        st.text(f"{len(rows)} audit events")
        if rows:
            st.dataframe(rows, hide_index=True)
        else:
            st.info("No audit event for this selection.")
        st.download_button("Export CSV", data=orchestrator.export_audit("csv", case_id, conn=conn),
                           file_name="audit_trail.csv", mime="text/csv", key="export_csv")
        st.download_button("Export JSON", data=orchestrator.export_audit("json", case_id, conn=conn),
                           file_name="audit_trail.json", mime="application/json", key="export_json")
except Exception as error:
    ui.show_error(error)
