"""
app/pages/2_History.py — session-based "Recent Diagnoses" list.

No database: history lives in st.session_state for the current browser
session only (see components/mock_data.py: add_to_history / get_history).
"""

from __future__ import annotations

import streamlit as st

from components.mock_data import get_history
from components.ui import inject_css, severity_badge, status_badge

st.set_page_config(page_title="History — AgriSmart AI", page_icon="🕘", layout="wide")
inject_css()

with st.sidebar:
    st.markdown("### 🌿 AgriSmart AI")
    st.caption("UI prototype — running on mock data")

st.markdown("## Recent Diagnoses")
st.caption("Diagnoses from this session. Cleared when the browser tab is closed — no database yet.")

history = get_history()

if not history:
    st.markdown(
        '<div class="agri-mock-note">No diagnoses yet in this session. '
        'Head to the Diagnose page and analyze a leaf photo to see it appear here.</div>',
        unsafe_allow_html=True,
    )
else:
    for entry in history:
        col_img, col_info = st.columns([1, 4])
        with col_img:
            st.image(entry["thumbnail"], width=90)
        with col_info:
            st.markdown(
                f"""
                <div class="agri-history-card">
                    <strong>{entry['plant']} — {entry['disease']}</strong><br/>
                    {status_badge(entry['status'])}&nbsp;&nbsp;
                    Confidence: {round(entry['confidence'] * 100)}%
                    <div class="agri-history-meta">{entry['timestamp']}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    if st.button("Clear history"):
        st.session_state["diagnosis_history"] = []
        st.rerun()