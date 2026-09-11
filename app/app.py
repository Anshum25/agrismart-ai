"""
AgriSmart AI — Streamlit web application.

Upload a leaf image → CNN prediction → Grad-CAM → LLM care advice
+ bonus irrigation, weather, and sustainability modules.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import numpy as np
import streamlit as st
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from bonus.assistant import get_care_advice
from bonus.irrigation import get_irrigation_advice
from bonus.sustainability import compute_sustainability_score
from bonus.weather import get_weather_risk
from model.config import DEFAULT_MODEL_PATH
from model.gradcam import generate_gradcam
from model.predict import format_label, load_model, predict_from_array

st.set_page_config(page_title="AgriSmart AI", page_icon="🌿", layout="wide")

st.title("🌿 AgriSmart AI")
st.caption("Plant disease detection with ResNet50 + AI-powered care advice")

with st.sidebar:
    st.header("About")
    st.markdown(
        "**AgriSmart AI** detects crop diseases from leaf photos using a "
        "ResNet50 model trained on PlantVillage (38 classes)."
    )
    st.divider()
    st.subheader("Live Webcam Demo")
    st.code("python app/live_demo.py --show-gradcam", language="bash")
    if st.button("Launch live demo (new terminal)"):
        demo_path = ROOT / "app" / "live_demo.py"
        try:
            if sys.platform == "win32":
                subprocess.Popen(
                    ["start", "cmd", "/k", sys.executable, str(demo_path), "--show-gradcam"],
                    shell=True,
                )
            else:
                subprocess.Popen([sys.executable, str(demo_path), "--show-gradcam"])
            st.success("Live demo launched in a separate window.")
        except Exception as exc:
            st.warning(f"Could not auto-launch: {exc}. Run the command manually.")

    if DEFAULT_MODEL_PATH.exists():
        st.success("Model weights found ✓")
    else:
        st.error("Model weights missing — see README to train or download.")


@st.cache_resource
def _cached_model():
    return load_model()


def run_inference(image: Image.Image) -> None:
    rgb = np.asarray(image.convert("RGB"))

    with st.spinner("Analyzing leaf image..."):
        try:
            _cached_model()
        except FileNotFoundError as exc:
            st.error(str(exc))
            return

        label, confidence = predict_from_array(rgb)

        try:
            gradcam_result = generate_gradcam(rgb)
            overlay = gradcam_result["overlay"]
            heatmap_ok = True
        except Exception:
            overlay = rgb
            heatmap_ok = False

        advice = get_care_advice(label)
        irrigation = get_irrigation_advice(label)
        weather = get_weather_risk(label)
        sustainability = compute_sustainability_score(label)

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Original")
        st.image(image, use_container_width=True)
    with col2:
        st.subheader("Grad-CAM Overlay")
        if heatmap_ok:
            st.image(overlay, use_container_width=True)
        else:
            st.image(image, use_container_width=True)
            st.caption("Grad-CAM unavailable.")

    st.divider()
    st.subheader("Diagnosis")
    st.metric("Predicted condition", format_label(label))
    st.progress(min(max(confidence, 0.0), 1.0), text=f"Confidence: {confidence:.1%}")

    st.subheader("Care & Prevention Advice")
    st.info(advice)

    with st.expander("💧 Smart Irrigation (Bonus A)"):
        st.write(irrigation["recommendation"])
        st.write(f"Suggested daily water: **{irrigation['daily_water_mm']} mm**")
        st.write(f"Next watering in: **~{irrigation['next_watering_hours']} hours**")
        for note in irrigation["notes"]:
            st.write(f"- {note}")

    with st.expander("🌦️ Weather Risk (Bonus B)"):
        st.write(f"Risk level: **{weather['risk_level'].upper()}** ({weather['risk_score']}/100)")
        st.write(weather["recommended_action"])
        for factor in weather["risk_factors"]:
            st.write(f"- {factor}")

    with st.expander("♻️ Sustainability Score (Bonus C)"):
        st.metric("Score", f"{sustainability['score']}/100 (Grade {sustainability['grade']})")
        for tip in sustainability["improvement_tips"]:
            st.write(f"- {tip}")


uploaded = st.file_uploader("Upload a leaf photo (JPG/PNG)", type=["jpg", "jpeg", "png"])

if uploaded is not None:
    run_inference(Image.open(uploaded))
else:
    st.markdown(
        "### Getting started\n"
        "1. Train the model on Colab or add weights to `model/weights/`\n"
        "2. Copy `.env.example` → `.env` and add your Hugging Face token\n"
        "3. Upload a leaf photo above\n"
        "4. Optional: `python app/live_demo.py` for webcam detection"
    )
