"""
AgriSmart AI — GenAI farmer assistant.

Generates structured, plain-language treatment advice for a predicted disease in
the farmer's language using Groq (GPT-OSS 120B by default, GROQ_CHAT_MODEL to override). Falls back, in order, to:
  1. the pre-generated offline pack  frontend/public/offline/advice_<lang>.json
  2. the curated English knowledge base  bonus/disease_kb.json
so the app always returns real, disease-specific advice.
"""

from __future__ import annotations

import json
import os
from functools import lru_cache
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

from bonus.languages import language_name, normalize_lang
from model.labels import split_label

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

MODEL_ID = os.getenv("GROQ_CHAT_MODEL", "openai/gpt-oss-120b")
KB_PATH = Path(__file__).resolve().parent / "disease_kb.json"
OFFLINE_DIR = ROOT / "frontend" / "public" / "offline"


def chat_options() -> dict[str, Any]:
    """Extra parameters for reasoning models (their thinking tokens count toward max_tokens)."""
    return {"reasoning_effort": "low"} if "gpt-oss" in MODEL_ID else {}

LIST_KEYS = ("immediate_steps", "prevention", "organic_options", "chemical_options")
TEXT_KEYS = ("summary", "irrigation_tip", "weather_watch")
ADVICE_KEYS = ("pathogen",) + TEXT_KEYS + LIST_KEYS


@lru_cache(maxsize=1)
def load_kb() -> dict[str, dict[str, Any]]:
    data = json.loads(KB_PATH.read_text(encoding="utf-8"))
    data.pop("_meta", None)
    return data


@lru_cache(maxsize=16)
def _offline_pack(lang: str) -> dict[str, Any]:
    path = OFFLINE_DIR / f"advice_{lang}.json"
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8")).get("advice", {})
    except (OSError, ValueError):
        return {}


def groq_client():
    api_key = (os.getenv("GROQ_API_KEY") or "").strip()
    if not api_key or api_key == "your_key_here":
        return None
    try:
        from groq import Groq
    except ImportError:
        return None
    return Groq(api_key=api_key, timeout=20.0)


def kb_advice(disease_class: str) -> dict[str, Any]:
    entry = load_kb().get(disease_class)
    if entry is None:
        crop, disease = split_label(disease_class)
        entry = {
            "pathogen": "Unknown",
            "summary": f"{disease} detected on {crop}. Confirm with your local KVK or agriculture officer.",
            "immediate_steps": ["Isolate affected plants.", "Remove damaged leaves.", "Sanitize tools."],
            "prevention": ["Rotate crops.", "Improve airflow.", "Use disease-free planting material."],
            "organic_options": ["Neem oil 1500 ppm @ 3 ml/L."],
            "chemical_options": ["Consult a local expert before using any chemical."],
            "irrigation_tip": "Avoid overhead watering.",
            "weather_watch": "Humid, wet weather usually increases disease spread.",
        }
    return dict(entry)


def _clean(parsed: dict[str, Any], fallback: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key in TEXT_KEYS + ("pathogen",):
        value = parsed.get(key)
        out[key] = value.strip() if isinstance(value, str) and value.strip() else fallback.get(key, "")
    for key in LIST_KEYS:
        value = parsed.get(key)
        items = [str(v).strip() for v in value if str(v).strip()] if isinstance(value, list) else []
        out[key] = items[:6] or fallback.get(key, [])
    return out


def build_prompt(disease_class: str, lang: str) -> str:
    crop, disease = split_label(disease_class)
    kb = kb_advice(disease_class)
    healthy = "healthy" in disease.lower()
    situation = f"The {crop} crop looks healthy." if healthy else f"Detected condition: {disease} on {crop}."
    return (
        "You are an experienced Indian agricultural extension officer (KVK) advising a smallholder farmer.\n"
        f"{situation}\n"
        "Verified reference notes (keep your advice consistent with these; do not invent unsafe doses):\n"
        f"{json.dumps(kb, ensure_ascii=False)}\n\n"
        f"Write the answer in {language_name(lang)} using simple words a farmer understands. "
        "Keep product/active-ingredient names and doses in a form that can be read at an agri-input shop "
        "(you may keep them in English in brackets).\n"
        "Return ONLY a JSON object with these English keys:\n"
        '  "pathogen": short cause,\n'
        '  "summary": 2 short sentences,\n'
        '  "immediate_steps": 3-4 short action items,\n'
        '  "prevention": 3 short items,\n'
        '  "organic_options": 2-3 items with dose per litre,\n'
        '  "chemical_options": 2-3 items with dose per litre, ending with advice to follow the label,\n'
        '  "irrigation_tip": 1 sentence,\n'
        '  "weather_watch": 1 sentence.'
    )


def llm_advice(disease_class: str, lang: str, client=None) -> dict[str, Any] | None:
    """Call Groq; returns cleaned advice or None on any failure."""
    client = client or groq_client()
    if client is None:
        return None
    try:
        completion = client.chat.completions.create(
            model=MODEL_ID,
            messages=[{"role": "user", "content": build_prompt(disease_class, lang)}],
            temperature=0.3,
            max_tokens=2500,
            **chat_options(),
            response_format={"type": "json_object"},
        )
        parsed = json.loads(completion.choices[0].message.content or "{}")
    except Exception:  # network, auth, rate-limit, bad JSON
        return None
    return _clean(parsed, kb_advice(disease_class))


def get_care_advice(disease_class: str, lang: str = "en", use_llm: bool = True) -> dict[str, Any]:
    """
    Structured advice for a PlantVillage label in the requested language.

    Returns keys: pathogen, summary, immediate_steps, prevention, organic_options,
    chemical_options, irrigation_tip, weather_watch, source, lang.
    """
    lang = normalize_lang(lang)
    if use_llm:
        advice = llm_advice(disease_class, lang)
        if advice:
            return {**advice, "source": "ai", "lang": lang}

    offline = _offline_pack(lang).get(disease_class)
    if offline:
        return {**_clean(offline, kb_advice(disease_class)), "source": "offline", "lang": lang}

    return {**kb_advice(disease_class), "source": "knowledge_base", "lang": "en"}


if __name__ == "__main__":
    print(json.dumps(get_care_advice("Tomato___Early_blight", "hi"), indent=2, ensure_ascii=False))
