import json
import re
from pathlib import Path

import numpy as np

from backend.tests.conftest import leaf_image
from model import runtime
from model.runtime import Engine, HeadWeights, gradcam_from_features

ROOT = Path(__file__).resolve().parents[2]


def test_gradcam_matches_finite_difference_gradients():
    rng = np.random.default_rng(3)
    head = HeadWeights(rng.normal(size=(6, 5)), rng.normal(size=5), rng.normal(size=(5, 4)), rng.normal(size=4))
    features = np.abs(rng.normal(size=(3, 3, 6)))
    cls, eps = 2, 1e-6

    # Grad-CAM channel weight = mean over pixels of d p_c / d A_ijk (numerically).
    alpha = np.zeros(6)
    for k in range(6):
        grads = np.zeros((3, 3))
        for i in range(3):
            for j in range(3):
                up = features.copy(); up[i, j, k] += eps
                dn = features.copy(); dn[i, j, k] -= eps
                grads[i, j] = (head.forward(up)[cls] - head.forward(dn)[cls]) / (2 * eps)
        alpha[k] = grads.mean()

    expected = np.maximum(features @ alpha, 0)
    expected = expected / (expected.max() + 1e-8)
    cam = gradcam_from_features(features, head, cls)
    assert cam.shape == (3, 3)
    assert np.allclose(cam, expected, atol=1e-4)


def test_preprocess_matches_resnet50_caffe_mode():
    rgb = np.zeros((224, 224, 3), dtype=np.uint8)
    rgb[..., 0] = 200  # pure red
    out = runtime.preprocess(rgb)
    assert out.shape == (1, 224, 224, 3)
    assert np.allclose(out[0, 0, 0], [-103.939, -116.779, 200 - 123.68], atol=1e-3)  # BGR order


def test_hsv_matches_opencv():
    import cv2

    rgb = np.random.default_rng(0).integers(0, 256, (32, 32, 3), dtype=np.uint8)
    h, s, v = runtime.rgb_to_hsv_cv(rgb)
    ref = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV).astype(np.float32)
    assert np.abs(h - ref[..., 0]).max() <= 1.0
    assert np.abs(s - ref[..., 1]).max() <= 1.0
    assert np.abs(v - ref[..., 2]).max() <= 1.0


def test_engine_probs_consistent_with_head_weights(fake_model_dir):
    engine = Engine(fake_model_dir)
    probs, features = engine.infer(runtime.resize(leaf_image(), 224))
    assert np.isclose(probs.sum(), 1.0, atol=1e-4)
    assert np.allclose(probs, engine.head.forward(features), atol=1e-4)


def test_quality_gate_rejects_old_fake_sample_and_accepts_leaf(fake_model_dir):
    engine = Engine(fake_model_dir)
    solid = np.full((224, 224, 3), (74, 28, 3), dtype=np.uint8)  # colour the old Samples tab sent
    rejected = engine.diagnose(solid)
    assert rejected["status"] == "rejected" and rejected["reason"] == "not_leaf"

    result = engine.diagnose(leaf_image())
    assert result["status"] in {"ok", "uncertain"}
    assert len(result["top3"]) == 3
    assert result["gradcam_image"].startswith("data:image/jpeg;base64,")


def test_blurry_leaf_is_rejected():
    import cv2

    blurred = cv2.GaussianBlur(leaf_image(spots=False), (0, 0), 12)
    reason, _ = runtime.quality_gate(runtime.analyse_image(runtime.resize(blurred, 224)))
    assert reason == "blurry"


def test_affected_area_and_severity():
    healthy = runtime.analyse_image(runtime.resize(leaf_image(spots=False), 224))
    spotted = runtime.analyse_image(runtime.resize(leaf_image(spots=True), 224))
    assert spotted["affected_area_pct"] > healthy["affected_area_pct"] + 3
    assert runtime.severity_from_area("Tomato___healthy", 40) == "healthy"
    assert runtime.severity_from_area("Tomato___Early_blight", 5) == "mild"
    assert runtime.severity_from_area("Tomato___Early_blight", 12) == "moderate"
    assert runtime.severity_from_area("Tomato___Early_blight", 30) == "severe"


def test_health_split():
    assert runtime.health_split("Apple___healthy", 12.0) == {"good_pct": 100.0, "bad_pct": 0.0}
    assert runtime.health_split("Tomato___Early_blight", 18.24) == {"good_pct": 81.8, "bad_pct": 18.2}
    assert runtime.health_split("Tomato___Early_blight", 0.0) == {"good_pct": 99.0, "bad_pct": 1.0}


def _js_object(name: str) -> dict:
    src = (ROOT / "frontend" / "src" / "lib" / "inference.js").read_text(encoding="utf-8")
    match = re.search(rf"export const {name} = (\{{.*?\}})", src, re.S)
    assert match, f"{name} not found in inference.js"
    return json.loads(match.group(1))


def test_thresholds_in_sync_with_browser_implementation():
    assert _js_object("QUALITY") == runtime.QUALITY
    assert _js_object("SEVERITY") == runtime.SEVERITY


def test_leaf_detection_crops_framed_leaf():
    leaf = leaf_image(300)
    frame = np.full((480, 640, 3), 110, dtype=np.uint8)
    frame[120:420, 250:550] = leaf
    box = runtime.locate_leaf(frame)
    assert box is not None
    crop, rect = runtime.crop_to_leaf(frame, box)
    assert rect["w"] < 0.7 and crop.shape[0] == crop.shape[1]
    # A photo that is already mostly leaf is left alone
    _, full = runtime.crop_to_leaf(leaf, runtime.locate_leaf(leaf))
    assert full == {"x": 0.0, "y": 0.0, "w": 1.0, "h": 1.0} or full["w"] > 0.5
