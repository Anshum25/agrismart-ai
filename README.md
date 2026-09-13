<div align="center">

# 🌿 AgriSmart AI
**Offline, explainable crop doctor for Indian farmers**

[![CI](https://github.com/Anshum25/agrismart-ai/actions/workflows/ci.yml/badge.svg)](https://github.com/Anshum25/agrismart-ai/actions/workflows/ci.yml)
[![React PWA](https://img.shields.io/badge/Frontend-React%20PWA-61DAFB?logo=react&logoColor=black)](https://react.dev/)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![ONNX](https://img.shields.io/badge/Model-ResNet50%20→%20ONNX-5C3EE8?logo=onnx&logoColor=white)](https://onnxruntime.ai/)
[![Groq](https://img.shields.io/badge/GenAI-GPT--OSS%20120B%20%2B%20Whisper-F55036)](https://groq.com/)

*Built for the Smart India Hackathon (SIH) 2026*

</div>

---

## 🚀 What it does

A farmer photographs a leaf, and AgriSmart AI:

1. **Checks the photo** and rejects anything that is not a leaf, too dark or blurry, with retake tips. It does not invent a diagnosis.
2. **Diagnoses 38 diseases across 14 crops on the phone itself** (ONNX Runtime Web), so it **works offline** once installed.
3. **Shows why**, with an exact Grad-CAM heatmap, the top-3 matches, and an **estimated % of leaf area affected** for severity.
   A **Good vs Bad health meter** shows the healthy share of the leaf (healthy leaves are "100% healthy").
   **Live scan mode** analyses the camera stream continuously — the leaf is detected (HSV segmentation + largest
   connected component), auto-cropped and diagnosed ~2×/second on the phone, no photo needed.
4. **Gives treatment advice in 9 Indian languages** (organic and chemical options with doses) and reads it aloud.
5. **Answers follow-up questions by voice** (Groq Whisper + GPT-OSS 120B, grounded in the diagnosis).
6. **Forecasts disease risk for the next 7 days** from local weather and suggests the best day to spray.
7. **Warns the community**: anonymous reports (~5 km precision) feed an **outbreak map** and **nearby alerts**.

Low-confidence results are clearly marked "not sure". Simulated demo data on the map is clearly labelled.

---

## 🏗️ Architecture

```text
             ┌──────────────────────── React PWA (Vercel) ────────────────────────┐
 photo ───►  │ quality gate → ONNX Runtime Web (worker) → Grad-CAM → severity     │ ◄── works offline
             │ offline advice packs · scan history (IndexedDB) · queued reports   │
             └───────────────┬────────────────────────────────────────────────────┘
                             │ HTTPS (when online)
             ┌───────────────▼──────────── FastAPI (Render) ──────────────────────┐
             │ /predict   same ONNX model + gate + Grad-CAM (no TensorFlow)       │
             │ /advice    Groq GPT-OSS 120B → offline pack → curated knowledge base  │
             │ /voice/ask Groq Whisper + GPT-OSS 120B                                │
             │ /insights  weather risk + irrigation + sustainability              │
             │ /forecast  Open-Meteo 7-day disease-risk rules + spray day         │
             │ /reports /alerts   SQLite outbreak reports (0.05° privacy grid)    │
             └────────────────────────────────────────────────────────────────────┘
```

```text
agrismart-ai/
├── frontend/                 React + Vite PWA
│   ├── public/model/         agrismart.onnx + head weights (from the export step)
│   ├── public/samples/       real held-out test images
│   ├── public/offline/       advice packs per language
│   └── src/
│       ├── lib/inference.js  on-device pipeline (mirror of model/runtime.py)
│       ├── lib/…             api client, IndexedDB store, speech, hooks
│       ├── i18n/             UI strings for 9 languages
│       ├── components/       ResultCard, AdvicePanel, VoiceAssistant, InsightsPanel, …
│       └── pages/            Home, Diagnose, Outbreaks, About
├── backend/                  FastAPI app, routes, SQLite, tests
├── model/
│   ├── train.py              two-phase ResNet50 transfer learning (Colab)
│   ├── export_onnx.py        Keras → ONNX (Colab, TensorFlow) + parity report
│   ├── runtime.py            TensorFlow-free inference, gate, Grad-CAM
│   └── gradcam.py, predict.py  TensorFlow reference implementations
├── bonus/                    advice (LLM + knowledge base), voice, weather/forecast, irrigation, sustainability
├── notebooks/                colab_train.ipynb, export_onnx.ipynb
└── scripts/                  offline advice packs, icon generation
```

---

## 📊 Model

ResNet50 (ImageNet) → GAP → Dense(256) → Dropout(0.4) → Dense(38), trained on PlantVillage (color) with a
stratified 70/15/15 split (`model/train.py`). The deployed checkpoint is **phase 1** (frozen backbone, trained head);
phase-2 fine-tuning of the last 30 layers is the next accuracy step.

| Metric | Value |
|---|---|
| Verified accuracy of the deployed ONNX model (1,500 PlantVillage images) | **88.6%** (macro F1 0.82) |
| ONNX vs Keras top-1 agreement | 100% |
| Weakest classes | Potato healthy, Tomato mosaic virus, Tomato early blight |
| Classes | 38 (14 crops) |
| Shipped format | ONNX (see `frontend/public/model/head_meta.json` and `reports/`) |

No TensorFlow? `model/export_onnx_local.py` exports the same artefacts using Keras on the PyTorch backend (CPU).

The export step (`notebooks/export_onnx.ipynb`) writes `parity_report.json` (Keras vs ONNX accuracy and top-1
agreement, Grad-CAM cosine similarity), plus `classification_report.json` and a confusion matrix on the same
held-out test split.

**Why auto-crop matters:** on 200 held-out images placed in camera-like frames, accuracy was 37.5% without
cropping and 89% with leaf detection + crop (same as the original images). Both the API and the browser crop to the
detected leaf before classifying.

**Honest limitation:** PlantVillage images are lab photos on plain backgrounds. Accuracy on real field photos is
lower, which is why the app has a quality gate, a "not sure" state and top-3 matches.

---

## 💻 Local setup

### 1. Export the model (once, on Google Colab)
Open `notebooks/export_onnx.ipynb` in Colab, provide your trained `agrismart_resnet50.keras`, and run all cells.
Unzip `agrismart_export.zip` and copy its `model/` and `samples/` folders into `frontend/public/`.

### 2. Backend
```bash
python -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -r backend/requirements.txt
cp .env.example .env                                  # add GROQ_API_KEY
uvicorn backend.main:app --reload --port 8000         # docs at http://localhost:8000/docs
```

### 3. Frontend
```bash
cd frontend
npm install
npm run dev            # http://localhost:5173 (proxies /api → :8000)
```

### 4. Tests
```bash
pip install pytest httpx onnx
pytest backend/tests -q
```
The tests build a tiny ONNX model with the same two-output contract, so they run without the real weights.

### 5. Offline advice packs (optional, needs `GROQ_API_KEY`)
```bash
python scripts/generate_offline_advice.py --langs en hi mr ta te kn bn gu pa
```

---

## ☁️ Deployment

**Backend — Render** (`render.yaml`): build `pip install -r backend/requirements.txt`, start
`uvicorn backend.main:app --host 0.0.0.0 --port $PORT`. It needs no TensorFlow and uses about 150–250 MB of RAM.

| Env var | Purpose |
|---|---|
| `GROQ_API_KEY` | AI advice + voice assistant |
| `FRONTEND_ORIGINS` | Comma-separated allowed origins, e.g. `https://your-app.vercel.app` |
| `MODEL_URL` / `MODEL_SHA256` | Optional: download the ONNX model if it is not in the repo |
| `DB_PATH` | SQLite path (Render free disk is ephemeral) |
| `SEED_DEMO_DATA` | `1` = seed clearly-labelled simulated outbreak reports when the DB is empty |

**Frontend — Vercel** (root `frontend/`): set `VITE_API_URL` to the Render URL. `vercel.json` keeps
`/model`, `/samples` and `/offline` out of the SPA rewrite.

---

## 🔌 API contract (`POST /predict`)

```json
{
  "status": "ok | uncertain | rejected",
  "reason": "not_leaf | too_dark | overexposed | blurry | low_confidence | null",
  "label": "Tomato___Early_blight",
  "pretty_label": "Tomato — Early blight",
  "confidence": 0.94,
  "top3": [{ "label": "…", "pretty_label": "…", "confidence": 0.94 }],
  "affected_area_pct": 18.2,
  "severity": "healthy | mild | moderate | severe",
  "gradcam_image": "data:image/jpeg;base64,…",
  "inference": "server"
}
```
The browser pipeline returns the same shape with `"inference": "device"`.

---

## 🏆 Originality

The React PWA, FastAPI backend, ResNet50 training and ONNX export pipeline, closed-form Grad-CAM, quality gate,
disease-risk forecast rules, outbreak reporting and the curated advice knowledge base were written for this hackathon.
Dataset: PlantVillage (via Kaggle). Map data © OpenStreetMap contributors. Weather: Open-Meteo.

> ⚠️ AgriSmart AI is decision support, not a substitute for an agronomist. Chemical doses are common extension
> recommendations; always follow the product label and your local KVK. Kisan Call Centre: 1800-180-1551.
