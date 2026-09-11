"""
AgriSmart AI — OpenCV live webcam demo.

Runs inference every ~15 frames (CPU-friendly). Press 'c' to classify immediately,
'q' to quit. Decoupled from Streamlit for demo recording.

Usage:
    python app/live_demo.py
    python app/live_demo.py --interval 20 --show-gradcam
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from model.gradcam import bounding_box_from_heatmap, compute_heatmap
from model.predict import format_label, load_model, predict_from_array


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="AgriSmart AI live webcam demo")
    parser.add_argument("--camera", type=int, default=0)
    parser.add_argument("--interval", type=int, default=15)
    parser.add_argument("--show-gradcam", action="store_true")
    return parser.parse_args()


def draw_prediction(frame, label, confidence, bbox=None, heatmap=None):
    display = frame.copy()
    text = f"{format_label(label)}  ({confidence:.0%})"
    cv2.rectangle(display, (8, 8), (min(640, 8 + len(text) * 11), 42), (0, 0, 0), -1)
    cv2.putText(display, text, (12, 32), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 120), 2)

    if bbox is not None:
        x, y, w, h = bbox
        cv2.rectangle(display, (x, y), (x + w, y + h), (0, 180, 255), 2)
        cv2.putText(display, "Grad-CAM focus", (x, max(y - 8, 16)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 180, 255), 1)
    elif heatmap is not None:
        mask = (heatmap > 0.55).astype(np.uint8)
        colored = np.zeros_like(display)
        colored[:, :, 2] = mask * 80
        display = cv2.addWeighted(display, 1.0, colored, 0.35, 0)

    cv2.putText(display, "c: classify now | q: quit", (8, display.shape[0] - 12),
                cv2.FONT_HERSHEY_SIMPLEX, 0.45, (200, 200, 200), 1)
    return display


def classify_frame(frame, use_gradcam):
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    label, confidence = predict_from_array(rgb)
    bbox, heatmap = None, None
    if use_gradcam:
        try:
            heatmap = compute_heatmap(rgb)
            bbox = bounding_box_from_heatmap(heatmap)
        except Exception:
            pass
    return label, confidence, bbox, heatmap


def main() -> None:
    args = parse_args()
    print("Loading model (once)...")
    try:
        load_model()
    except FileNotFoundError as exc:
        print(exc)
        sys.exit(1)

    cap = cv2.VideoCapture(args.camera)
    if not cap.isOpened():
        print(f"Could not open camera {args.camera}")
        sys.exit(1)

    frame_count = 0
    last_label, last_confidence = "Waiting...", 0.0
    last_bbox, last_heatmap = None, None
    infer_ms = 0.0

    print("Webcam started. Press 'c' to classify, 'q' to quit.")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame_count += 1
        force = False
        key = cv2.waitKey(1) & 0xFF
        if key == ord("q"):
            break
        if key == ord("c"):
            force = True

        if force or frame_count % args.interval == 0:
            t0 = time.perf_counter()
            last_label, last_confidence, last_bbox, last_heatmap = classify_frame(
                frame, args.show_gradcam,
            )
            infer_ms = (time.perf_counter() - t0) * 1000

        display = draw_prediction(
            frame, last_label, last_confidence,
            bbox=last_bbox if args.show_gradcam else None,
            heatmap=last_heatmap if args.show_gradcam and last_bbox is None else None,
        )
        cv2.putText(display, f"Inference: {infer_ms:.0f} ms", (8, 58),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.4, (180, 180, 180), 1)
        cv2.imshow("AgriSmart AI — Live Demo", display)

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
