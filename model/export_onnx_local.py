"""
AgriSmart AI — export the Keras model to ONNX **without TensorFlow** (Windows/macOS/Linux, CPU).

Keras 3 can load the same .keras file on its PyTorch backend, and torch.onnx exports it.
Produces the same artefacts as model/export_onnx.py (the Colab/TensorFlow path).

    pip install torch --index-url https://download.pytorch.org/whl/cpu
    pip install "keras>=3.8" h5py onnx onnxruntime onnxscript pillow opencv-python-headless scikit-learn
    python model/export_onnx_local.py --keras model/weights/agrismart_resnet50_phase1.keras \
        --data-dir "data/plantvillage/plantvillage dataset/color"
"""

from __future__ import annotations

import os

os.environ.setdefault("KERAS_BACKEND", "torch")

import argparse  # noqa: E402
import csv  # noqa: E402
import json  # noqa: E402
import shutil  # noqa: E402
import sys  # noqa: E402
import time  # noqa: E402
from pathlib import Path  # noqa: E402

import numpy as np  # noqa: E402
from PIL import Image  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from model.config import TEST_RATIO, TRAIN_RATIO, VAL_RATIO, WEIGHTS_DIR  # noqa: E402
from model.export_onnx import SAMPLE_CLASSES, identify_outputs, load_labels, load_rgb224, quantize  # noqa: E402
from model.runtime import IMG_SIZE, HeadWeights, gradcam_from_features, preprocess, sha256_file  # noqa: E402

HEAD_LAYERS = ["gap", "head_dense", "head_dropout", "predictions"]


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--keras", default=str(WEIGHTS_DIR / "agrismart_resnet50.keras"))
    p.add_argument("--labels", default=str(WEIGHTS_DIR / "class_labels.json"))
    p.add_argument("--data-dir", default=None, help="PlantVillage color folder; needed for int8, parity and samples")
    p.add_argument("--out-dir", default=str(WEIGHTS_DIR / "export"))
    p.add_argument("--calib-images", type=int, default=200)
    p.add_argument("--parity-images", type=int, default=300)
    p.add_argument("--eval-images", type=int, default=0, help="Extra accuracy eval of the shipped ONNX (0 = skip)")
    p.add_argument("--no-quantize", action="store_true")
    return p.parse_args()


def discover(data_dir: Path) -> tuple[list[str], list[str]]:
    paths, labels = [], []
    for class_dir in sorted(d for d in data_dir.iterdir() if d.is_dir()):
        for img in sorted(class_dir.rglob("*")):
            if img.suffix.lower() in {".jpg", ".jpeg", ".png"}:
                paths.append(str(img))
                labels.append(class_dir.name)
    return paths, labels


def split(paths, labels):
    from sklearn.model_selection import train_test_split

    tr_p, tmp_p, tr_l, tmp_l = train_test_split(paths, labels, test_size=1 - TRAIN_RATIO, stratify=labels, random_state=42)
    rel = VAL_RATIO / (VAL_RATIO + TEST_RATIO)
    _, te_p, _, te_l = train_test_split(tmp_p, tmp_l, test_size=1 - rel, stratify=tmp_l, random_state=42)
    return tr_p, tr_l, te_p, te_l


def build_parts(keras, model):
    base = model.get_layer("resnet50")
    inp = keras.Input(shape=(IMG_SIZE, IMG_SIZE, 3), name="image")
    features = base(inp, training=False)
    x = features
    for name in HEAD_LAYERS:
        x = model.get_layer(name)(x)
    two_out = keras.Model(inp, [features, x], name="agrismart_export")

    feat_in = keras.Input(shape=tuple(features.shape[1:]))
    h = feat_in
    for name in HEAD_LAYERS:
        h = model.get_layer(name)(h)
    head_model = keras.Model(feat_in, h, name="agrismart_head")
    return two_out, head_model


def export_torch_onnx(torch, two_out, path: Path) -> None:
    class Wrapper(torch.nn.Module):
        def __init__(self, m):
            super().__init__()
            self.m = m

        def forward(self, image):
            features, probs = self.m(image, training=False)
            return features, probs

    wrapper = Wrapper(two_out).eval()
    dummy = torch.zeros(1, IMG_SIZE, IMG_SIZE, 3)
    kwargs = dict(input_names=["image"], output_names=["features", "probs"], opset_version=17)
    with torch.no_grad():
        try:
            torch.onnx.export(wrapper, (dummy,), str(path), dynamo=False, **kwargs)
        except TypeError:  # very old torch without the dynamo flag
            torch.onnx.export(wrapper, (dummy,), str(path), **kwargs)


