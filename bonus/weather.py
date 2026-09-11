"""
AgriSmart AI — Weather-based intelligence (Bonus B).

Assesses disease risk from weather conditions and suggests preventive actions.
Uses Open-Meteo free API when available; falls back to rule-based logic.
"""

from __future__ import annotations

import os
from typing import Any

try:
    import requests
except ImportError:
    requests = None  # type: ignore[assignment]

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"


def _rule_based_risk(
    humidity_pct: float,
    temperature_c: float,
    rainfall_mm: float,
    disease_class: str | None = None,
) -> dict[str, Any]:
    """Score disease risk from weather using agronomic heuristics."""
    score = 0
    factors: list[str] = []

    if humidity_pct > 80:
        score += 35
        factors.append("High humidity favours fungal spore germination.")
    elif humidity_pct > 65:
        score += 20
        factors.append("Moderate humidity — monitor for mildew and blight.")

    if 20 <= temperature_c <= 30:
        score += 15
        factors.append("Temperature range suitable for many foliar pathogens.")
    elif temperature_c > 32:
        score += 10
        factors.append("Heat stress may weaken plants, increasing susceptibility.")

    if rainfall_mm > 10:
        score += 30
        factors.append("Recent heavy rain increases leaf wetness duration.")
    elif rainfall_mm > 2:
        score += 15
        factors.append("Light rain — ensure good drainage.")

    if disease_class and "healthy" not in disease_class.lower():
        score += 20
        factors.append("Active disease detected — weather may accelerate spread.")

    score = min(score, 100)
    if score >= 70:
        level = "high"
        action = "Apply preventive fungicide if approved; improve airflow; delay overhead irrigation."
    elif score >= 40:
        level = "moderate"
        action = "Scout fields daily; remove infected debris; ensure proper spacing."
    else:
        level = "low"
        action = "Maintain standard preventive practices and monitoring."

    return {
        "risk_score": score,
        "risk_level": level,
        "risk_factors": factors,
        "recommended_action": action,
        "source": "rule_based",
    }


def _fetch_open_meteo(lat: float, lon: float) -> dict[str, float] | None:
    if requests is None:
        return None
    try:
        params = {
            "latitude": lat,
            "longitude": lon,
            "current": "temperature_2m,relative_humidity_2m,precipitation",
            "forecast_days": 1,
        }
        resp = requests.get(OPEN_METEO_URL, params=params, timeout=10)
        resp.raise_for_status()
        current = resp.json().get("current", {})
        return {
            "temperature_c": float(current.get("temperature_2m", 25)),
            "humidity_pct": float(current.get("relative_humidity_2m", 60)),
            "rainfall_mm": float(current.get("precipitation", 0)),
        }
    except Exception:
        return None


def get_weather_risk(
    disease_class: str | None = None,
    latitude: float | None = None,
    longitude: float | None = None,
    humidity_pct: float = 65.0,
    temperature_c: float = 28.0,
    rainfall_mm: float = 0.0,
) -> dict[str, Any]:
    """
    Assess weather-driven disease risk.

    Args:
        disease_class: Optional detected disease label for context
        latitude/longitude: If provided, fetch live weather from Open-Meteo
        humidity_pct, temperature_c, rainfall_mm: Manual overrides / fallback values

    Returns:
        dict with risk_score (0-100), risk_level, risk_factors, recommended_action
    """
    lat = latitude or float(os.getenv("DEFAULT_LAT", "28.6139"))
    lon = longitude or float(os.getenv("DEFAULT_LON", "77.2090"))

    live = _fetch_open_meteo(lat, lon)
    if live:
        humidity_pct = live["humidity_pct"]
        temperature_c = live["temperature_c"]
        rainfall_mm = live["rainfall_mm"]
        source_note = "open_meteo"
    else:
        source_note = "manual_or_fallback"

    result = _rule_based_risk(humidity_pct, temperature_c, rainfall_mm, disease_class)
    result["weather"] = {
        "humidity_pct": humidity_pct,
        "temperature_c": temperature_c,
        "rainfall_mm": rainfall_mm,
    }
    result["source"] = source_note
    return result


if __name__ == "__main__":
    print(get_weather_risk("Tomato___Early_blight"))
