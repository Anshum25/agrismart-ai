"""AI agronomist advice, farm insights, 7-day risk forecast and voice assistant."""

from __future__ import annotations

import time
from typing import Any

from fastapi import APIRouter, File, Form, HTTPException, Query, Request, UploadFile
from pydantic import BaseModel

from backend import db
from backend.routes.predict import read_upload
from backend.state import limiter
from bonus.assistant import get_care_advice
from bonus.irrigation import get_irrigation_advice
from bonus.languages import LANGUAGES, normalize_lang
from bonus.sustainability import compute_sustainability_score
from bonus.voice import VoiceUnavailable, answer_question, transcribe
from bonus.weather import get_risk_forecast, get_weather_risk
from model.config import DEFAULT_CLASS_LABELS

router = APIRouter(tags=["advisory"])

KNOWN_LABELS = set(DEFAULT_CLASS_LABELS)
MAX_AUDIO_BYTES = 5 * 1024 * 1024


def validate_label(label: str | None, required: bool = True) -> str | None:
    if label is None and not required:
        return None
    if label not in KNOWN_LABELS:
        raise HTTPException(status_code=422, detail="Unknown disease label.")
    return label


# ---------------------------------------------------------------------------
# Advice
# ---------------------------------------------------------------------------

class AdviceRequest(BaseModel):
    label: str
    lang: str = "en"


@router.get("/languages")
def languages():
    return [{"code": code, **info} for code, info in LANGUAGES.items()]


@router.post("/advice")
@limiter.limit("30/minute")
def advice(request: Request, body: AdviceRequest):
    label = validate_label(body.label)
    lang = normalize_lang(body.lang)
    cached = db.get_cached_advice(label, lang)
    if cached:
        return {**cached, "cached": True}
    result = get_care_advice(label, lang)
    if result["source"] == "ai":
        db.set_cached_advice(label, lang, result)
    return result


# ---------------------------------------------------------------------------
# Insights (current weather risk + irrigation + sustainability)
# ---------------------------------------------------------------------------

@router.get("/insights")
@limiter.limit("30/minute")
def insights(request: Request, label: str, lat: float | None = Query(None, ge=-90, le=90),
             lon: float | None = Query(None, ge=-180, le=180),
             soil_moisture: float | None = Query(None, ge=0, le=100)):
    label = validate_label(label)
    weather = get_weather_risk(label, latitude=lat, longitude=lon)
    temp = weather["weather"]["temperature_c"]
    irrigation = get_irrigation_advice(
        label, soil_moisture_pct=soil_moisture if soil_moisture is not None else 50.0, temperature_c=temp,
    )
    irrigation["soil_moisture_assumed"] = soil_moisture is None
    if weather["weather"]["rainfall_mm"] >= 5:
        irrigation["notes"].append("Recent rain - skip the next irrigation if the soil is still moist.")
    return {
        "location": {"lat": lat, "lon": lon, "is_default": lat is None or lon is None},
        "weather_risk": weather,
        "irrigation": irrigation,
        "sustainability": compute_sustainability_score(label),
    }


# ---------------------------------------------------------------------------
# 7-day disease risk forecast (cached per ~11 km cell for 30 minutes)
# ---------------------------------------------------------------------------

_FORECAST_CACHE: dict[tuple, tuple[float, dict[str, Any]]] = {}
FORECAST_TTL_S = 30 * 60


@router.get("/forecast")
@limiter.limit("30/minute")
def forecast(request: Request, lat: float = Query(..., ge=-90, le=90), lon: float = Query(..., ge=-180, le=180),
             label: str | None = None):
    label = validate_label(label, required=False)
    key = (round(lat, 1), round(lon, 1), label)
    hit = _FORECAST_CACHE.get(key)
    if hit and time.time() - hit[0] < FORECAST_TTL_S:
        return hit[1]
    result = get_risk_forecast(lat, lon, label)
    if result is None:
        raise HTTPException(status_code=503, detail="Weather forecast service is unavailable. Try again later.")
    _FORECAST_CACHE[key] = (time.time(), result)
    return result


# ---------------------------------------------------------------------------
# Voice / text question to the AI agronomist
# ---------------------------------------------------------------------------

@router.post("/voice/ask")
@limiter.limit("10/minute")
async def voice_ask(
    request: Request,
    audio: UploadFile | None = File(None),
    question: str | None = Form(None, max_length=500),
    lang: str = Form("en"),
    label: str | None = Form(None),
    confidence: float | None = Form(None),
    affected_area_pct: float | None = Form(None),
):
    from fastapi.concurrency import run_in_threadpool

    lang = normalize_lang(lang)
    if label is not None:
        validate_label(label)
    try:
        if audio is not None:
            data = await read_upload(audio, MAX_AUDIO_BYTES)
            question = await run_in_threadpool(transcribe, data, audio.filename or "question.webm", lang)
        if not question or not question.strip():
            raise HTTPException(status_code=422, detail="Could not hear a question. Please try again.")
        context = {"label": label, "confidence": confidence, "affected_area_pct": affected_area_pct}
        answer = await run_in_threadpool(answer_question, question.strip(), lang, context)
    except VoiceUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return {"transcript": question.strip(), "answer": answer, "lang": lang}
