import io

import numpy as np
from PIL import Image

from backend.tests.conftest import leaf_image


def _png(arr: np.ndarray) -> bytes:
    buf = io.BytesIO()
    Image.fromarray(arr).save(buf, format="PNG")
    return buf.getvalue()


def test_health_reports_model_loaded(client):
    body = client.get("/health").json()
    assert body["model_loaded"] is True
    assert body["classes"] == 38
    assert body["ai_advice_enabled"] is False


def test_predict_leaf_returns_contract(client):
    r = client.post("/predict", files={"file": ("leaf.png", _png(leaf_image()), "image/png")})
    assert r.status_code == 200
    body = r.json()
    for key in ("status", "label", "pretty_label", "crop", "confidence", "top3", "severity",
                "affected_area_pct", "gradcam_image", "inference"):
        assert key in body
    assert body["inference"] == "server"


def test_predict_rejects_non_leaf_and_bad_uploads(client):
    solid = np.full((300, 300, 3), 200, dtype=np.uint8)
    assert client.post("/predict", files={"file": ("x.png", _png(solid), "image/png")}).json()["status"] == "rejected"
    assert client.post("/predict", files={"file": ("x.txt", b"hello", "text/plain")}).status_code == 422
    assert client.post("/predict", files={"file": ("x.png", b"notanimage", "image/png")}).status_code == 422
    big = b"0" * (5 * 1024 * 1024 + 10)
    assert client.post("/predict", files={"file": ("x.png", big, "image/png")}).status_code == 413


def test_predict_returns_503_without_model(client):
    from backend.state import model_state

    engine, model_state.engine = model_state.engine, None
    try:
        r = client.post("/predict", files={"file": ("leaf.png", _png(leaf_image()), "image/png")})
        assert r.status_code == 503
    finally:
        model_state.engine = engine


def test_advice_falls_back_to_knowledge_base_without_key(client):
    r = client.post("/advice", json={"label": "Potato___Late_blight", "lang": "hi"})
    assert r.status_code == 200
    body = r.json()
    assert body["source"] in {"knowledge_base", "offline"}
    assert body["immediate_steps"] and body["chemical_options"]
    assert client.post("/advice", json={"label": "Not_a_label", "lang": "en"}).status_code == 422


def test_voice_without_key_is_honest_503(client):
    r = client.post("/voice/ask", data={"question": "What should I spray?", "lang": "hi",
                                        "label": "Tomato___Early_blight"})
    assert r.status_code == 503


def test_insights_combines_bonus_modules(client, monkeypatch):
    from bonus import weather

    monkeypatch.setattr(weather, "_fetch_open_meteo", lambda lat, lon: {
        "temperature_c": 30.0, "humidity_pct": 88.0, "rainfall_mm": 6.0})
    body = client.get("/insights?label=Tomato___Early_blight&lat=13.1&lon=78.1").json()
    assert body["weather_risk"]["risk_level"] in {"moderate", "high"}
    assert body["irrigation"]["soil_moisture_assumed"] is True
    assert body["sustainability"]["grade"] in {"A", "B", "C", "D", "F"}


def test_reports_roundtrip_and_alerts(client):
    r = client.post("/reports", json={"label": "Tomato___Late_blight", "confidence": 0.93,
                                      "lat": 13.1432, "lon": 78.1311})
    assert r.status_code == 201
    assert r.json()["stored_location"] == {"lat": 13.15, "lon": 78.15}  # 0.05° privacy grid

    low = client.post("/reports", json={"label": "Tomato___Late_blight", "confidence": 0.3, "lat": 13.1, "lon": 78.1})
    assert low.status_code == 422

    cells = client.get("/reports/aggregate?days=7").json()["cells"]
    assert cells[0]["label"] == "Tomato___Late_blight" and cells[0]["simulated"] is False

    alerts = client.get("/alerts?lat=13.2&lon=78.2&radius_km=25").json()["alerts"]
    assert alerts and alerts[0]["count"] == 1
    assert client.get("/alerts?lat=28.6&lon=77.2&radius_km=25").json()["alerts"] == []


def test_demo_seed_is_flagged_simulated(client):
    from backend import db

    db.seed_demo_reports(n=20)
    body = client.get("/reports/aggregate?days=30").json()
    assert body["has_simulated"] is True
    assert all(c["simulated"] for c in body["cells"])
    assert client.get("/reports/aggregate?days=30&include_demo=false").json()["cells"] == []


def test_forecast_rules_with_fixture(monkeypatch, client):
    from bonus import weather

    dates = [f"2026-09-{d:02d}" for d in range(14, 21)]
    hourly_time, rh, temp = [], [], []
    for i, date in enumerate(dates):
        for hour in range(24):
            hourly_time.append(f"{date}T{hour:02d}:00")
            rh.append(97 if i == 3 else 60)       # day 4: cool and wet all day
            temp.append(18 if i == 3 else 32)
    payload = {
        "daily": {"time": dates, "temperature_2m_max": [33] * 7, "temperature_2m_min": [20] * 7,
                  "precipitation_sum": [0, 0, 0, 12, 0, 0, 0], "wind_speed_10m_max": [8, 20, 5, 10, 5, 5, 5]},
        "hourly": {"time": hourly_time, "relative_humidity_2m": rh, "temperature_2m": temp},
    }
    monkeypatch.setattr(weather, "fetch_forecast_payload", lambda lat, lon: payload)
    body = client.get("/forecast?lat=27.18&lon=78.01&label=Potato___Late_blight").json()
    assert body["disease_group"] == "late_blight"
    levels = [d["risk_level"] for d in body["days"]]
    assert levels[3] == "high" and levels[0] != "high"
    assert body["best_spray_day"] == {"date": dates[2], "reason": "before_high_risk"}
