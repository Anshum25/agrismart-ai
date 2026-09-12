import numpy as np
from PIL import Image

def _generate_mock_gradcam(img_arr: np.ndarray) -> Image.Image:
    """Generates a highly realistic mock Grad-CAM heatmap for demo mode."""
    import cv2
    h, w = img_arr.shape[:2]
    heatmap = np.zeros((h, w), dtype=np.float32)
    center_x, center_y = w // 2, h // 2
    cv2.circle(heatmap, (center_x, center_y), min(w, h) // 3, 1.0, -1)
    heatmap = cv2.GaussianBlur(heatmap, (99, 99), 0)
    
    heatmap_uint8 = np.uint8(255 * heatmap)
    jet = cv2.applyColorMap(heatmap_uint8, cv2.COLORMAP_JET)
    
    img_bgr = cv2.cvtColor(img_arr, cv2.COLORMAP_RGB2BGR) if img_arr.shape[2] == 3 else img_arr
    overlay = cv2.addWeighted(img_bgr, 0.5, jet, 0.5, 0)
    overlay_rgb = cv2.cvtColor(overlay, cv2.COLORMAP_BGR2RGB)
    return Image.fromarray(overlay_rgb)

img = np.zeros((224, 224, 3), dtype=np.uint8)
try:
    out = _generate_mock_gradcam(img)
    print("SUCCESS")
except Exception as e:
    import traceback
    traceback.print_exc()
