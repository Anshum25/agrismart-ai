"""
AgriSmart AI — export the trained Keras ResNet50 to ONNX for server + browser.

Produces (in --out-dir, default model/weights/export/):

  web/model/agrismart.onnx      two outputs: last-conv features + class probabilities
  web/model/head_weights.bin    float32 W1, b1, W2, b2 of the classification head
  web/model/head_meta.json      tensor names, layout, labels, quantization, sha256
  web/samples/*.jpg             6 real test-split images for the demo "Samples" tab
  parity_report.json            Keras vs ONNX agreement + Grad-CAM similarity
  classification_report.json    per-class precision / recall / F1 on the test split
  confusion_matrix.csv

Copy the *contents* of web/ into frontend/public/ and commit them. The API and
the browser both load frontend/public/model/.

Run on Google Colab (see notebooks/export_onnx.ipynb):
    python model/export_onnx.py --keras model/weights/agrismart_resnet50.keras \
        --data-dir data/plantvillage/color
"""

from __future__ import annotations

import argparse
import csv
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from model.config import DEFAULT_CLASS_LABELS, WEIGHTS_DIR  # noqa: E402
from model.runtime import (  # noqa: E402
    IMG_SIZE,
    HeadWeights,
    gradcam_from_features,
    model_input,
    preprocess,
    sha256_file,
)

SAMPLE_CLASSES = {
    "tomato_early_blight.jpg": "Tomato___Early_blight",
    "apple_scab.jpg": "Apple___Apple_scab",
    "potato_late_blight.jpg": "Potato___Late_blight",
    "corn_gray_leaf_spot.jpg": "Corn_(maize)___Cercospora_leaf_spot Gray_leaf_spot",
    "grape_black_rot.jpg": "Grape___Black_rot",
    "tomato_healthy.jpg": "Tomato___healthy",
}


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Export AgriSmart AI model to ONNX")
    p.add_argument("--keras", default=str(WEIGHTS_DIR / "agrismart_resnet50.keras"))
    p.add_argument("--labels", default=str(WEIGHTS_DIR / "class_labels.json"))
    p.add_argument("--data-dir", required=True, help="PlantVillage color folder (one subfolder per class)")
    p.add_argument("--out-dir", default=str(WEIGHTS_DIR / "export"))
    p.add_argument("--calib-images", type=int, default=200)
    p.add_argument("--parity-images", type=int, default=500)
    p.add_argument("--full-eval", action="store_true", help="Per-class metrics on the full test split (GPU recommended)")
    p.add_argument("--no-quantize", action="store_true", help="Ship float32 instead of int8")
    p.add_argument("--opset", type=int, default=17)
    return p.parse_args()


def load_labels(path: Path) -> list[str]:
    if path.exists():
        labels = json.loads(path.read_text(encoding="utf-8"))["labels"]
    else:
        print(f"[warn] {path} not found - falling back to DEFAULT_CLASS_LABELS (alphabetical, same as training)")
        labels = list(DEFAULT_CLASS_LABELS)
    if sorted(labels) != labels:
        print("[warn] labels are not alphabetical; make sure they match the training class_indices")
    return labels


def load_rgb224(path: str) -> np.ndarray:
    return model_input(np.asarray(Image.open(path).convert("RGB")))


def build_two_output_model(tf, model):
    """Same split as model/gradcam.py:make_gradcam_model."""
    base = model.layers[1]
    if not isinstance(base, tf.keras.Model):
        raise SystemExit("Expected model.layers[1] to be the ResNet50 backbone (see model/train.py:build_model)")
    inp = tf.keras.Input(shape=(IMG_SIZE, IMG_SIZE, 3), name="image")
    features = base(inp, training=False)
    x = features
    for layer in model.layers[2:]:
        x = layer(x)
    return tf.keras.Model(inp, [features, x], name="agrismart_export")


def export_head(model, out_model_dir: Path) -> tuple[HeadWeights, list]:
    dense1 = model.get_layer("head_dense")
    dense2 = model.get_layer("predictions")
    w1, b1 = [w.astype("<f4") for w in dense1.get_weights()]
    w2, b2 = [w.astype("<f4") for w in dense2.get_weights()]
    with (out_model_dir / "head_weights.bin").open("wb") as f:
        for arr in (w1, b1, w2, b2):
            f.write(np.ascontiguousarray(arr).tobytes())
    layout = [["W1", list(w1.shape)], ["b1", list(b1.shape)], ["W2", list(w2.shape)], ["b2", list(b2.shape)]]
    return HeadWeights(w1, b1, w2, b2), layout


