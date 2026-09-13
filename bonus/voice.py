"""
AgriSmart AI — vernacular voice assistant.

Speech-to-text with Groq Whisper, then a short spoken-style answer from the LLM,
grounded in the current diagnosis. Text-to-speech happens in the browser.
"""

from __future__ import annotations

import json
import os
from typing import Any

from bonus.assistant import MODEL_ID, groq_client, kb_advice
from bonus.languages import language_name, normalize_lang
from model.labels import format_label

WHISPER_MODEL = os.getenv("GROQ_WHISPER_MODEL", "whisper-large-v3-turbo")


class VoiceUnavailable(RuntimeError):
    """Raised when the Groq API key is missing or the service fails."""


def transcribe(audio: bytes, filename: str, lang: str) -> str:
    client = groq_client()
    if client is None:
        raise VoiceUnavailable("Voice assistant needs GROQ_API_KEY on the server.")
    try:
        result = client.audio.transcriptions.create(
            file=(filename or "question.webm", audio),
            model=WHISPER_MODEL,
            language=normalize_lang(lang),
            response_format="json",
            temperature=0.0,
        )
    except Exception as exc:
        raise VoiceUnavailable(f"Speech recognition failed: {type(exc).__name__}") from exc
    return (getattr(result, "text", "") or "").strip()


def answer_question(question: str, lang: str, context: dict[str, Any] | None = None) -> str:
    client = groq_client()
    if client is None:
        raise VoiceUnavailable("Voice assistant needs GROQ_API_KEY on the server.")

    context = context or {}
    label = context.get("label")
    grounding = ""
    if label:
        grounding = (
            f"The farmer's latest leaf scan shows: {format_label(label)} "
            f"(model confidence {context.get('confidence', 'unknown')}, "
            f"estimated affected leaf area {context.get('affected_area_pct', 'unknown')}%).\n"
            f"Verified reference notes: {json.dumps(kb_advice(label), ensure_ascii=False)}\n"
        )
    system = (
        "You are 'AgriSmart', a friendly Indian agricultural extension officer talking to a farmer on the phone. "
        f"Always reply in {language_name(lang)}. Answer in at most 4 short spoken sentences (under 80 words), "
        "no markdown, no bullet points, no emojis. Be practical and safe: never invent pesticide doses beyond the "
        "reference notes, and suggest contacting the local KVK or Kisan Call Centre (1800-180-1551) when unsure. "
        "If the question is not about farming, politely steer back to crops."
    )
    try:
        completion = client.chat.completions.create(
            model=MODEL_ID,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": f"{grounding}Farmer's question: {question}"},
            ],
            temperature=0.4,
            max_tokens=300,
        )
    except Exception as exc:
        raise VoiceUnavailable(f"Assistant failed: {type(exc).__name__}") from exc
    return (completion.choices[0].message.content or "").strip()
