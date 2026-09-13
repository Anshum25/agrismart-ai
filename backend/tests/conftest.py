"""Test fixtures: a tiny real ONNX model with the same two-output contract as the
exported ResNet50 (features + probabilities), so the full pipeline runs without
the 25 MB production model or TensorFlow."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from model.config import DEFAULT_CLASS_LABELS  # noqa: E402

N_CLASSES = len(DEFAULT_CLASS_LABELS)
CHANNELS, HIDDEN = 8, 16


def build_fake_model(model_dir: Path, seed: int = 0) -> None:
    import onnx
    from onnx import TensorProto, helper, numpy_helper

    rng = np.random.default_rng(seed)
    conv_w = rng.normal(0, 0.05, (CHANNELS, 3, 1, 1)).astype(np.float32)
    w1 = rng.normal(0, 0.5, (CHANNELS, HIDDEN)).astype(np.float32)
    b1 = rng.normal(0, 0.1, (HIDDEN,)).astype(np.float32)
    w2 = rng.normal(0, 0.5, (HIDDEN, N_CLASSES)).astype(np.float32)
    b2 = rng.normal(0, 0.1, (N_CLASSES,)).astype(np.float32)

    inits = [numpy_helper.from_array(a, n) for a, n in [
        (conv_w, "conv_w"), (w1, "W1"), (b1, "b1"), (w2, "W2"), (b2, "b2"),
        (np.array([1, 2], dtype=np.int64), "axes_hw"),
    ]]
    nodes = [
        helper.make_node("Transpose", ["image"], ["nchw"], perm=[0, 3, 1, 2]),
        helper.make_node("AveragePool", ["nchw"], ["pooled"], kernel_shape=[32, 32], strides=[32, 32]),
        helper.make_node("Conv", ["pooled", "conv_w"], ["conv"]),
        helper.make_node("Relu", ["conv"], ["act"]),
        helper.make_node("Transpose", ["act"], ["features"], perm=[0, 2, 3, 1]),
        helper.make_node("ReduceMean", ["features", "axes_hw"], ["gap"], keepdims=0),
        helper.make_node("MatMul", ["gap", "W1"], ["d1m"]),
        helper.make_node("Add", ["d1m", "b1"], ["d1"]),
        helper.make_node("Relu", ["d1"], ["h"]),
        helper.make_node("MatMul", ["h", "W2"], ["d2m"]),
        helper.make_node("Add", ["d2m", "b2"], ["logits"]),
        helper.make_node("Softmax", ["logits"], ["probs"], axis=-1),
    ]
    graph = helper.make_graph(
        nodes, "fake_agrismart",
        [helper.make_tensor_value_info("image", TensorProto.FLOAT, [1, 224, 224, 3])],
        [helper.make_tensor_value_info("features", TensorProto.FLOAT, [1, 7, 7, CHANNELS]),
         helper.make_tensor_value_info("probs", TensorProto.FLOAT, [1, N_CLASSES])],
        inits,
    )
    model = helper.make_model(graph, opset_imports=[helper.make_opsetid("", 18)])
    model.ir_version = 9
    model_dir.mkdir(parents=True, exist_ok=True)
    onnx.save(model, str(model_dir / "agrismart.onnx"))

    with (model_dir / "head_weights.bin").open("wb") as f:
        for arr in (w1, b1, w2, b2):
            f.write(arr.astype("<f4").tobytes())
    meta = {
        "version": 1, "model_file": "agrismart.onnx", "quantization": "fp32",
        "input_name": "image", "features_output": "features", "probs_output": "probs",
        "feature_shape": [7, 7, CHANNELS],
        "head": {"file": "head_weights.bin", "dtype": "float32", "layout": [
            ["W1", list(w1.shape)], ["b1", list(b1.shape)], ["W2", list(w2.shape)], ["b2", list(b2.shape)],
        ]},
        "labels": list(DEFAULT_CLASS_LABELS),
    }
    (model_dir / "head_meta.json").write_text(json.dumps(meta))


def leaf_image(size: int = 400, spots: bool = True, seed: int = 1) -> np.ndarray:
    """Synthetic textured green leaf with brown lesions on a grey background."""
    import cv2

    rng = np.random.default_rng(seed)
    img = np.full((size, size, 3), 120, dtype=np.uint8)
    cv2.ellipse(img, (size // 2, size // 2), (int(size * 0.38), int(size * 0.25)), 30, 0, 360, (60, 150, 50), -1)
    if spots:
        for _ in range(10):
            center = tuple(int(v) for v in rng.integers(int(size * 0.35), int(size * 0.65), 2))
            cv2.circle(img, center, int(rng.integers(8, 20)), (120, 80, 30), -1)
    noise = rng.normal(0, 12, img.shape)
    return np.clip(img + noise, 0, 255).astype(np.uint8)


@pytest.fixture(scope="session")
def fake_model_dir(tmp_path_factory) -> Path:
    d = tmp_path_factory.mktemp("model")
    build_fake_model(d)
    return d


@pytest.fixture()
def client(fake_model_dir, tmp_path, monkeypatch):
    monkeypatch.setenv("MODEL_DIR", str(fake_model_dir))
    monkeypatch.setenv("DB_PATH", str(tmp_path / "test.db"))
    monkeypatch.setenv("SEED_DEMO_DATA", "0")
    monkeypatch.setenv("GROQ_API_KEY", "")
    monkeypatch.delenv("MODEL_URL", raising=False)
    from fastapi.testclient import TestClient

    from backend.main import app
    from backend.state import limiter

    limiter.reset()
    with TestClient(app) as test_client:
        yield test_client