def convert_to_onnx(tf, export_model, fp32_path: Path, opset: int) -> None:
    saved_dir = Path(tempfile.mkdtemp()) / "saved_model"
    if hasattr(export_model, "export"):
        export_model.export(str(saved_dir))  # Keras 3
    else:
        tf.saved_model.save(export_model, str(saved_dir))
    subprocess.run(
        [sys.executable, "-m", "tf2onnx.convert", "--saved-model", str(saved_dir),
         "--output", str(fp32_path), "--opset", str(opset)],
        check=True,
    )


def identify_outputs(session) -> tuple[str, str, str]:
    inp = session.get_inputs()[0].name
    features = probs = None
    for out in session.get_outputs():
        rank = len(out.shape)
        if rank == 4:
            features = out.name
        elif rank == 2:
            probs = out.name
    if not features or not probs:
        raise SystemExit(f"Could not identify outputs: {[ (o.name, o.shape) for o in session.get_outputs()]}")
    return inp, features, probs


def quantize(fp32_path: Path, int8_path: Path, calib_paths: list[str], input_name: str) -> None:
    from onnxruntime.quantization import CalibrationDataReader, QuantFormat, QuantType, quantize_static
    from onnxruntime.quantization.shape_inference import quant_pre_process

    class Reader(CalibrationDataReader):
        def __init__(self):
            self._it = iter(calib_paths)

        def get_next(self):
            path = next(self._it, None)
            return None if path is None else {input_name: preprocess(load_rgb224(path))}

    flush_every = 8
    if len(calib_paths) % flush_every == 0:
        # onnxruntime raises "No data is collected" when the final flushed batch is empty.
        calib_paths = calib_paths[:-1]
    pre_path = fp32_path.with_name("agrismart_pre.onnx")
    quant_pre_process(str(fp32_path), str(pre_path))
    quantize_static(
        str(pre_path), str(int8_path), Reader(),
        quant_format=QuantFormat.QDQ, per_channel=True,
        activation_type=QuantType.QUInt8, weight_type=QuantType.QInt8,
        # Flush collected activations regularly so calibration fits in a few GB of RAM.
        extra_options={"CalibMaxIntermediateOutputs": flush_every},
    )


