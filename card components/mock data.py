"""
components/mock_data.py

╔══════════════════════════════════════════════════════════════════════╗
║  MOCK DATA LAYER — NOT THE REAL MODEL                                 ║
║                                                                        ║
║  Every function in this file returns fabricated data so the UI can    ║
║  be demoed end-to-end before the ML model is ready. Nothing here      ║
║  loads weights, runs inference, or imports anything from `model/`.    ║
║                                                                        ║
║  HOW TO SWAP IN THE REAL MODEL LATER:                                 ║
║  Replace the body of `mock_predict()` with a call to the real         ║
║  model, e.g. `model.predict.predict_from_array(image_array)`, and     ║
║  keep the same return shape (a dict with the same keys) so none of    ║
║  the page code in pages/1_Diagnose.py has to change.                  ║
╚══════════════════════════════════════════════════════════════════════╝
"""

from __future__ import annotations

import hashlib
import random
from datetime import datetime
from typing import Any

import numpy as np
import streamlit as st
from PIL import Image, ImageFilter

# A small catalog of plausible plant/disease profiles used to fabricate
# results. Feel free to extend this list — it only feeds the UI demo.
_DISEASE_CATALOG: list[dict[str, Any]] = [
    {
        "plant": "Tomato",
        "disease": "Early Blight",
        "status": "Disease Detected",
        "severity": "Moderate",
        "symptoms": [
            "Dark concentric rings on lower, older leaves",
            "Yellowing tissue surrounding the spots",
            "Leaves eventually wilt and drop",
        ],
        "treatment": [
            "Remove and destroy affected leaves",
            "Apply a copper-based or chlorothalonil fungicide",
            "Avoid overhead watering to keep foliage dry",
        ],
        "prevention": [
            "Rotate crops — avoid planting tomatoes in the same spot yearly",
            "Space plants for good airflow",
            "Mulch to stop soil-borne spores splashing onto leaves",
        ],
    },
    {
        "plant": "Potato",
        "disease": "Late Blight",
        "status": "Disease Detected",
        "severity": "Severe",
        "symptoms": [
            "Water-soaked dark patches on leaves and stems",
            "White fungal growth on the underside of leaves in humid weather",
            "Rapid collapse of foliage within days",
        ],
        "treatment": [
            "Apply a systemic fungicide immediately",
            "Remove and destroy infected plants to stop spread",
            "Improve field drainage to reduce humidity around plants",
        ],
        "prevention": [
            "Plant certified disease-free seed potatoes",
            "Avoid overhead irrigation, especially in the evening",
            "Monitor closely during cool, wet weather",
        ],
    },
    {
        "plant": "Grape",
        "disease": "Powdery Mildew",
        "status": "Disease Detected",
        "severity": "Mild",
        "symptoms": [
            "White-grey powdery coating on leaves and shoots",
            "Distorted or stunted young leaves",
            "Reduced fruit quality on affected clusters",
        ],
        "treatment": [
            "Apply sulfur-based fungicide at first sign of infection",
            "Prune to open up the canopy for airflow",
            "Remove heavily infected leaves",
        ],
        "prevention": [
            "Choose mildew-resistant grape varieties where possible",
            "Avoid excess nitrogen fertilizer, which encourages soft growth",
            "Maintain a regular preventive spray schedule in humid seasons",
        ],
    },
    {
        "plant": "Corn",
        "disease": "Healthy",
        "status": "Healthy",
        "severity": "Healthy",
        "symptoms": ["No visible lesions, spots, or discoloration detected"],
        "treatment": ["No treatment needed — plant appears healthy"],
        "prevention": [
            "Continue regular field monitoring",
            "Maintain balanced fertilization",
            "Keep up with routine irrigation scheduling",
        ],
    },
    {
        "plant": "Apple",
        "disease": "Cedar Apple Rust",
        "status": "Disease Detected",
        "severity": "Moderate",
        "symptoms": [
            "Bright orange-yellow spots on upper leaf surface",
            "Small raised structures on the underside of leaves",
            "Premature leaf drop in heavy infections",
        ],
        "treatment": [
            "Apply a protectant fungicide from bud break through early summer",
            "Remove nearby cedar/juniper hosts if practical",
        ],
        "prevention": [
            "Plant rust-resistant apple varieties",
            "Space trees for airflow",
            "Scout leaves weekly during spring",
        ],
    },
]


def _seed_from_image_bytes(image_bytes: bytes) -> int:
    """Derives a stable seed from the image so re-analyzing the same photo
    gives the same mock result during a demo, instead of a new random one
    every click."""
    digest = hashlib.md5(image_bytes).hexdigest()
    return int(digest[:8], 16)


def mock_predict(image_bytes: bytes) -> dict[str, Any]:
    """MOCK — stands in for the real model's predict_from_array().

    Returns a dict shaped like:
        {
            "plant": str, "disease": str, "status": str,
            "confidence": float (0-1), "severity": str,
        }
    """
    rng = random.Random(_seed_from_image_bytes(image_bytes))
    profile = rng.choice(_DISEASE_CATALOG)
    confidence = rng.uniform(0.55, 0.98)
    return {
        "plant": profile["plant"],
        "disease": profile["disease"],
        "status": profile["status"],
        "severity": profile["severity"],
        "confidence": round(confidence, 4),
        "_profile": profile,  # internal — used by mock_get_treatment below
    }


