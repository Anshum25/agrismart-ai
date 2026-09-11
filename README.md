# AgriSmart AI

AI-powered plant disease detection for hackathons and Smart India Hackathon (SIH) demos. Upload a leaf photo or use your webcam to get a disease classification, Grad-CAM explanation, and plain-language care advice from an LLM.


**What we adopted (ideas, not code):** ResNet50 backbone, two-phase fine-tuning, Grad-CAM visualization, and a separate inference/demo layer.

**What is original here:** project structure, training pipeline (`model/train.py`), inference API (`model/predict.py`), Hugging Face Mistral advice module, Streamlit app, OpenCV live demo, Colab notebook, and all implementation code in this repository.

## Project structure

```
agrismart-ai/
├── model/
│   ├── train.py          # Two-phase ResNet50 training (Colab-ready)
│   ├── predict.py        # predict(image_path) → (label, confidence)
│   ├── gradcam.py        # Grad-CAM heatmaps
│   ├── config.py         # Shared constants
│   └── weights/          # Saved model (gitignored — train or download)
├── app/
│   ├── app.py            # Streamlit main app
│   └── live_demo.py      # OpenCV webcam demo (separate from Streamlit)
├── bonus/
│   └── assistant.py      # Hugging Face LLM care advice
├── data/                 # Local dataset cache (gitignored)
├── notebooks/
│   └── colab_train.ipynb # Colab training walkthrough
├── report/
├── requirements.txt
├── .env.example
└── README.md
```

## Quick start (local)

### 1. Clone and install

```bash
cd agrismart-ai
python -m venv venv
# Windows: venv\Scripts\activate
# macOS/Linux: source venv/bin/activate
pip install -r requirements.txt
```

### 2. Model weights

Weights are **not** committed to git. Choose one:

| Option | Steps |
|--------|--------|
| **Train on Colab** | Open `notebooks/colab_train.ipynb`, enable GPU, run training. Download `agrismart_resnet50.keras` + `class_labels.json` into `model/weights/`. |
| **Train locally** | Download [PlantVillage on Kaggle](https://www.kaggle.com/datasets/abdallahalidev/plantvillage-dataset), then: `python model/train.py --data-dir path/to/color` |
| **Kaggle API** | Place `kaggle.json` in `~/.kaggle/`, then: `python model/train.py --kaggle-download` |

Expected files:

```
model/weights/agrismart_resnet50.keras
model/weights/class_labels.json
```

### 3. Hugging Face token (LLM advice)

1. Create a free account at [huggingface.co](https://huggingface.co)
2. Generate a token: [Settings → Access Tokens](https://huggingface.co/settings/tokens)
3. Copy `.env.example` → `.env` and set:

```env
HUGGINGFACE_TOKEN=hf_your_token_here
```

If the token is missing or the API is unavailable, the app falls back to canned advice (no crash).

### 4. Run Streamlit app

From the project root:

```bash
streamlit run app/app.py
```

Upload a leaf image → see prediction, confidence, Grad-CAM overlay, and care advice.

### 5. Run OpenCV live demo (separate terminal)

Optimized for **CPU-only** Mac/laptop (inference every 15 frames, model loaded once):

```bash
python app/live_demo.py
python app/live_demo.py --show-gradcam   # with Grad-CAM bounding box
```

| Key | Action |
|-----|--------|
| `c` | Force immediate classification |
| `q` | Quit |

## Training on Google Colab

1. **Runtime → Change runtime type → T4 GPU**
2. Upload or clone this repo
3. Add Kaggle credentials (`kaggle.json` → `~/.kaggle/`)
4. Run:

```bash
!pip install -r requirements.txt
!python model/train.py --colab --kaggle-download \
    --drive-path /content/drive/MyDrive/AgriSmartAI/weights \
    --output-dir model/weights
```

Checkpoints sync to Google Drive. After training, download weights to your local `model/weights/`.

See `notebooks/colab_train.ipynb` for a step-by-step notebook.

## Model details

| Setting | Value |
|---------|--------|
| Backbone | ResNet50 (ImageNet weights) |
| Head | GAP → Dense(256, relu) → Dropout(0.4) → Dense(38, softmax) |
| Phase 1 | Frozen base, lr=1e-4 |
| Phase 2 | Unfreeze last 30 base layers, lr=1e-5 |
| Split | Stratified 70% / 15% / 15% (train / val / test) |
| Augmentation | flips, rotation, zoom, shift, brightness/contrast |
| Callbacks | EarlyStopping, ReduceLROnPlateau, ModelCheckpoint |

## Inference API (for judges)

```python
from model.predict import predict, predict_from_array

label, confidence = predict("path/to/leaf.jpg")
# label e.g. "Tomato___Early_blight", confidence e.g. 0.94

import cv2
frame = cv2.imread("leaf.jpg")
label, confidence = predict_from_array(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
```

## Dataset

- **Source:** [PlantVillage on Kaggle](https://www.kaggle.com/datasets/abdallahalidev/plantvillage-dataset) — 38 classes, ~54k color leaf images
- **License:** Check Kaggle dataset page for current terms
- **Local path:** `data/plantvillage/` (gitignored)

## Reported metrics

Fill in after training:

| Metric | Score |
|--------|-------|
| Test accuracy | TBD |
| Macro-F1 | TBD |

Training writes `model/weights/training_metrics.json` after evaluation.

## Originality declaration

We declare that **AgriSmart AI** is our original implementation for this hackathon.

**Architecture reference (ideas only):**

> Ishaaq09, *Automated Plant Disease Detection using Deep Learning and Transfer Learning*  
> https://github.com/Ishaaq09/Automated_plant_disease_detection_using_Deep_Learning_and_Transfer_Learning

We studied that repository for the high-level pipeline (ResNet50 transfer learning → fine-tuning → Grad-CAM → deployment) and reimplemented all code independently in this repository.

## Demo video

[Link to demo video](#)

## License

See [LICENSE](LICENSE).
