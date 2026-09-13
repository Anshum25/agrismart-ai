"""Supported languages (codes are ISO-639-1, as accepted by Whisper)."""

from __future__ import annotations

LANGUAGES: dict[str, dict[str, str]] = {
    "en": {"name": "English", "native": "English", "bcp47": "en-IN"},
    "hi": {"name": "Hindi", "native": "हिन्दी", "bcp47": "hi-IN"},
    "mr": {"name": "Marathi", "native": "मराठी", "bcp47": "mr-IN"},
    "ta": {"name": "Tamil", "native": "தமிழ்", "bcp47": "ta-IN"},
    "te": {"name": "Telugu", "native": "తెలుగు", "bcp47": "te-IN"},
    "kn": {"name": "Kannada", "native": "ಕನ್ನಡ", "bcp47": "kn-IN"},
    "bn": {"name": "Bengali", "native": "বাংলা", "bcp47": "bn-IN"},
    "gu": {"name": "Gujarati", "native": "ગુજરાતી", "bcp47": "gu-IN"},
    "pa": {"name": "Punjabi", "native": "ਪੰਜਾਬੀ", "bcp47": "pa-IN"},
}


def normalize_lang(lang: str | None) -> str:
    code = (lang or "en").split("-")[0].lower()
    return code if code in LANGUAGES else "en"


def language_name(lang: str) -> str:
    info = LANGUAGES[normalize_lang(lang)]
    return f"{info['name']} ({info['native']})"
