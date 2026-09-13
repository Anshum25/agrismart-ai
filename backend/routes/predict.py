"""Leaf image diagnosis endpoints."""

from __future__ import annotations

import io
import os

import numpy as np
from fastapi import APIRouter, File, HTTPException, Query, Request, UploadFile
from fastapi.concurrency import run_in_threadpool
from PIL import Image, ImageOps

from backend.state import limiter, model_state

router = APIRouter(tags=["diagnosis"])

MAX_UPLOAD_BYTES = int(float(os.getenv("MAX_UPLOAD_MB", "5")) * 1024 * 1024)
MAX_DECODE_SIDE = 1600
Image.MAX_IMAGE_PIXELS = 40_000_000


async def read_upload(file: UploadFile, max_bytes: int = MAX_UPLOAD_BYTES) -> bytes:
    data = await file.read(max_bytes + 1)
    if len(data) > max_bytes:
        raise HTTPException(status_code=413, detail=f"File too large (max {max_bytes // (1024 * 1024)} MB).")
    if not data:
        raise HTTPException(status_code=422, detail="Empty upload.")
    return data


def decode_image(data: bytes) -> np.ndarray:
    try:
        img = Image.open(io.BytesIO(data))
        img = ImageOps.exif_transpose(img)  # phone photos carry rotation in EXIF
        img = img.convert("RGB")
    except Exception as exc:  # includes DecompressionBombError
        raise HTTPException(status_code=422, detail=f"Cannot decode image: {type(exc).__name__}") from exc
    img.thumbnail((MAX_DECODE_SIDE, MAX_DECODE_SIDE))
    return np.asarray(img)


def require_engine():
    if model_state.engine is None:
        raise HTTPException(
            status_code=503,
            detail="The diagnosis model is not loaded on the server"
                   + (f": {model_state.error}" if model_state.error else "."),
        )
    return model_state.engine


async def _diagnose(file: UploadFile, gradcam: bool) -> dict:
    if not (file.content_type or "").startswith("image/"):
        raise HTTPException(status_code=422, detail="Only image files are accepted.")
    engine = require_engine()
    rgb = decode_image(await read_upload(file))
    return await run_in_threadpool(engine.diagnose, rgb, gradcam)


@router.post("/predict")
@limiter.limit("30/minute")
async def predict(request: Request, file: UploadFile = File(...),
                  gradcam: bool = Query(True, description="Include a Grad-CAM overlay image")):
    """Diagnose a leaf photo. Returns status ok | uncertain | rejected (see README)."""
    return await _diagnose(file, gradcam)


@router.post("/predict/gradcam", include_in_schema=False)
@limiter.limit("30/minute")
async def predict_gradcam(request: Request, file: UploadFile = File(...)):
    """Backwards-compatible alias for /predict?gradcam=true."""
    return await _diagnose(file, True)
