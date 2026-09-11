"""
AgriSmart AI — Grad-CAM heatmap utility.

Visualizes which image regions most influenced the model's prediction.
"""

from __future__ import annotations

from pathlib import Path
from typing import Union

import cv2
import numpy as np
import tensorflow as tf
from PIL import Image
from tensorflow.keras.applications.resnet50 import preprocess_input

from model.config import IMG_SIZE
from model.predict import load_model, predict_from_array


def _find_last_conv_layer(model: tf.keras.Model) -> str:
    """Locate the last convolutional layer in the ResNet50 backbone."""
    conv_layers: list[str] = []
    for layer in model.layers:
        if isinstance(layer, tf.keras.Model):
            for sub in layer.layers:
                if isinstance(sub, tf.keras.layers.Conv2D):
                    conv_layers.append(sub.name)
    return conv_layers[-1] if conv_layers else "conv5_block3_3_conv"


def make_gradcam_model(model: tf.keras.Model, last_conv_layer_name: str | None = None):
    """Build a sub-model that outputs conv feature maps + predictions."""
    last_conv = last_conv_layer_name or _find_last_conv_layer(model)
    base = model.layers[1]
    try:
        last_conv_layer = base.get_layer(last_conv)
    except ValueError:
        last_conv_layer = base.layers[-30]

    grad_model = tf.keras.models.Model(
        inputs=model.inputs,
        outputs=[last_conv_layer.output, model.output],
    )
    return grad_model, last_conv_layer.name


def compute_heatmap(
    image_array: np.ndarray,
    model: tf.keras.Model | None = None,
    class_index: int | None = None,
) -> np.ndarray:
    """Compute a Grad-CAM heatmap (float32, HxW, values 0-1)."""
    model = model or load_model()
    grad_model, _ = make_gradcam_model(model)

    if image_array.ndim == 2:
        image_array = np.stack([image_array] * 3, axis=-1)
    if image_array.shape[-1] == 4:
        image_array = image_array[..., :3]

    rgb = image_array.copy()
    if rgb.dtype != np.uint8:
        rgb = np.clip(rgb, 0, 255).astype(np.uint8)

    pil_img = Image.fromarray(rgb).resize(IMG_SIZE, Image.Resampling.LANCZOS)
    arr = np.asarray(pil_img, dtype=np.float32)
    batch = np.expand_dims(arr, axis=0)
    batch = preprocess_input(batch)

    with tf.GradientTape() as tape:
        conv_outputs, predictions = grad_model(batch, training=False)
        if class_index is None:
            class_index = int(tf.argmax(predictions[0]))
        loss = predictions[:, class_index]

    grads = tape.gradient(loss, conv_outputs)
    pooled_grads = tf.reduce_mean(grads, axis=(0, 1, 2))
    conv_outputs = conv_outputs[0]
    heatmap = tf.reduce_sum(tf.multiply(pooled_grads, conv_outputs), axis=-1)
    heatmap = tf.maximum(heatmap, 0) / (tf.reduce_max(heatmap) + 1e-8)
    heatmap = heatmap.numpy()

    h, w = image_array.shape[:2]
    return cv2.resize(heatmap, (w, h)).astype(np.float32)


def overlay_heatmap(
    image_array: np.ndarray,
    heatmap: np.ndarray,
    alpha: float = 0.45,
) -> np.ndarray:
    """Blend heatmap onto image; returns uint8 RGB array."""
    rgb = image_array.copy()
    if rgb.shape[-1] == 3 and rgb.dtype == np.uint8:
        pass
    elif rgb.shape[-1] == 3:
        rgb = np.clip(rgb, 0, 255).astype(np.uint8)
    else:
        rgb = cv2.cvtColor(rgb, cv2.COLOR_BGR2RGB)

    colored = cv2.applyColorMap(np.uint8(255 * heatmap), cv2.COLORMAP_JET)
    colored = cv2.cvtColor(colored, cv2.COLOR_BGR2RGB)
    return (alpha * colored + (1 - alpha) * rgb).astype(np.uint8)


def bounding_box_from_heatmap(
    heatmap: np.ndarray,
    threshold: float = 0.5,
) -> tuple[int, int, int, int] | None:
    """Derive bounding box (x, y, w, h) from high-activation Grad-CAM regions."""
    mask = (heatmap >= threshold).astype(np.uint8)
    if mask.sum() == 0:
        threshold = float(np.percentile(heatmap, 85))
        mask = (heatmap >= threshold).astype(np.uint8)
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None
    return cv2.boundingRect(max(contours, key=cv2.contourArea))


def generate_gradcam(
    image_source: Union[str, Path, np.ndarray],
    return_overlay: bool = True,
) -> dict:
    """
    Full Grad-CAM pipeline.

    Returns dict with: heatmap, overlay (optional), bbox, class_label, confidence
    """
    if isinstance(image_source, (str, Path)):
        rgb = np.asarray(Image.open(image_source).convert("RGB"))
    else:
        rgb = image_source
        if rgb.dtype != np.uint8:
            rgb = np.clip(rgb, 0, 255).astype(np.uint8)

    label, confidence = predict_from_array(rgb)
    heatmap = compute_heatmap(rgb)
    result: dict = {
        "heatmap": heatmap,
        "class_label": label,
        "confidence": confidence,
        "bbox": bounding_box_from_heatmap(heatmap),
    }
    if return_overlay:
        result["overlay"] = overlay_heatmap(rgb, heatmap)
    return result


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python model/gradcam.py <image_path> [output_path]")
        sys.exit(1)

    out = generate_gradcam(sys.argv[1])
    output_path = sys.argv[2] if len(sys.argv) > 2 else "gradcam_output.jpg"
    Image.fromarray(out["overlay"]).save(output_path)
    print(f"Saved Grad-CAM overlay to {output_path}")
    print(f"Prediction: {out['class_label']} ({out['confidence']:.2%})")
