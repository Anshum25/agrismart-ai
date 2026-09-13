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
    lat = latitude if latitude is not None else float(os.getenv("DEFAULT_LAT", "28.6139"))
    lon = longitude if longitude is not None else float(os.getenv("DEFAULT_LON", "77.2090"))

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


# ---------------------------------------------------------------------------
# 7-day disease risk forecast
# ---------------------------------------------------------------------------

# Simplified epidemiological windows per disease group. temp = favourable mean
# temperature range (°C); wet_hours = hours with RH >= 90% (leaf-wetness proxy)
# needed for full moisture score. "dry" groups favour low humidity instead.
DISEASE_RULES: list[dict[str, Any]] = [
    {"group": "late_blight", "keywords": ["late_blight"], "temp": (10, 25), "wet_hours": 10,
     "note": "Cool, very humid weather lets late blight spread within days."},
    {"group": "rust", "keywords": ["rust"], "temp": (15, 25), "wet_hours": 6,
     "note": "Moderate temperatures with dew favour rust spores."},
    {"group": "powdery_mildew", "keywords": ["powdery_mildew"], "temp": (20, 30), "dry": "mildew",
     "note": "Warm days with humid nights but dry leaves favour powdery mildew."},
    {"group": "leaf_mold", "keywords": ["leaf_mold"], "temp": (20, 27), "wet_hours": 8,
     "note": "Humidity above 85% drives leaf mould."},
    {"group": "mites", "keywords": ["spider_mites"], "temp": (27, 40), "dry": "hot",
     "note": "Hot, dry weather makes mite populations explode."},
    {"group": "virus_vector", "keywords": ["virus", "greening", "haunglongbing"], "temp": (25, 35), "dry": "hot",
     "note": "Warm, dry weather increases whiteflies/psyllids that spread viruses."},
    {"group": "bacterial", "keywords": ["bacterial"], "temp": (24, 30), "wet_hours": 6, "rain_bonus": True,
     "note": "Warm rain and wind splash spread bacterial spots."},
    {"group": "fungal_leaf_spot", "keywords": [], "temp": (20, 30), "wet_hours": 6, "rain_bonus": True,
     "note": "Warm weather with long leaf wetness favours fungal leaf spots and blights."},
]


def rule_for(disease_class: str | None) -> dict[str, Any]:
    label = (disease_class or "").lower()
    for rule in DISEASE_RULES:
        if any(k in label for k in rule["keywords"]):
            return rule
    return DISEASE_RULES[-1]


def _temp_score(mean_temp: float, lo: float, hi: float) -> int:
    if lo <= mean_temp <= hi:
        return 35
    distance = lo - mean_temp if mean_temp < lo else mean_temp - hi
    return 15 if distance <= 3 else 0


def score_day(day: dict[str, float], rule: dict[str, Any], diseased: bool) -> dict[str, Any]:
    score = _temp_score(day["temp_mean"], *rule["temp"])
    factors: list[str] = []
    if score == 35:
        factors.append("favourable_temperature")

    dry = rule.get("dry")
    if dry == "mildew":
        if day["wet_hours"] <= 4 and 50 <= day["rh_mean"] <= 85:
            score += 40
            factors.append("dry_leaves_humid_air")
        elif day["rh_mean"] > 85:
            score += 15
    elif dry == "hot":
        if day["rh_mean"] < 55 and day["rain_mm"] < 1:
            score += 40
            factors.append("hot_dry")
        elif day["rh_mean"] < 70:
            score += 20
    else:
        needed = rule["wet_hours"]
        if day["wet_hours"] >= needed:
            score += 40
            factors.append("long_leaf_wetness")
        elif day["wet_hours"] >= needed / 2:
            score += 20
            factors.append("some_leaf_wetness")
        if rule.get("rain_bonus") and day["rain_mm"] >= 5:
            score += 15
            factors.append("rain_splash")

    if diseased:
        score += 10
        factors.append("active_infection")
    score = min(score, 100)
    level = "high" if score >= 65 else "moderate" if score >= 35 else "low"
    return {"risk_score": score, "risk_level": level, "factors": factors}


