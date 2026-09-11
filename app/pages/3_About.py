"""
app/pages/3_About.py — static About page.
"""

from __future__ import annotations

import streamlit as st

from components.ui import feature_card, inject_css, section_title

st.set_page_config(page_title="About — AgriSmart AI", page_icon="ℹ️", layout="wide")
inject_css()

with st.sidebar:
    st.markdown("### 🌿 AgriSmart AI")
    st.caption("UI prototype — running on mock data")

st.markdown("## About AgriSmart AI")

st.markdown(
    "AgriSmart AI is a plant disease detection tool built for the Smart India Hackathon. "
    "It lets a farmer photograph a leaf and get back a diagnosis, along with plain-language "
    "treatment guidance, so problems can be caught and acted on early instead of spreading "
    "across a field."
)

section_title("The Problem")
st.markdown(
    "Crop diseases are often identified late, after visible damage has already spread, "
    "by which point yield loss is harder to prevent. Farmers don't always have quick access "
    "to an agronomist, and existing diagnostic tools can be slow or require lab equipment. "
    "AgriSmart AI aims to close that gap with a fast, photo-based first assessment."
)

section_title("How the Application Works")
w1, w2, w3 = st.columns(3)
with w1:
    feature_card("📸", "1. Capture", "The farmer uploads or photographs a leaf showing possible symptoms.")
with w2:
    feature_card("🧠", "2. Analyze", "A trained model classifies the leaf against known disease patterns.")
with w3:
    feature_card("📋", "3. Act", "The app returns a diagnosis plus treatment and prevention steps.")

section_title("Key Features")
f1, f2, f3 = st.columns(3)
with f1:
    feature_card("🔬", "AI-Based Disease Detection", "Photo-based classification across common crop diseases.")
with f2:
    feature_card("🎯", "Explainable AI", "Highlights which parts of the leaf informed the diagnosis.")
with f3:
    feature_card("🌾", "Smart Agriculture Features", "Irrigation, weather-risk, and sustainability guidance alongside each diagnosis.")

st.write("")
st.info(
    "This build is a UI prototype: diagnosis results are sample data. "
    "The trained model is being developed separately and will be connected in a later stage."
)