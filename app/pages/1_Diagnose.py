"""
app/pages/1_Diagnose.py — main diagnosis flow.

UI PROTOTYPE ONLY. Calls mock_predict() and friends from
components/mock_data.py — never the real model. See that file for the
one place to swap in real inference later.
"""

from __future__ import annotations

import hashlib
import io
import time

import streamlit as st
from PIL import Image

from components.mock_data import (
    add_to_history,
    mock_generate_attention_map,
    mock_get_irrigation,
    mock_get_sustainability,
    mock_get_treatment,
    mock_get_weather,
    mock_predict,
)
from components.ui import (
    COLORS,
    confidence_bar,
    diagnosis_summary,
    inject_css,
    insight_card,
    mock_note,
    section_title,
)

st.set_page_config(page_title="Diagnose — AgriSmart AI", page_icon="🔍", layout="wide")
inject_css()

with st.sidebar:
    st.markdown("### 🌿 AgriSmart AI")
    st.caption("UI prototype — running on mock data")

st.markdown("## Diagnose Your Plant")
st.caption("Upload a clear photo of the affected leaf, or use your camera.")

if "uploader_key" not in st.session_state:
    st.session_state["uploader_key"] = 0


def _reset_diagnosis() -> None:
    st.session_state["uploader_key"] += 1
    for key in ("diag_image_bytes", "diag_result", "diag_attention", "diag_logged_hash"):
        st.session_state.pop(key, None)


# ---------------------------------------------------------------------------
# Step 1 — get an image (upload or camera)
# ---------------------------------------------------------------------------
input_mode = st.radio(
    "Input method", ["📁 Upload a photo", "📷 Use camera"], horizontal=True, label_visibility="collapsed"
)

new_bytes = None
if input_mode == "📁 Upload a photo":
    uploaded = st.file_uploader(
        "Upload a leaf photo (JPG/PNG)",
        type=["jpg", "jpeg", "png"],
        key=f"uploader_{st.session_state['uploader_key']}",
    )
    if uploaded is not None:
        new_bytes = uploaded.getvalue()
else:
    captured = st.camera_input(
        "Take a photo of the leaf", key=f"camera_{st.session_state['uploader_key']}"
    )
    if captured is not None:
        new_bytes = captured.getvalue()

if new_bytes:
    st.session_state["diag_image_bytes"] = new_bytes

# ---------------------------------------------------------------------------
# Step 2 — preview + analyze
# ---------------------------------------------------------------------------
analyze_clicked = False

if st.session_state.get("diag_image_bytes"):
    original_image = Image.open(io.BytesIO(st.session_state["diag_image_bytes"])).convert("RGB")

    pcol1, pcol2 = st.columns([2, 1])
    with pcol1:
        st.image(original_image, caption="Preview", use_container_width=True)
    with pcol2:
        st.write("")
        analyze_clicked = st.button("🔍 Analyze Plant", type="primary", use_container_width=True)
        if st.button("🗑️ Remove / change image", use_container_width=True):
            _reset_diagnosis()
            st.rerun()

    if analyze_clicked:
        with st.spinner("Analyzing your plant..."):
            time.sleep(1.4)  # simulated processing time for the demo
            result = mock_predict(st.session_state["diag_image_bytes"])
            attention_img = mock_generate_attention_map(
                original_image, st.session_state["diag_image_bytes"]
            )
        st.session_state["diag_result"] = result
        st.session_state["diag_attention"] = attention_img
else:
    st.markdown(
        '<div class="agri-mock-note">Upload or capture a leaf photo above to get started.</div>',
        unsafe_allow_html=True,
    )

# ---------------------------------------------------------------------------
# Step 3 — results dashboard
# ---------------------------------------------------------------------------
result = st.session_state.get("diag_result")

if result and st.session_state.get("diag_image_bytes"):
    original_image = Image.open(io.BytesIO(st.session_state["diag_image_bytes"])).convert("RGB")
    attention_image = st.session_state.get("diag_attention", original_image)
    confidence = result["confidence"]

    section_title("Diagnosis Results")

    if confidence < 0.6:
        st.warning("⚠️ We couldn't confidently identify the disease.")
        st.write("Please upload a clearer image showing the affected leaf.")
        if st.button("🔁 Try Another Image"):
            _reset_diagnosis()
            st.rerun()
    else:
        # Log this result to session history once per new image
        img_hash = hashlib.md5(st.session_state["diag_image_bytes"]).hexdigest()
        if st.session_state.get("diag_logged_hash") != img_hash:
            thumb = original_image.copy()
            thumb.thumbnail((160, 160))
            buf = io.BytesIO()
            thumb.save(buf, format="PNG")
            add_to_history(result, buf.getvalue())
            st.session_state["diag_logged_hash"] = img_hash

        diagnosis_summary(result["plant"], result["disease"], result["status"], result["severity"])
        st.write("")
        confidence_bar(confidence, note="Confidence shown here is sample data for the prototype.")

        section_title("Explainable AI")
        ecol1, ecol2 = st.columns(2)
        with ecol1:
            st.image(original_image, caption="Original Image", use_container_width=True)
        with ecol2:
            st.image(attention_image, caption="AI Attention Map", use_container_width=True)
        st.caption(
            "The highlighted regions represent areas the AI would use when "
            "identifying potential disease symptoms."
        )
        mock_note("This is a mock visualization for the UI prototype — not real Grad-CAM output.")

        treatment_info = mock_get_treatment(result)
        irrigation = mock_get_irrigation(result["plant"])
        weather = mock_get_weather(result["plant"])
        sustainability = mock_get_sustainability(result["plant"])

        section_title("Detailed Insights")
        d1, d2 = st.columns(2)
        with d1:
            insight_card(
                "🌿", "What we detected",
                [f"Plant: {result['plant']}", f"Condition: {result['disease']}", f"Status: {result['status']}"],
                COLORS["leaf"],
            )
            insight_card("🔍", "Symptoms", treatment_info["symptoms"], COLORS["amber"])
            insight_card("💊", "Recommended Treatment", treatment_info["treatment"], COLORS["soil"])
            insight_card("🛡️", "Prevention", treatment_info["prevention"], COLORS["forest"])
        with d2:
            insight_card(
                "💧", "Irrigation Recommendation",
                [
                    irrigation["recommendation"],
                    f"Suggested daily water: {irrigation['daily_water_mm']} mm",
                    f"Next watering in ~{irrigation['next_watering_hours']} hours",
                    *irrigation["notes"],
                ],
                COLORS["sky"],
            )
            insight_card(
                "🌦️", "Weather Risk",
                [
                    f"Risk level: {weather['risk_level'].capitalize()} ({weather['risk_score']}/100)",
                    weather["recommended_action"],
                    *weather["risk_factors"],
                ],
                COLORS["sky"],
            )
            insight_card(
                "♻️", "Sustainability Insight",
                [
                    f"Score: {sustainability['score']}/100 (Grade {sustainability['grade']})",
                    *sustainability["improvement_tips"],
                ],
                "#2D6A4F",
            )

        mock_note("All figures above are sample data for this UI prototype and will be replaced by real model output.")