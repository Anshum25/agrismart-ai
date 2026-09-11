"""
app/app.py — Home page (entry point).

This is the UI PROTOTYPE for AgriSmart AI. It uses mock/dummy data only —
see components/mock_data.py. The real ML model under model/ is NOT
imported or called anywhere in this app/ directory.

Run with:  streamlit run app/app.py
"""

from __future__ import annotations

import streamlit as st

from components.ui import feature_card, inject_css, render_hero, step_card

st.set_page_config(page_title="AgriSmart AI", page_icon="🌿", layout="wide")
inject_css()

with st.sidebar:
    st.markdown("### 🌿 AgriSmart AI")
    st.caption("UI prototype — running on mock data")

# ---------------------------------------------------------------------------
# Hero
# ---------------------------------------------------------------------------
render_hero(
    "AgriSmart AI",
    "Smart Plant Disease Detection for Better Farming",
)

col1, col2 = st.columns([1, 3])
with col1:
    if st.button("🔍 Diagnose Your Plant", use_container_width=True):
        st.switch_page("pages/1_Diagnose.py")

st.write("")
st.markdown(
    "AgriSmart AI helps farmers spot crop diseases early — upload a photo of a leaf "
    "and get an instant diagnosis, plain-language treatment advice, and follow-up "
    "guidance on irrigation, weather risk, and sustainable practices, all in one place."
)

# ---------------------------------------------------------------------------
# How it works
# ---------------------------------------------------------------------------
st.markdown("## How It Works")
h1, h2, h3 = st.columns(3)
with h1:
    step_card(1, "Upload a photo", "Take or upload a clear photo of the affected leaf.")
with h2:
    step_card(2, "AI analyzes it", "The model checks the leaf against known disease patterns.")
with h3:
    step_card(3, "Get a plan", "See the diagnosis plus treatment and prevention steps.")

# ---------------------------------------------------------------------------
# Feature cards
# ---------------------------------------------------------------------------
st.markdown("## What AgriSmart AI Offers")
f1, f2, f3, f4 = st.columns(4)
with f1:
    feature_card("🧠", "AI Disease Detection", "Identifies common crop diseases from a single leaf photo.")
with f2:
    feature_card("🔬", "Explainable AI", "Shows which regions of the leaf informed the diagnosis.")
with f3:
    feature_card("💊", "Treatment Recommendations", "Clear, actionable treatment and prevention steps.")
with f4:
    feature_card("🌾", "Smart Agriculture Insights", "Irrigation, weather risk, and sustainability guidance.")

st.write("")
st.info("This is a UI prototype. Diagnosis results are sample data until the trained model is connected.")