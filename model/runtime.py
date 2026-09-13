"""
AgriSmart AI — lightweight inference runtime (no TensorFlow).

Runs the exported ONNX model (see model/export_onnx.py) with ONNX Runtime and
implements everything the API needs around it:

* ResNet50 "caffe" preprocessing (RGB->BGR, ImageNet mean subtraction)
* Grad-CAM computed in closed form from the exported classification-head
  weights (GAP -> Dense+ReLU -> Dropout -> Dense+softmax), numerically
  identical to the TensorFlow GradientTape version in model/gradcam.py
* An image quality / "is this a leaf?" gate
* An affected-leaf-area estimate used for severity

The same algorithms are implemented in the browser in
frontend/src/lib/inference.js. Keep QUALITY and SEVERITY in sync with that file
(backend/tests/test_runtime.py checks this).
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
from collections import deque
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

from model.labels import extract_crop_type, format_label, is_healthy

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_MODEL_DIR = PROJECT_ROOT / "frontend" / "public" / "model"

IMG_SIZE = 224
ANALYSIS_SIZE = 128
MEAN_BGR = np.array([103.939, 116.779, 123.68], dtype=np.float32)

# Thresholds for the quality gate. Mirrored in frontend/src/lib/inference.js.
QUALITY = {
    "minPlantRatio": 0.20,
    "minGreenRatio": 0.03,
    "minBrightness": 35,
    "maxBrightness": 235,
    "blurReject": 10,
    "blurWarn": 40,
    "minConfidence": 0.60,
    "minMargin": 0.20,
    "cropPad": 1.0,
    "cropMaxArea": 0.80,
    "cropMinArea": 0.02,
}

# Affected-area (%) cut-offs for severity. Mirrored in the frontend.
SEVERITY = {"moderate": 10, "severe": 25}


class ModelNotAvailable(RuntimeError):
    """Raised when the ONNX model files are missing or cannot be loaded."""


# ---------------------------------------------------------------------------
# Pure-numpy image analysis (shared by server + tests)
# ---------------------------------------------------------------------------

def to_rgb_uint8(image: np.ndarray) -> np.ndarray:
    if image.ndim == 2:
        image = np.stack([image] * 3, axis=-1)
    if image.shape[-1] == 4:
        image = image[..., :3]
    if image.dtype != np.uint8:
        image = np.clip(image, 0, 255).astype(np.uint8)
    return image


def resize(image: np.ndarray, size: int) -> np.ndarray:
    import cv2

    return cv2.resize(image, (size, size), interpolation=cv2.INTER_AREA)


TRAIN_SOURCE_SIZE = 256  # PlantVillage images are 256x256


def model_input(rgb: np.ndarray) -> np.ndarray:
    """
    Resize like training: Keras flow_from_directory loads 256px PlantVillage images and
    resizes them to 224px with *nearest* interpolation. Large photos are first smoothly
    downscaled to 256px so nearest sampling does not alias. Mirrored in inference.js.
    """
    import cv2

    h, w = rgb.shape[:2]
    if max(h, w) > TRAIN_SOURCE_SIZE:
        rgb = cv2.resize(rgb, (TRAIN_SOURCE_SIZE, TRAIN_SOURCE_SIZE), interpolation=cv2.INTER_AREA)
    return cv2.resize(rgb, (IMG_SIZE, IMG_SIZE), interpolation=cv2.INTER_NEAREST)


def preprocess(rgb224: np.ndarray) -> np.ndarray:
    """Replicates tf.keras.applications.resnet50.preprocess_input (caffe mode)."""
    bgr = rgb224[..., ::-1].astype(np.float32)
    return (bgr - MEAN_BGR)[None, ...]


def rgb_to_hsv_cv(rgb: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """OpenCV-style 8-bit HSV (H in 0..180, S/V in 0..255), written out explicitly
    so the JavaScript port can match it exactly."""
    rgbf = rgb.astype(np.float32)
    r, g, b = rgbf[..., 0], rgbf[..., 1], rgbf[..., 2]
    v = rgbf.max(axis=-1)
    mn = rgbf.min(axis=-1)
    delta = v - mn
    s = np.where(v > 0, delta / np.maximum(v, 1e-6) * 255.0, 0.0)

    safe = np.maximum(delta, 1e-6)
    h = np.zeros_like(v)
    is_r = (v == r) & (delta > 0)
    is_g = (v == g) & (delta > 0) & ~is_r
    is_b = (delta > 0) & ~is_r & ~is_g
    h = np.where(is_r, 60.0 * (g - b) / safe, h)
    h = np.where(is_g, 120.0 + 60.0 * (b - r) / safe, h)
    h = np.where(is_b, 240.0 + 60.0 * (r - g) / safe, h)
    h = np.where(h < 0, h + 360.0, h) / 2.0
    return h, s, v


def plant_masks(rgb: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Return (plant_mask, green_mask). Plant = green, yellow or brown tissue."""
    h, s, v = rgb_to_hsv_cv(rgb)
    colourful = (s >= 40) & (v >= 40)
    plant = colourful & (h >= 8) & (h <= 95)
    green = colourful & (h >= 30) & (h <= 95)
    return plant, green


