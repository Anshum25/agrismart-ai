# AgriSmart AI — Model Report

## Objective

Classify plant leaf diseases across 38 PlantVillage classes using ResNet50 transfer learning.

## Architecture

```
Input (224×224×3)
    ↓
ResNet50 (ImageNet, partially fine-tuned)
    ↓
GlobalAveragePooling2D
    ↓
Dense(256, ReLU) → Dropout(0.4) → Dense(38, Softmax)
```

## Training protocol

1. **Phase 1:** Freeze ResNet50; train head only @ lr=1e-4
2. **Phase 2:** Unfreeze last 30 layers; fine-tune @ lr=1e-5
3. **Split:** Stratified 70/15/15 train/val/test
4. **Callbacks:** EarlyStopping (patience=5), ReduceLROnPlateau

## Results

| Metric | Value |
|--------|-------|
| Test accuracy | _Run training to populate_ |
| Test loss | _Run training to populate_ |

Metrics are saved to `model/weights/training_metrics.json` after `model/train.py` completes.

## Deployment export & verification

`model/export_onnx.py` (run via `notebooks/export_onnx.ipynb`) converts the Keras model to a two-output ONNX model
(last-conv features + probabilities), quantizes it to int8, and writes to `frontend/public/model/reports/`:

- `parity_report.json`: Keras vs ONNX accuracy and top-1 agreement on 500 held-out images, plus Grad-CAM cosine similarity against `model/gradcam.py`
- `classification_report.json`: per-class precision, recall and F1 on the full held-out test split
- `confusion_matrix.csv`

Paste the headline numbers into the table above once the export has been run.

## Explainability

Grad-CAM (`model/gradcam.py`) highlights image regions that drive predictions — useful for farmer trust and demo presentations.

## References

- PlantVillage dataset (Kaggle)
- Architecture inspiration: [Ishaaq09 plant disease repo](https://github.com/Ishaaq09/Automated_plant_disease_detection_using_Deep_Learning_and_Transfer_Learning)
