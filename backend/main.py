"""
AgriSmart AI — FastAPI backend
==============================
Serves the ONNX-exported ResNet50 model (no TensorFlow at runtime) plus the
advisory services used by the React PWA.

  GET  /health                 model + service status
  POST /predict                leaf image -> diagnosis (+ Grad-CAM)
  POST /advice                 structured treatment advice in 9 languages
  GET  /insights               live weather risk + irrigation + sustainability
  GET  /forecast               7-day disease risk forecast + best spray day
  POST /voice/ask              voice/text question -> answer (Groq Whisper + LLM)
  POST /reports                share an anonymous diagnosis to the outbreak map
  GET  /reports/aggregate      outbreak map cells
  GET  /alerts                 nearby disease alerts

Run from the project root:  uvicorn backend.main:app --reload
"""

from __future__ import annotations

import logging
import os
import sys
import urllib.request
from contextlib import asynccontextmanager
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(_ROOT / ".env")

from fastapi import FastAPI  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402
from slowapi import _rate_limit_exceeded_handler  # noqa: E402
from slowapi.errors import RateLimitExceeded  # noqa: E402

from backend import db  # noqa: E402
from backend.routes import advice, predict, reports  # noqa: E402
from backend.state import limiter, model_state  # noqa: E402
from bonus.assistant import groq_client  # noqa: E402
from model.runtime import DEFAULT_MODEL_DIR, Engine, ModelNotAvailable, sha256_file  # noqa: E402

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("agrismart.api")

VERSION = "2.0.0"


def download_model_if_missing(model_dir: Path) -> None:
    """Fetch the ONNX file from MODEL_URL when it is not bundled with the repo."""
    url = os.getenv("MODEL_URL", "").strip()
    target = model_dir / "agrismart.onnx"
    if target.exists() or not url:
        return
    model_dir.mkdir(parents=True, exist_ok=True)
    tmp = target.with_suffix(".part")
    log.info("Downloading model from %s", url)
    urllib.request.urlretrieve(url, tmp)
    expected = os.getenv("MODEL_SHA256", "").strip().lower()
    if expected and sha256_file(tmp) != expected:
        tmp.unlink(missing_ok=True)
        raise ModelNotAvailable("Downloaded model failed SHA256 verification")
    tmp.replace(target)


def load_engine() -> None:
    model_dir = Path(os.getenv("MODEL_DIR") or DEFAULT_MODEL_DIR)
    try:
        download_model_if_missing(model_dir)
        model_state.engine = Engine(model_dir)
        model_state.error = None
        log.info("Model loaded from %s (%s)", model_dir, model_state.engine.meta.get("quantization"))
    except Exception as exc:  # keep the API up for advice/forecast/map, but be honest
        model_state.engine = None
        model_state.error = str(exc)
        log.error("Model NOT loaded - /predict will return 503: %s", exc)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    db.init()
    if os.getenv("SEED_DEMO_DATA", "0") == "1" and db.count_reports() == 0:
        db.seed_demo_reports()
        log.info("Seeded simulated outbreak reports (source=demo_seed)")
    load_engine()
    yield


app = FastAPI(
    title="AgriSmart AI API",
    description="Explainable crop disease diagnosis and farmer advisory — Smart India Hackathon 2026",
    version=VERSION,
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

_origins = [o.strip() for o in os.getenv(
    "FRONTEND_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173,http://localhost:4173"
).split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_origin_regex=os.getenv("FRONTEND_ORIGIN_REGEX") or None,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

app.include_router(predict.router)
app.include_router(advice.router)
app.include_router(reports.router)


@app.get("/health", tags=["status"])
def health():
    engine = model_state.engine
    meta = engine.meta if engine else {}
    return {
        "status": "ok",
        "version": VERSION,
        "model_loaded": engine is not None,
        "model_error": model_state.error,
        "classes": len(meta.get("labels", [])) if engine else None,
        "backbone": "ResNet50",
        "runtime": "onnxruntime",
        "quantization": meta.get("quantization"),
        "parity": meta.get("parity"),
        "ai_advice_enabled": groq_client() is not None,
        "reports_stored": db.count_reports(),
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("backend.main:app", host="0.0.0.0", port=int(os.getenv("PORT", "8000")), reload=True)
