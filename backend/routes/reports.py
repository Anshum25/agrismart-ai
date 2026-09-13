"""Anonymous outbreak reports, district map aggregation and nearby alerts."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel, Field

from backend import db
from backend.routes.advice import validate_label
from backend.state import limiter
from model.labels import extract_crop_type, is_healthy

router = APIRouter(tags=["outbreaks"])

MIN_REPORT_CONFIDENCE = 0.60


class ReportIn(BaseModel):
    label: str
    confidence: float = Field(ge=0, le=1)
    lat: float = Field(ge=-90, le=90)
    lon: float = Field(ge=-180, le=180)


@router.post("/reports", status_code=201)
@limiter.limit("20/hour")
def create_report(request: Request, body: ReportIn):
    label = validate_label(body.label)
    if body.confidence < MIN_REPORT_CONFIDENCE:
        raise HTTPException(status_code=422, detail="Only confident diagnoses can be shared to the outbreak map.")
    report_id = db.insert_report(
        label=label, crop=extract_crop_type(label), is_healthy=is_healthy(label),
        confidence=body.confidence, lat=body.lat, lon=body.lon,
    )
    return {"id": report_id, "stored_location": {"lat": db.round_to_grid(body.lat), "lon": db.round_to_grid(body.lon)}}


@router.get("/reports/aggregate")
@limiter.limit("60/minute")
def aggregate(request: Request, days: int = Query(14, ge=1, le=90), include_demo: bool = True,
              crop: str | None = Query(None, max_length=40)):
    cells = db.aggregate(days=days, include_demo=include_demo, crop=crop)
    return {"days": days, "grid_deg": db.GRID_DEG, "cells": cells,
            "has_simulated": any(c["demo_count"] for c in cells)}


@router.get("/alerts")
@limiter.limit("60/minute")
def alerts(request: Request, lat: float = Query(..., ge=-90, le=90), lon: float = Query(..., ge=-180, le=180),
           radius_km: float = Query(25, gt=0, le=200), days: int = Query(7, ge=1, le=60),
           include_demo: bool = True):
    return {
        "radius_km": radius_km,
        "days": days,
        "alerts": db.nearby_alerts(lat, lon, radius_km=radius_km, days=days, include_demo=include_demo),
    }