def summarize_hourly(hourly: dict[str, list], daily_dates: list[str]) -> dict[str, dict[str, float]]:
    per_day: dict[str, dict[str, list[float]]] = {d: {"rh": [], "t": []} for d in daily_dates}
    for ts, rh, t in zip(hourly.get("time", []), hourly.get("relative_humidity_2m", []),
                         hourly.get("temperature_2m", [])):
        day = ts[:10]
        if day in per_day and rh is not None and t is not None:
            per_day[day]["rh"].append(float(rh))
            per_day[day]["t"].append(float(t))
    out = {}
    for day, vals in per_day.items():
        rh, t = vals["rh"], vals["t"]
        out[day] = {
            "rh_mean": round(sum(rh) / len(rh), 1) if rh else 60.0,
            "wet_hours": sum(1 for v in rh if v >= 90),
            "temp_mean": round(sum(t) / len(t), 1) if t else 25.0,
        }
    return out


def build_forecast(payload: dict[str, Any], disease_class: str | None) -> dict[str, Any]:
    """Turn an Open-Meteo response into a scored 7-day forecast (pure function, testable)."""
    daily = payload.get("daily", {})
    dates: list[str] = daily.get("time", [])
    hourly = summarize_hourly(payload.get("hourly", {}), dates)
    rule = rule_for(disease_class)
    diseased = bool(disease_class) and "healthy" not in (disease_class or "").lower()

    days = []
    for i, date in enumerate(dates):
        day = {
            "date": date,
            "temp_max": daily.get("temperature_2m_max", [None] * len(dates))[i],
            "temp_min": daily.get("temperature_2m_min", [None] * len(dates))[i],
            "rain_mm": float(daily.get("precipitation_sum", [0] * len(dates))[i] or 0.0),
            "wind_max_kmh": float(daily.get("wind_speed_10m_max", [0] * len(dates))[i] or 0.0),
            **hourly.get(date, {"rh_mean": 60.0, "wet_hours": 0, "temp_mean": 25.0}),
        }
        day.update(score_day(day, rule, diseased))
        days.append(day)

    return {
        "disease_group": rule["group"],
        "note": rule["note"],
        "days": days,
        "best_spray_day": best_spray_day(days),
    }


def best_spray_day(days: list[dict[str, Any]]) -> dict[str, Any] | None:
    """Latest dry, calm day before the first high-risk day (or the calmest dry day)."""
    if not days:
        return None
    first_high = next((i for i, d in enumerate(days) if d["risk_level"] == "high"), None)

    def sprayable(d: dict[str, Any]) -> bool:
        return d["rain_mm"] < 1.0 and d["wind_max_kmh"] < 15.0

    if first_high is not None:
        before = [d for d in days[: first_high + 1] if sprayable(d)]
        if before:
            return {"date": before[-1]["date"], "reason": "before_high_risk"}
    dry_days = [d for d in days if sprayable(d)]
    if dry_days:
        pick = min(dry_days, key=lambda d: (d["wind_max_kmh"], d["rain_mm"]))
        return {"date": pick["date"], "reason": "dry_calm_day"}
    return None


def fetch_forecast_payload(lat: float, lon: float) -> dict[str, Any] | None:
    if requests is None:
        return None
    params = {
        "latitude": lat,
        "longitude": lon,
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,wind_speed_10m_max",
        "hourly": "relative_humidity_2m,temperature_2m",
        "forecast_days": 7,
        "timezone": "auto",
    }
    try:
        resp = requests.get(OPEN_METEO_URL, params=params, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except Exception:
        return None


def get_risk_forecast(lat: float, lon: float, disease_class: str | None = None) -> dict[str, Any] | None:
    payload = fetch_forecast_payload(lat, lon)
    if payload is None:
        return None
    return build_forecast(payload, disease_class)


if __name__ == "__main__":
    print(get_weather_risk("Tomato___Early_blight"))
