"""
AgriSmart AI — OpenCV live webcam demo.

Runs inference every ~15 frames (CPU/MPS friendly for 8GB Mac).
Press 'c' to classify immediately, 'q' to quit. Decoupled from Streamlit for demo recording.

Usage:
    python app/live_demo.py
    python app/live_demo.py --interval 15 --show-gradcam
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
    parser.add_argument("--camera", type=int, default=0, help="Camera device index (default: 0)")
    parser.add_argument("--interval", type=int, default=15, help="Frames between inferences (default: 15)")
    parser.add_argument("--show-gradcam", action="store_true", help="Overlay Grad-CAM heatmap on feed")
    return parser.parse_args()


def draw_prediction(
    frame: np.ndarray,
    label: str,
    confidence: float,
    bbox: tuple[int, int, int, int] | None = None,
    heatmap: np.ndarray | None = None,
    fps: float = 0.0,
    infer_ms: float = 0.0,
) -> np.ndarray:
    display = frame.copy()

    # 1. Overlay heatmap on video feed when Grad-CAM is enabled
    if heatmap is not None:
        try:
            if heatmap.shape[:2] != display.shape[:2]:
                heatmap = cv2.resize(heatmap, (display.shape[1], display.shape[0]))
            colored = cv2.applyColorMap(np.uint8(255 * heatmap), cv2.COLORMAP_JET)
            display = cv2.addWeighted(display, 0.65, colored, 0.35, 0)
        except Exception:
            pass

    # 2. Top banner for prediction label + confidence
    text = f"{format_label(label)}  ({confidence:.0%})"
    box_w = min(display.shape[1] - 16, max(240, 16 + len(text) * 11))
    cv2.rectangle(display, (8, 8), (box_w, 42), (20, 28, 20), -1)
    cv2.putText(display, text, (14, 32), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 120), 2)

    # 3. Grad-CAM focus bounding box
    if bbox is not None:
        x, y, w, h = bbox
        cv2.rectangle(display, (x, y), (x + w, y + h), (0, 180, 255), 2)
        cv2.putText(
            display, "Grad-CAM focus", (x, max(y - 8, 18)),
            cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 180, 255), 1,
        )

    # 4. Performance overlay: FPS and inference latency
    perf_text = f"FPS: {fps:.1f} | Inference: {infer_ms:.0f} ms"
    perf_w = min(display.shape[1] - 16, 16 + len(perf_text) * 9)
    cv2.rectangle(display, (8, 48), (perf_w, 72), (20, 28, 20), -1)
    cv2.putText(display, perf_text, (14, 65), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (100, 220, 255), 1)

    # 5. Instructions footer
    cv2.putText(
        display, "c: classify now | q: quit", (8, display.shape[0] - 12),
        cv2.FONT_HERSHEY_SIMPLEX, 0.45, (220, 220, 220), 1,
    )
    return display


def classify_frame(frame: np.ndarray, use_gradcam: bool):
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
    print("Loading AgriSmart AI model weights (once)...")
    try:
        load_model()
        print("Model weights loaded successfully.")
    except FileNotFoundError as exc:
        print(exc)
        sys.exit(1)

    cap = cv2.VideoCapture(args.camera)
    if not cap.isOpened():
        print(f"Could not open camera {args.camera}. (Camera index {args.camera} unavailable)")
        sys.exit(1)

    frame_count = 0
    last_label, last_confidence = "Waiting...", 0.0
    last_bbox, last_heatmap = None, None
    infer_ms = 0.0
    fps = 0.0
    t_prev = time.perf_counter()

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

        # Calculate live FPS
        t_now = time.perf_counter()
        dt = t_now - t_prev
        t_prev = t_now
        if dt > 0:
            instant_fps = 1.0 / dt
            fps = instant_fps if fps == 0.0 else (fps * 0.85 + instant_fps * 0.15)

        # Run inference periodically or on 'c'
        if force or frame_count % args.interval == 0:
            t0 = time.perf_counter()
            last_label, last_confidence, last_bbox, last_heatmap = classify_frame(
                frame, args.show_gradcam,
            )
            infer_ms = (time.perf_counter() - t0) * 1000

        display = draw_prediction(
            frame,
            last_label,
            last_confidence,
            bbox=last_bbox if args.show_gradcam else None,
            heatmap=last_heatmap if args.show_gradcam else None,
            fps=fps,
            infer_ms=infer_ms,
        )
        cv2.imshow("AgriSmart AI — Live Demo", display)

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