def main() -> None:
    args = parse_args()
    import onnxruntime as ort
    import tensorflow as tf
    from sklearn.metrics import classification_report, confusion_matrix

    from model.gradcam import compute_heatmap
    from model.train import discover_images, stratified_split

    out_dir = Path(args.out_dir)
    web_model = out_dir / "web" / "model"
    web_samples = out_dir / "web" / "samples"
    for d in (web_model, web_samples):
        d.mkdir(parents=True, exist_ok=True)

    labels = load_labels(Path(args.labels))
    model = tf.keras.models.load_model(args.keras)
    export_model = build_two_output_model(tf, model)
    head, layout = export_head(model, web_model)

    # Same deterministic split as training (random_state=42) -> true held-out images.
    paths, path_labels = discover_images(Path(args.data_dir))
    train_p, _val_p, test_p, train_l, _val_l, test_l = stratified_split(paths, path_labels)
    rng = np.random.default_rng(0)
    calib = list(rng.choice(train_p, size=min(args.calib_images, len(train_p)), replace=False))
    parity_idx = rng.choice(len(test_p), size=min(args.parity_images, len(test_p)), replace=False)
    parity_paths = [test_p[i] for i in parity_idx]
    parity_labels = [test_l[i] for i in parity_idx]

    fp32_path = out_dir / "agrismart_fp32.onnx"
    print("Converting to ONNX ...")
    convert_to_onnx(tf, export_model, fp32_path, args.opset)
    fp32 = ort.InferenceSession(str(fp32_path), providers=["CPUExecutionProvider"])
    input_name, feat_name, prob_name = identify_outputs(fp32)

    chosen_path = fp32_path
    quantization = "fp32"
    if not args.no_quantize:
        print("Quantizing (static int8, QDQ) ...")
        int8_path = out_dir / "agrismart_int8.onnx"
        quantize(fp32_path, int8_path, calib, input_name)
        chosen_path, quantization = int8_path, "int8_qdq"

    print("Checking parity ...")
    candidates = {"fp32": fp32}
    if quantization == "int8_qdq":
        candidates["int8"] = ort.InferenceSession(str(chosen_path), providers=["CPUExecutionProvider"])

    correct = {"keras": 0, "fp32": 0, "int8": 0}
    agree = {"fp32": 0, "int8": 0}
    cam_sims: list[float] = []
    label_to_idx = {l: i for i, l in enumerate(labels)}
    for n, (path, true_label) in enumerate(zip(parity_paths, parity_labels)):
        rgb = load_rgb224(path)
        batch = preprocess(rgb)
        k_pred = int(np.argmax(model.predict(batch, verbose=0)[0]))
        correct["keras"] += int(k_pred == label_to_idx[true_label])
        for name, sess in candidates.items():
            feats, probs = sess.run([feat_name, prob_name], {input_name: batch})
            pred = int(np.argmax(probs[0]))
            agree[name] += int(pred == k_pred)
            correct[name] += int(pred == label_to_idx[true_label])
            if name == ("int8" if "int8" in candidates else "fp32") and n < 50:
                cam = gradcam_from_features(feats[0].astype(np.float32), head, k_pred)
                import cv2
                cam_up = cv2.resize(cam, (IMG_SIZE, IMG_SIZE))
                tf_cam = compute_heatmap(rgb, model=model, class_index=k_pred)
                a, b = cam_up.ravel(), tf_cam.ravel()
                cam_sims.append(float(a @ b / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-8)))

    n = len(parity_paths)
    report = {
        "images": n,
        "keras_accuracy": correct["keras"] / n,
        "fp32_accuracy": correct["fp32"] / n,
        "fp32_top1_agreement": agree["fp32"] / n,
        "shipped_quantization": quantization,
        "gradcam_cosine_similarity_mean": float(np.mean(cam_sims)) if cam_sims else None,
    }
    if "int8" in candidates:
        report["int8_accuracy"] = correct["int8"] / n
        report["int8_top1_agreement"] = agree["int8"] / n
        drop = report["keras_accuracy"] - report["int8_accuracy"]
        if drop > 0.01:
            print(f"[warn] int8 accuracy drop {drop:.2%} > 1% - shipping float32 instead")
            chosen_path, quantization = fp32_path, "fp32"
            report["shipped_quantization"] = "fp32"
    print(json.dumps(report, indent=2))
    (out_dir / "parity_report.json").write_text(json.dumps(report, indent=2))

    shutil.copy2(chosen_path, web_model / "agrismart.onnx")
    meta = {
        "version": 1,
        "model_file": "agrismart.onnx",
        "sha256": sha256_file(web_model / "agrismart.onnx"),
        "quantization": quantization,
        "input_name": input_name,
        "input_layout": "NHWC",
        "input_size": [IMG_SIZE, IMG_SIZE],
        "preprocess": "resnet50_caffe_bgr_mean",
        "features_output": feat_name,
        "probs_output": prob_name,
        "feature_shape": list(export_model.outputs[0].shape[1:]),
        "head": {"file": "head_weights.bin", "dtype": "float32", "layout": layout},
        "labels": labels,
        "parity": report,
    }
    (web_model / "head_meta.json").write_text(json.dumps(meta, indent=2))

    # Demo samples: first correctly + confidently classified test image per class.
    for filename, cls in SAMPLE_CLASSES.items():
        for path, true_label in zip(test_p, test_l):
            if true_label != cls:
                continue
            probs = model.predict(preprocess(load_rgb224(path)), verbose=0)[0]
            if labels[int(np.argmax(probs))] == cls and probs.max() > 0.9:
                Image.open(path).convert("RGB").save(web_samples / filename, quality=90)
                break

    if args.full_eval:
        print("Full test-split evaluation ...")
        y_true, y_pred = [], []
        for i in range(0, len(test_p), 64):
            chunk = test_p[i:i + 64]
            batch = np.concatenate([preprocess(load_rgb224(p)) for p in chunk])
            y_pred.extend(np.argmax(model.predict(batch, verbose=0), axis=1).tolist())
            y_true.extend(label_to_idx[l] for l in test_l[i:i + 64])
        cls_report = classification_report(y_true, y_pred, target_names=labels, output_dict=True, zero_division=0)
        (out_dir / "classification_report.json").write_text(json.dumps(cls_report, indent=2))
        cm = confusion_matrix(y_true, y_pred)
        with (out_dir / "confusion_matrix.csv").open("w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([""] + labels)
            for label, row in zip(labels, cm.tolist()):
                writer.writerow([label] + row)
        print(f"Test accuracy (full split): {cls_report['accuracy']:.4f}")

    reports_dir = out_dir / "web" / "model" / "reports"
    reports_dir.mkdir(exist_ok=True)
    for name in ("parity_report.json", "classification_report.json", "confusion_matrix.csv"):
        if (out_dir / name).exists():
            shutil.copy2(out_dir / name, reports_dir / name)
    archive = shutil.make_archive(str(out_dir.parent / "agrismart_export"), "zip", out_dir / "web")
    print(f"\nDone. Download {archive}, unzip it and copy model/ and samples/ into frontend/public/.")


if __name__ == "__main__":
    main()
