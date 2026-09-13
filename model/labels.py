"""
AgriSmart AI — PlantVillage label helpers.

Kept free of TensorFlow/ONNX imports so the API, scripts and tests can use them
without loading any ML framework.
"""

from __future__ import annotations


def split_label(label: str) -> tuple[str, str]:
    """'Tomato___Early_blight' -> ('Tomato', 'Early blight')."""
    if "___" in label:
        crop, disease = label.split("___", 1)
        return crop.replace("_", " ").strip(), disease.replace("_", " ").strip()
    return "Plant", label.replace("_", " ").strip()


def format_label(label: str) -> str:
    """Human-readable label: 'Tomato___Early_blight' -> 'Tomato — Early blight'."""
    if "___" not in label:
        return label.replace("_", " ")
    crop, disease = split_label(label)
    return f"{crop} — {disease}"


def extract_crop_type(label: str) -> str:
    """Return crop/plant name from a PlantVillage class label."""
    return label.split("___")[0].replace("_", " ")


def is_healthy(label: str) -> bool:
    return "healthy" in label.lower()
