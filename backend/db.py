"""
SQLite storage for anonymous outbreak reports and the AI advice cache.

Locations are rounded to a 0.05° grid (~5 km) before storage, so no exact farm
location is ever saved. On Render's free tier the disk is ephemeral; set
SEED_DEMO_DATA=1 to repopulate clearly-labelled simulated reports after a deploy.
"""

from __future__ import annotations

import json
import math
import os
import random
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterator

ROOT = Path(__file__).resolve().parent.parent
GRID_DEG = 0.05

SCHEMA = """
CREATE TABLE IF NOT EXISTS reports (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at  TEXT    NOT NULL,
    label       TEXT    NOT NULL,
    crop        TEXT    NOT NULL,
    is_healthy  INTEGER NOT NULL,
    confidence  REAL    NOT NULL,
    lat         REAL    NOT NULL,
    lon         REAL    NOT NULL,
    source      TEXT    NOT NULL DEFAULT 'user'
);
CREATE INDEX IF NOT EXISTS idx_reports_created ON reports(created_at);
CREATE INDEX IF NOT EXISTS idx_reports_geo ON reports(lat, lon);

CREATE TABLE IF NOT EXISTS advice_cache (
    label       TEXT NOT NULL,
    lang        TEXT NOT NULL,
    payload     TEXT NOT NULL,
    created_at  TEXT NOT NULL,
    PRIMARY KEY (label, lang)
);
"""


def db_path() -> Path:
    raw = os.getenv("DB_PATH", "backend/data/agrismart.db")
    path = Path(raw)
    return path if path.is_absolute() else ROOT / path


@contextmanager
def connect() -> Iterator[sqlite3.Connection]:
    path = db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path, timeout=10)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init() -> None:
    with connect() as conn:
        conn.executescript(SCHEMA)


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def round_to_grid(value: float) -> float:
    return round(round(value / GRID_DEG) * GRID_DEG, 4)


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


# ---------------------------------------------------------------------------
# Reports
# ---------------------------------------------------------------------------

def insert_report(label: str, crop: str, is_healthy: bool, confidence: float,
                  lat: float, lon: float, source: str = "user", created_at: str | None = None) -> int:
    with connect() as conn:
        cur = conn.execute(
            "INSERT INTO reports (created_at, label, crop, is_healthy, confidence, lat, lon, source) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (created_at or now_iso(), label, crop, int(is_healthy), round(confidence, 4),
             round_to_grid(lat), round_to_grid(lon), source),
        )
        return int(cur.lastrowid)


def _since(days: int) -> str:
    return (datetime.now(timezone.utc) - timedelta(days=days)).isoformat(timespec="seconds")


def aggregate(days: int = 14, include_demo: bool = True, crop: str | None = None) -> list[dict[str, Any]]:
    sql = (
        "SELECT lat, lon, label, crop, is_healthy, COUNT(*) AS count, MAX(created_at) AS last_seen, "
        "SUM(CASE WHEN source = 'demo_seed' THEN 1 ELSE 0 END) AS demo_count "
        "FROM reports WHERE created_at >= ?"
    )
    params: list[Any] = [_since(days)]
    if not include_demo:
        sql += " AND source != 'demo_seed'"
    if crop:
        sql += " AND lower(crop) = lower(?)"
        params.append(crop)
    sql += " GROUP BY lat, lon, label ORDER BY count DESC"
    with connect() as conn:
        rows = conn.execute(sql, params).fetchall()
    return [
        {**dict(r), "is_healthy": bool(r["is_healthy"]), "simulated": r["demo_count"] == r["count"]}
        for r in rows
    ]


def nearby_alerts(lat: float, lon: float, radius_km: float = 25, days: int = 7,
                  include_demo: bool = True) -> list[dict[str, Any]]:
    dlat = radius_km / 111.0
    dlon = radius_km / (111.0 * max(math.cos(math.radians(lat)), 0.01))
    sql = (
        "SELECT lat, lon, label, crop, created_at, source FROM reports "
        "WHERE is_healthy = 0 AND created_at >= ? AND lat BETWEEN ? AND ? AND lon BETWEEN ? AND ?"
    )
    params: list[Any] = [_since(days), lat - dlat, lat + dlat, lon - dlon, lon + dlon]
    if not include_demo:
        sql += " AND source != 'demo_seed'"
    with connect() as conn:
        rows = conn.execute(sql, params).fetchall()

    by_label: dict[str, dict[str, Any]] = {}
    for r in rows:
        dist = haversine_km(lat, lon, r["lat"], r["lon"])
        if dist > radius_km:
            continue
        entry = by_label.setdefault(r["label"], {
            "label": r["label"], "crop": r["crop"], "count": 0,
            "nearest_km": dist, "last_seen": r["created_at"], "simulated": True,
        })
        entry["count"] += 1
        entry["nearest_km"] = round(min(entry["nearest_km"], dist), 1)
        entry["last_seen"] = max(entry["last_seen"], r["created_at"])
        entry["simulated"] = entry["simulated"] and r["source"] == "demo_seed"
    return sorted(by_label.values(), key=lambda e: -e["count"])


