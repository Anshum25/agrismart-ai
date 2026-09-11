"""
AgriSmart AI — inference interface.

Primary API (for hackathon judges):
    predict(image_path) -> (class_label, confidence)

Also supports in-memory frames for live webcam inference:
    predict_from_array(image_array) -> (class_label, confidence)
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Union

import numpy as np
import tensorflow as tf
from PIL import Image
from tensorflow.keras.applications.resnet50 import preprocess_input

from model.config import CLASS_LABELS_PATH, DEFAULT_CLASS_LABELS, DEFAULT_MODEL_PATH, IMG_SIZE

_model: tf.keras.Model | None = None
_labels: list[str] | None = None


def _load_class_labels(labels_path: Path) -> list[str]:
    if labels_path.exists():
        with labels_path.open(encoding="utf-8") as f:
            data = json.load(f)
        return data.get("labels", DEFAULT_CLASS_LABELS)
    return list(DEFAULT_CLASS_LABELS)


def load_model(
    model_path: str | Path | None = None,
    labels_path: str | Path | None = None,
) -> tf.keras.Model:
    """Load (or return cached) Keras model and class labels."""
    global _model, _labels

    if _model is not None:
        return _model

    model_path = Path(model_path or DEFAULT_MODEL_PATH)
    labels_path = Path(labels_path or CLASS_LABELS_PATH)

    if not model_path.exists():
        raise FileNotFoundError(
            f"Model weights not found at {model_path}.\n"
            "Train with `python model/train.py` (see README for Colab instructions) "
            "or download pre-trained weights into model/weights/."
        )

    _model = tf.keras.models.load_model(model_path)
    _labels = _load_class_labels(labels_path)
    return _model


def _prepare_array(image_array: np.ndarray) -> np.ndarray:
    """Convert HWC uint8/float array to batched preprocessed tensor."""
    if image_array.ndim == 2:
        image_array = np.stack([image_array] * 3, axis=-1)
    if image_array.shape[-1] == 4:
        image_array = image_array[..., :3]

    if image_array.dtype != np.uint8:
        image_array = np.clip(image_array, 0, 255).astype(np.uint8)

    pil_img = Image.fromarray(image_array).resize(IMG_SIZE, Image.Resampling.LANCZOS)
    arr = np.asarray(pil_img, dtype=np.float32)
    arr = np.expand_dims(arr, axis=0)
    return preprocess_input(arr)


def predict_from_array(
    image_array: np.ndarray,
    model_path: str | Path | None = None,
) -> tuple[str, float]:
    """
    Predict disease class from an in-memory image (BGR or RGB numpy array).

    Returns:
        (class_label, confidence) where confidence is in [0, 1].
    """
    global _labels
    model = load_model(model_path)
    if _labels is None:
        _labels = _load_class_labels(CLASS_LABELS_PATH)

    batch = _prepare_array(image_array)
    probs = model.predict(batch, verbose=0)[0]
    idx = int(np.argmax(probs))
    confidence = float(probs[idx])
    label = _labels[idx] if idx < len(_labels) else f"class_{idx}"
    return label, confidence


def predict(
    image_path: Union[str, Path],
    model_path: str | Path | None = None,
) -> tuple[str, float]:
    """
    Predict disease class from an image file path.

    Returns:
        (class_label, confidence) where confidence is in [0, 1].
    """
    path = Path(image_path)
    if not path.exists():
        raise FileNotFoundError(f"Image not found: {path}")

    image = Image.open(path).convert("RGB")
    return predict_from_array(np.asarray(image), model_path=model_path)


def format_label(label: str) -> str:
    """Human-readable label: 'Tomato___Early_blight' -> 'Tomato — Early blight'."""
    parts = label.split("___", 1)
    if len(parts) == 2:
        crop, disease = parts
        crop = crop.replace("_", " ")
        disease = disease.replace("_", " ")
        return f"{crop} — {disease}"
    return label.replace("_", " ")


def extract_crop_type(label: str) -> str:
    """Return crop/plant name from a PlantVillage class label."""
    return label.split("___")[0].replace("_", " ")


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python model/predict.py <image_path>")
        sys.exit(1)

    cls, conf = predict(sys.argv[1])
    print(f"Prediction: {format_label(cls)}")
    print(f"Confidence: {conf:.2%}")