def torch_gradcam(torch, two_out_conv, head_model, rgb224: np.ndarray, class_index: int) -> np.ndarray:
    x = torch.from_numpy(preprocess(rgb224))
    with torch.no_grad():
        feats = two_out_conv(x, training=False)[0]
    feats = feats.detach().clone().requires_grad_(True)
    probs = head_model(feats, training=False)
    probs[0, class_index].backward()
    grads = feats.grad[0].numpy()
    fmap = feats.detach()[0].numpy()
    cam = np.maximum(fmap @ grads.mean(axis=(0, 1)), 0)
    return cam / (cam.max() + 1e-8)


def main() -> None:
    args = parse_args()
    import keras
    import onnxruntime as ort
    import torch

    out_dir = Path(args.out_dir)
    web_model, web_samples = out_dir / "web" / "model", out_dir / "web" / "samples"
    reports = web_model / "reports"
    for d in (web_model, web_samples, reports):
        d.mkdir(parents=True, exist_ok=True)

    labels = load_labels(Path(args.labels))
    print("Loading Keras model (torch backend) ...")
    model = keras.saving.load_model(args.keras, compile=False)
    two_out, head_model = build_parts(keras, model)

    w1, b1 = [np.asarray(w, dtype="<f4") for w in model.get_layer("head_dense").get_weights()]
    w2, b2 = [np.asarray(w, dtype="<f4") for w in model.get_layer("predictions").get_weights()]
    with (web_model / "head_weights.bin").open("wb") as f:
        for arr in (w1, b1, w2, b2):
            f.write(np.ascontiguousarray(arr).tobytes())
    head = HeadWeights(w1, b1, w2, b2)
    layout = [["W1", list(w1.shape)], ["b1", list(b1.shape)], ["W2", list(w2.shape)], ["b2", list(b2.shape)]]

    fp32_path = out_dir / "agrismart_fp32.onnx"
    print("Exporting ONNX ...")
    export_torch_onnx(torch, two_out, fp32_path)
    fp32 = ort.InferenceSession(str(fp32_path), providers=["CPUExecutionProvider"])
    input_name, feat_name, prob_name = identify_outputs(fp32)

    report: dict = {"exporter": "keras-torch-backend", "keras_file": Path(args.keras).name}
    metrics_file = Path(args.keras).with_name("training_metrics.json")
    if metrics_file.exists():
        report["training_metrics"] = json.loads(metrics_file.read_text())

    chosen, quantization = fp32_path, "fp32"
    test_p: list[str] = []
    test_l: list[str] = []
    if args.data_dir:
        paths, path_labels = discover(Path(args.data_dir))
        print(f"Dataset: {len(paths)} images")
        tr_p, _tr_l, test_p, test_l = split(paths, path_labels)
        rng = np.random.default_rng(0)
        calib = list(rng.choice(tr_p, size=min(args.calib_images, len(tr_p)), replace=False))

        if not args.no_quantize:
            print("Quantizing (static int8, QDQ) ...")
            int8_path = out_dir / "agrismart_int8.onnx"
            quantize(fp32_path, int8_path, calib, input_name)
            int8 = ort.InferenceSession(str(int8_path), providers=["CPUExecutionProvider"])
        else:
            int8 = None

        print("Checking parity ...")
        idx = rng.choice(len(test_p), size=min(args.parity_images, len(test_p)), replace=False)
        label_to_idx = {l: i for i, l in enumerate(labels)}
        stats = {"keras": 0, "fp32": 0, "int8": 0, "fp32_agree": 0, "int8_agree": 0}
        cam_sims, max_prob_diff = [], 0.0
        start = time.time()
        for n, i in enumerate(idx):
            rgb = load_rgb224(test_p[i])
            truth = label_to_idx[test_l[i]]
            batch = preprocess(rgb)
            with torch.no_grad():
                k_probs = np.asarray(two_out(torch.from_numpy(batch), training=False)[1].cpu())[0]
            k_pred = int(np.argmax(k_probs))
            stats["keras"] += k_pred == truth
            f_feats, f_probs = fp32.run([feat_name, prob_name], {input_name: batch})
            max_prob_diff = max(max_prob_diff, float(np.abs(f_probs[0] - k_probs).max()))
            stats["fp32"] += int(np.argmax(f_probs)) == truth
            stats["fp32_agree"] += int(np.argmax(f_probs)) == k_pred
            if int8 is not None:
                i_feats, i_probs = int8.run([feat_name, prob_name], {input_name: batch})
                stats["int8"] += int(np.argmax(i_probs)) == truth
                stats["int8_agree"] += int(np.argmax(i_probs)) == k_pred
            if n < 30:
                ref = torch_gradcam(torch, two_out, head_model, rgb, k_pred).ravel()
                feats = (i_feats if int8 is not None else f_feats)[0].astype(np.float32)
                ours = gradcam_from_features(feats, head, k_pred).ravel()
                cam_sims.append(float(ref @ ours / (np.linalg.norm(ref) * np.linalg.norm(ours) + 1e-8)))
            if (n + 1) % 50 == 0:
                print(f"  {n + 1}/{len(idx)} ({time.time() - start:.0f}s)")
        n = len(idx)
        report.update({
            "parity_images": n,
            "split_note": "Stratified split recomputed locally (random_state=42, sorted paths); it may not match the "
                          "training run's split exactly, so these accuracies can be optimistic. Use training_metrics "
                          "for the official held-out number.",
            "keras_accuracy": stats["keras"] / n,
            "fp32_accuracy": stats["fp32"] / n,
            "fp32_top1_agreement": stats["fp32_agree"] / n,
            "fp32_max_abs_prob_diff": max_prob_diff,
            "gradcam_cosine_similarity_mean": float(np.mean(cam_sims)),
        })
        if int8 is not None:
            report["int8_accuracy"] = stats["int8"] / n
            report["int8_top1_agreement"] = stats["int8_agree"] / n
            if report["keras_accuracy"] - report["int8_accuracy"] <= 0.01 and report["int8_top1_agreement"] >= 0.97:
                chosen, quantization = int8_path, "int8_qdq"
            else:
                print("[warn] int8 parity below target - shipping float32")

        print("Picking demo samples ...")
        shipped = ort.InferenceSession(str(chosen), providers=["CPUExecutionProvider"])
        for filename, cls in SAMPLE_CLASSES.items():
            for p, l in zip(test_p, test_l):
                if l != cls:
                    continue
                probs = shipped.run([prob_name], {input_name: preprocess(load_rgb224(p))})[0][0]
                if labels[int(np.argmax(probs))] == cls and probs.max() > 0.9:
                    Image.open(p).convert("RGB").save(web_samples / filename, quality=90)
                    break

        if args.eval_images:
            print(f"Evaluating shipped model on {args.eval_images} images ...")
            from sklearn.metrics import classification_report, confusion_matrix

            eidx = rng.choice(len(test_p), size=min(args.eval_images, len(test_p)), replace=False)
            y_true, y_pred = [], []
            for i in eidx:
                probs = shipped.run([prob_name], {input_name: preprocess(load_rgb224(test_p[i]))})[0][0]
                y_true.append(label_to_idx[test_l[i]])
                y_pred.append(int(np.argmax(probs)))
            cls = classification_report(y_true, y_pred, labels=list(range(len(labels))), target_names=labels,
                                        output_dict=True, zero_division=0)
            (reports / "classification_report.json").write_text(json.dumps(cls, indent=2))
            cm = confusion_matrix(y_true, y_pred, labels=list(range(len(labels))))
            with (reports / "confusion_matrix.csv").open("w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow([""] + labels)
                for label, row in zip(labels, cm.tolist()):
                    writer.writerow([label] + row)
            report["eval_images"] = len(eidx)
            report["eval_accuracy"] = cls["accuracy"]

    report["shipped_quantization"] = quantization
    print(json.dumps(report, indent=2))
    (reports / "parity_report.json").write_text(json.dumps(report, indent=2))

    shutil.copy2(chosen, web_model / "agrismart.onnx")
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
        "feature_shape": [int(d) for d in two_out.outputs[0].shape[1:]],
        "head": {"file": "head_weights.bin", "dtype": "float32", "layout": layout},
        "labels": labels,
        "parity": report,
    }
    (web_model / "head_meta.json").write_text(json.dumps(meta, indent=2))
    print(f"\nDone. Copy {out_dir / 'web'}/* into frontend/public/")


if __name__ == "__main__":
    main()