def mock_get_treatment(prediction: dict[str, Any]) -> dict[str, list[str]]:
    """MOCK — stands in for a real symptoms/treatment/prevention lookup."""
    profile = prediction.get("_profile", _DISEASE_CATALOG[0])
    return {
        "symptoms": profile["symptoms"],
        "treatment": profile["treatment"],
        "prevention": profile["prevention"],
    }


def mock_get_irrigation(plant: str) -> dict[str, Any]:
    """MOCK — stands in for the real irrigation-advice module."""
    rng = random.Random(hashlib.md5(plant.encode()).hexdigest())
    return {
        "recommendation": f"{plant} in this growth stage benefits from consistent, "
        "moderate soil moisture rather than deep infrequent watering.",
        "daily_water_mm": round(rng.uniform(4, 9), 1),
        "next_watering_hours": rng.randint(8, 30),
        "notes": [
            "Water early morning to reduce evaporation loss",
            "Check topsoil moisture before watering if rain is expected",
        ],
    }


def mock_get_weather(plant: str) -> dict[str, Any]:
    """MOCK — stands in for the real weather-risk module."""
    rng = random.Random(hashlib.md5((plant + "weather").encode()).hexdigest())
    score = rng.randint(20, 85)
    level = "low" if score < 40 else "moderate" if score < 70 else "high"
    return {
        "risk_level": level,
        "risk_score": score,
        "recommended_action": {
            "low": "Conditions are favorable — no special precautions needed.",
            "moderate": "Keep an eye on humidity levels over the next few days.",
            "high": "High humidity and rain are forecast — consider a preventive fungicide application.",
        }[level],
        "risk_factors": [
            "Elevated humidity in the extended forecast",
            "Recent rainfall increasing leaf wetness duration",
        ],
    }


def mock_get_sustainability(plant: str) -> dict[str, Any]:
    """MOCK — stands in for the real sustainability-scoring module."""
    rng = random.Random(hashlib.md5((plant + "sustain").encode()).hexdigest())
    score = rng.randint(55, 95)
    grade = "A" if score >= 85 else "B" if score >= 70 else "C"
    return {
        "score": score,
        "grade": grade,
        "improvement_tips": [
            "Reduce fungicide frequency by combining with resistant varieties",
            "Use drip irrigation to cut water usage",
            "Rotate crops to maintain soil health",
        ],
    }


def mock_generate_attention_map(image: Image.Image, seed_bytes: bytes) -> Image.Image:
    """MOCK — fabricates a plausible-looking attention heatmap overlay.

    This is NOT Grad-CAM. It's a stand-in so the "Explainable AI" section
    has something visual to show before the real pipeline in
    model/gradcam.py is wired into this app. Swap this call out for the
    real `generate_gradcam()` output once the model is ready.
    """
    rng_seed = int(hashlib.md5(seed_bytes).hexdigest()[:8], 16)
    rng = random.Random(rng_seed)

    w, h = image.size
    grid = 96
    yy, xx = np.mgrid[0:grid, 0:grid]
    heat = np.zeros((grid, grid), dtype=np.float32)

    for _ in range(rng.randint(1, 2)):
        cx = rng.uniform(grid * 0.3, grid * 0.7)
        cy = rng.uniform(grid * 0.3, grid * 0.7)
        sigma = rng.uniform(grid * 0.08, grid * 0.16)
        heat += np.exp(-(((xx - cx) ** 2 + (yy - cy) ** 2) / (2 * sigma**2)))

    peak = heat.max()
    if peak > 0:
        heat = heat / peak

    rgba = np.zeros((grid, grid, 4), dtype=np.uint8)
    rgba[..., 0] = 255
    rgba[..., 1] = (255 * (1 - heat)).astype(np.uint8)
    rgba[..., 2] = 40
    rgba[..., 3] = (heat * 180).astype(np.uint8)

    heat_img = Image.fromarray(rgba, mode="RGBA").resize((w, h), Image.BICUBIC)
    heat_img = heat_img.filter(ImageFilter.GaussianBlur(radius=max(w, h) * 0.02))

    base = image.convert("RGBA")
    overlay = Image.alpha_composite(base, heat_img)
    return overlay.convert("RGB")


# ---------------------------------------------------------------------------
# Session-based "Recent Diagnoses" history (no database — just st.session_state)
# ---------------------------------------------------------------------------

def add_to_history(prediction: dict[str, Any], thumbnail_bytes: bytes) -> None:
    if "diagnosis_history" not in st.session_state:
        st.session_state["diagnosis_history"] = []
    st.session_state["diagnosis_history"].insert(
        0,
        {
            "plant": prediction["plant"],
            "disease": prediction["disease"],
            "status": prediction["status"],
            "confidence": prediction["confidence"],
            "timestamp": datetime.now().strftime("%b %d, %Y — %I:%M %p"),
            "thumbnail": thumbnail_bytes,
        },
    )
    # Keep the list from growing unbounded during a long demo session
    st.session_state["diagnosis_history"] = st.session_state["diagnosis_history"][:20]


def get_history() -> list[dict[str, Any]]:
    return st.session_state.get("diagnosis_history", [])