def fill_holes(mask: np.ndarray) -> np.ndarray:
    """Pixels not reachable from the border through non-mask pixels (4-connected)."""
    height, width = mask.shape
    outside = np.zeros_like(mask, dtype=bool)
    queue: deque[tuple[int, int]] = deque()
    for x in range(width):
        for y in (0, height - 1):
            if not mask[y, x] and not outside[y, x]:
                outside[y, x] = True
                queue.append((y, x))
    for y in range(height):
        for x in (0, width - 1):
            if not mask[y, x] and not outside[y, x]:
                outside[y, x] = True
                queue.append((y, x))
    while queue:
        y, x = queue.popleft()
        for ny, nx in ((y - 1, x), (y + 1, x), (y, x - 1), (y, x + 1)):
            if 0 <= ny < height and 0 <= nx < width and not mask[ny, nx] and not outside[ny, nx]:
                outside[ny, nx] = True
                queue.append((ny, nx))
    return ~outside


def locate_leaf(rgb: np.ndarray) -> dict[str, float] | None:
    """
    Detect the largest leaf: HSV plant mask -> fill holes -> largest 4-connected component
    (cv2.connectedComponentsWithStats). Returns a normalised box or None.
    Mirrored in inference.js (locateLeaf).
    """
    import cv2

    small = resize(rgb, ANALYSIS_SIZE)
    plant, _ = plant_masks(small)
    leaf = fill_holes(plant).astype(np.uint8)
    count, _, stats, _ = cv2.connectedComponentsWithStats(leaf, connectivity=4)
    if count <= 1:
        return None
    best = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
    x, y, w, h, area = stats[best]
    if area < QUALITY["cropMinArea"] * ANALYSIS_SIZE * ANALYSIS_SIZE:
        return None
    return {"x": x / ANALYSIS_SIZE, "y": y / ANALYSIS_SIZE, "w": w / ANALYSIS_SIZE, "h": h / ANALYSIS_SIZE}


def crop_to_leaf(rgb: np.ndarray, box: dict[str, float] | None) -> tuple[np.ndarray, dict[str, float]]:
    """Padded square crop around the detected leaf, so background does not confuse the classifier."""
    full = {"x": 0.0, "y": 0.0, "w": 1.0, "h": 1.0}
    if box is None:
        return rgb, full
    height, width = rgb.shape[:2]
    bw, bh = box["w"] * width, box["h"] * height
    if bw * bh > QUALITY["cropMaxArea"] * width * height:
        return rgb, full
    side = min(max(bw, bh) * QUALITY["cropPad"], width, height)
    cx, cy = (box["x"] + box["w"] / 2) * width, (box["y"] + box["h"] / 2) * height
    x0 = int(round(min(max(cx - side / 2, 0), width - side)))
    y0 = int(round(min(max(cy - side / 2, 0), height - side)))
    side_px = int(round(side))
    crop = rgb[y0:y0 + side_px, x0:x0 + side_px]
    return crop, {"x": x0 / width, "y": y0 / height, "w": side_px / width, "h": side_px / height}


def laplacian_variance(gray: np.ndarray) -> float:
    g = gray.astype(np.float32)
    lap = -4.0 * g[1:-1, 1:-1] + g[:-2, 1:-1] + g[2:, 1:-1] + g[1:-1, :-2] + g[1:-1, 2:]
    return float(lap.var())


def to_gray(rgb: np.ndarray) -> np.ndarray:
    rgbf = rgb.astype(np.float32)
    return 0.299 * rgbf[..., 0] + 0.587 * rgbf[..., 1] + 0.114 * rgbf[..., 2]


def analyse_image(rgb224: np.ndarray) -> dict[str, Any]:
    """Quality metrics + affected-area estimate on the 224x224 model input."""
    small = resize(rgb224, ANALYSIS_SIZE)
    plant, green = plant_masks(small)
    leaf = fill_holes(plant)
    leaf_px = int(leaf.sum())
    affected = leaf & ~green
    gray = to_gray(rgb224)
    return {
        "plant_ratio": round(float(plant.mean()), 4),
        "green_ratio": round(float(green.mean()), 4),
        "brightness": round(float(gray.mean()), 1),
        "sharpness": round(laplacian_variance(gray), 1),
        "affected_area_pct": round(float(100.0 * affected.sum() / leaf_px), 1) if leaf_px else 0.0,
    }