def count_reports() -> int:
    with connect() as conn:
        return int(conn.execute("SELECT COUNT(*) FROM reports").fetchone()[0])


# Simulated hotspots in real growing regions (for demos only; tagged demo_seed).
DEMO_HOTSPOTS = [
    ("Kolar, KA", 13.14, 78.13, ["Tomato___Early_blight", "Tomato___Tomato_Yellow_Leaf_Curl_Virus", "Tomato___healthy"]),
    ("Nashik, MH", 20.00, 73.79, ["Grape___Black_rot", "Grape___Leaf_blight_(Isariopsis_Leaf_Spot)", "Tomato___Late_blight"]),
    ("Sangli, MH", 16.85, 74.58, ["Grape___Esca_(Black_Measles)", "Grape___healthy"]),
    ("Agra, UP", 27.18, 78.01, ["Potato___Late_blight", "Potato___Early_blight", "Potato___healthy"]),
    ("Hooghly, WB", 22.90, 88.39, ["Potato___Late_blight", "Potato___healthy"]),
    ("Jalandhar, PB", 31.33, 75.58, ["Potato___Early_blight", "Corn_(maize)___Common_rust_"]),
    ("Shimla, HP", 31.10, 77.17, ["Apple___Apple_scab", "Apple___Cedar_apple_rust", "Apple___healthy"]),
    ("Srinagar, JK", 34.08, 74.80, ["Apple___Apple_scab", "Apple___Black_rot"]),
    ("Chhindwara, MP", 22.06, 78.94, ["Corn_(maize)___Northern_Leaf_Blight", "Corn_(maize)___Cercospora_leaf_spot Gray_leaf_spot"]),
    ("Davangere, KA", 14.46, 75.92, ["Corn_(maize)___Common_rust_", "Corn_(maize)___healthy"]),
    ("Nagpur, MH", 21.15, 79.09, ["Orange___Haunglongbing_(Citrus_greening)"]),
    ("Madanapalle, AP", 13.55, 78.50, ["Tomato___Bacterial_spot", "Tomato___Septoria_leaf_spot"]),
]


def seed_demo_reports(n: int = 140, seed: int = 7) -> int:
    from model.labels import extract_crop_type, is_healthy

    rng = random.Random(seed)
    now = datetime.now(timezone.utc)
    for _ in range(n):
        _name, lat, lon, labels = rng.choice(DEMO_HOTSPOTS)
        label = rng.choice(labels)
        created = now - timedelta(days=rng.uniform(0, 20), hours=rng.uniform(0, 23))
        insert_report(
            label=label, crop=extract_crop_type(label), is_healthy=is_healthy(label),
            confidence=rng.uniform(0.75, 0.99),
            lat=lat + rng.gauss(0, 0.15), lon=lon + rng.gauss(0, 0.15),
            source="demo_seed", created_at=created.isoformat(timespec="seconds"),
        )
    return n


# ---------------------------------------------------------------------------
# Advice cache
# ---------------------------------------------------------------------------

def get_cached_advice(label: str, lang: str, max_age_days: int = 30) -> dict[str, Any] | None:
    with connect() as conn:
        row = conn.execute(
            "SELECT payload FROM advice_cache WHERE label = ? AND lang = ? AND created_at >= ?",
            (label, lang, _since(max_age_days)),
        ).fetchone()
    return json.loads(row["payload"]) if row else None


def set_cached_advice(label: str, lang: str, payload: dict[str, Any]) -> None:
    with connect() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO advice_cache (label, lang, payload, created_at) VALUES (?, ?, ?, ?)",
            (label, lang, json.dumps(payload, ensure_ascii=False), now_iso()),
        )