def quality_gate(metrics: dict[str, Any]) -> tuple[str | None, list[str]]:
    """Return (rejection_reason or None, warnings)."""
    warnings: list[str] = []
    if metrics["plant_ratio"] < QUALITY["minPlantRatio"] or metrics["green_ratio"] < QUALITY["minGreenRatio"]:
        return "not_leaf", warnings
    if metrics["brightness"] < QUALITY["minBrightness"]:
        return "too_dark", warnings
    if metrics["brightness"] > QUALITY["maxBrightness"]:
        return "overexposed", warnings
    if metrics["sharpness"] < QUALITY["blurReject"]:
        return "blurry", warnings
    if metrics["sharpness"] < QUALITY["blurWarn"]:
        warnings.append("slightly_blurry")
    return None, warnings


def health_split(label: str, affected_pct: float) -> dict[str, float]:
    """
    Good vs bad share of the leaf. A leaf classified healthy is 100% good; otherwise
    the estimated affected tissue is "bad" (at least 1%, since disease was detected).
    Mirrored in frontend/src/lib/inference.js (healthSplit).
    """
    if is_healthy(label):
        return {"good_pct": 100.0, "bad_pct": 0.0}
    bad = round(min(100.0, max(1.0, float(affected_pct))), 1)
    return {"good_pct": round(100.0 - bad, 1), "bad_pct": bad}


def severity_from_area(label: str, affected_pct: float) -> str:
    if is_healthy(label):
        return "healthy"
    if affected_pct >= SEVERITY["severe"]:
        return "severe"
    if affected_pct >= SEVERITY["moderate"]:
        return "moderate"
    return "mild"


# ---------------------------------------------------------------------------
# Grad-CAM from head weights
# ---------------------------------------------------------------------------

@dataclass
class HeadWeights:
    w1: np.ndarray  # (C, H1)  Keras Dense kernel layout (in, out)
    b1: np.ndarray  # (H1,)
    w2: np.ndarray  # (H1, K)
    b2: np.ndarray  # (K,)

    def forward(self, features: np.ndarray) -> np.ndarray:
        g = features.reshape(-1, features.shape[-1]).mean(axis=0)
        h = np.maximum(g @ self.w1 + self.b1, 0.0)
        z = h @ self.w2 + self.b2
        z = z - z.max()
        e = np.exp(z)
        return e / e.sum()


def gradcam_from_features(features: np.ndarray, head: HeadWeights, class_index: int) -> np.ndarray:
    """
    Grad-CAM heatmap (feature-map resolution, values 0..1).

    features: (H, W, C) activations of the last conv block.
    The target is the softmax probability of `class_index`, matching
    model/gradcam.py which differentiates `predictions[:, class_index]`.
    """
    fh, fw, c = features.shape
    g = features.reshape(-1, c).mean(axis=0)
    pre = g @ head.w1 + head.b1
    h = np.maximum(pre, 0.0)
    z = h @ head.w2 + head.b2
    z = z - z.max()
    p = np.exp(z) / np.exp(z).sum()

    one_hot = np.zeros_like(p)
    one_hot[class_index] = 1.0
    dz = p[class_index] * (one_hot - p)          # d p_c / d z
    dh = head.w2 @ dz                            # d p_c / d h
    dpre = dh * (pre > 0)                        # through ReLU
    dg = head.w1 @ dpre                          # d p_c / d g   (C,)
    alpha = dg / float(fh * fw)                  # mean spatial gradient per channel

    cam = np.maximum(features @ alpha, 0.0)
    peak = cam.max()
    return (cam / (peak + 1e-8)).astype(np.float32)


def jet_colormap(values: np.ndarray) -> np.ndarray:
    """Matplotlib/OpenCV-like JET colormap for values in 0..1 -> uint8 RGB."""
    v = np.clip(values, 0.0, 1.0)
    r = np.clip(1.5 - np.abs(4.0 * v - 3.0), 0.0, 1.0)
    g = np.clip(1.5 - np.abs(4.0 * v - 2.0), 0.0, 1.0)
    b = np.clip(1.5 - np.abs(4.0 * v - 1.0), 0.0, 1.0)
    return (np.stack([r, g, b], axis=-1) * 255).astype(np.uint8)


def overlay_heatmap(rgb: np.ndarray, cam: np.ndarray, alpha: float = 0.45, max_side: int = 512) -> np.ndarray:
    import cv2

    h, w = rgb.shape[:2]
    scale = min(1.0, max_side / max(h, w))
    out_w, out_h = max(1, int(w * scale)), max(1, int(h * scale))
    base = cv2.resize(rgb, (out_w, out_h), interpolation=cv2.INTER_AREA)
    heat = cv2.resize(cam, (out_w, out_h), interpolation=cv2.INTER_CUBIC)
    colored = jet_colormap(heat)
    return (alpha * colored + (1.0 - alpha) * base).astype(np.uint8)


def encode_jpeg_data_url(rgb: np.ndarray, quality: int = 85) -> str:
    import cv2

    ok, buf = cv2.imencode(".jpg", rgb[..., ::-1], [int(cv2.IMWRITE_JPEG_QUALITY), quality])
    if not ok:
        raise ValueError("Could not encode heatmap image")
    return "data:image/jpeg;base64," + base64.b64encode(buf.tobytes()).decode()


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_head(model_dir: Path, meta: dict[str, Any]) -> HeadWeights:
    raw = np.fromfile(model_dir / meta["head"]["file"], dtype="<f4")
    arrays: dict[str, np.ndarray] = {}
    offset = 0
    for name, shape in meta["head"]["layout"]:
        size = int(np.prod(shape))
        arrays[name] = raw[offset: offset + size].reshape(shape)
        offset += size
    if offset != raw.size:
        raise ModelNotAvailable("head_weights.bin size does not match head_meta.json layout")
    return HeadWeights(arrays["W1"], arrays["b1"], arrays["W2"], arrays["b2"])


class Engine:
    """Loads the ONNX model + metadata once and serves diagnoses."""

    def __init__(self, model_dir: str | Path | None = None, session: Any = None):
        self.model_dir = Path(model_dir or os.getenv("MODEL_DIR") or DEFAULT_MODEL_DIR)
        meta_path = self.model_dir / "head_meta.json"
        if not meta_path.exists():
            raise ModelNotAvailable(
                f"Model metadata not found at {meta_path}. Export the model with "
                "model/export_onnx.py (see notebooks/export_onnx.ipynb)."
            )
        self.meta = json.loads(meta_path.read_text(encoding="utf-8"))
        self.labels: list[str] = self.meta["labels"]
        self.head = load_head(self.model_dir, self.meta)

        if session is None:
            model_path = self.model_dir / self.meta["model_file"]
            if not model_path.exists():
                raise ModelNotAvailable(f"ONNX model not found at {model_path}")
            import onnxruntime as ort

            opts = ort.SessionOptions()
            opts.intra_op_num_threads = int(os.getenv("ORT_THREADS", "2"))
            session = ort.InferenceSession(str(model_path), sess_options=opts, providers=["CPUExecutionProvider"])
        self.session = session
        self.input_name = self.meta.get("input_name") or session.get_inputs()[0].name
        self.features_name = self.meta["features_output"]
        self.probs_name = self.meta["probs_output"]

    # -- inference -----------------------------------------------------------
    def infer(self, rgb224: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        features, probs = self.session.run(
            [self.features_name, self.probs_name], {self.input_name: preprocess(rgb224)}
        )
        return np.asarray(probs)[0].astype(np.float64), np.asarray(features)[0].astype(np.float32)

    def diagnose(self, image: np.ndarray, with_gradcam: bool = True) -> dict[str, Any]:
        full = to_rgb_uint8(image)
        rgb, crop_box = crop_to_leaf(full, locate_leaf(full))
        rgb224 = model_input(rgb)
        metrics = analyse_image(rgb224)
        reason, warnings = quality_gate(metrics)
        if reason:
            return {"status": "rejected", "reason": reason, "warnings": warnings,
                    "metrics": metrics, "crop_box": crop_box, "inference": "server"}

        probs, features = self.infer(rgb224)
        order = np.argsort(probs)[::-1]
        idx = int(order[0])
        label = self.labels[idx]
        confidence = float(probs[idx])
        margin = confidence - float(probs[order[1]])
        top3 = [
            {"label": self.labels[int(i)], "pretty_label": format_label(self.labels[int(i)]),
             "confidence": round(float(probs[int(i)]), 4)}
            for i in order[:3]
        ]

        status = "ok"
        if confidence < QUALITY["minConfidence"] or margin < QUALITY["minMargin"]:
            status = "uncertain"

        result: dict[str, Any] = {
            "status": status,
            "reason": "low_confidence" if status == "uncertain" else None,
            "warnings": warnings,
            "label": label,
            "pretty_label": format_label(label),
            "crop": extract_crop_type(label),
            "confidence": round(confidence, 4),
            "top3": top3,
            "is_healthy": is_healthy(label),
            "affected_area_pct": 0.0 if is_healthy(label) else metrics["affected_area_pct"],
            "severity": severity_from_area(label, metrics["affected_area_pct"]),
            "health": health_split(label, metrics["affected_area_pct"]),
            "metrics": metrics,
            "crop_box": crop_box,
            "inference": "server",
            "model": {"quantization": self.meta.get("quantization"), "version": self.meta.get("version")},
        }
        if with_gradcam:
            cam = gradcam_from_features(features, self.head, idx)
            result["gradcam_image"] = encode_jpeg_data_url(overlay_heatmap(rgb, cam))
        return result
