"""
AgriSmart AI — GenAI farmer assistant (Bonus D).

Generates plain-language treatment and prevention advice after CNN prediction,
using the Hugging Face Inference API (Mistral-7B-Instruct).
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

FALLBACK_MESSAGE = (
    "Care advice is temporarily unavailable. General tips: remove affected leaves, "
    "avoid overhead watering, improve air circulation, and consult your local "
    "agricultural extension office for disease-specific treatment."
)

MODEL_ID = "mistralai/Mistral-7B-Instruct-v0.2"
REQUEST_TIMEOUT = 30


def _parse_crop_and_disease(disease_class: str) -> tuple[str, str]:
    if "___" in disease_class:
        crop, disease = disease_class.split("___", 1)
        return crop.replace("_", " "), disease.replace("_", " ")
    return "plant", disease_class.replace("_", " ")


def _build_prompt(disease_class: str) -> str:
    crop, disease = _parse_crop_and_disease(disease_class)
    is_healthy = "healthy" in disease.lower()

    if is_healthy:
        return (
            f"<s>[INST] You are an expert agricultural advisor helping smallholder farmers.\n"
            f"The crop appears healthy: {crop} — {disease}.\n"
            f"Provide concise, practical advice covering:\n"
            f"1) Ongoing care and nutrition\n"
            f"2) Preventive practices to avoid common diseases\n"
            f"3) Signs to watch for that indicate emerging problems\n"
            f"Keep the response under 200 words, use simple language, no markdown. [/INST]"
        )

    return (
        f"<s>[INST] You are an expert agricultural advisor helping smallholder farmers.\n"
        f"Detected condition: {crop} — {disease}.\n"
        f"Provide concise, practical advice covering:\n"
        f"1) Immediate treatment steps (organic and chemical options if applicable)\n"
        f"2) Preventive practices to stop spread and recurrence\n"
        f"3) General crop care tips for recovery\n"
        f"Keep the response under 250 words, use simple language, no markdown. [/INST]"
    )


def _canned_advice(disease_class: str) -> str:
    crop, disease = _parse_crop_and_disease(disease_class)
    if "healthy" in disease.lower():
        return (
            f"Your {crop} appears healthy. Continue regular watering, balanced fertilization, "
            f"and monitor leaves weekly for early spots or discoloration."
        )
    if "blight" in disease.lower():
        return (
            f"For {disease} on {crop}: remove infected tissue, improve spacing for airflow, "
            f"avoid wetting foliage, and apply a copper-based fungicide if approved locally."
        )
    if "rust" in disease.lower() or "mildew" in disease.lower():
        return (
            f"For {disease} on {crop}: prune affected areas, reduce humidity around plants, "
            f"and consider sulfur or fungicide treatment per local guidelines."
        )
    return (
        f"For {disease} on {crop}: isolate affected plants, remove damaged leaves, "
        f"sanitize tools, and seek region-specific treatment from an extension agent."
    )


def get_care_advice(disease_class: str) -> str:
    """
    Return plain-language care advice for a predicted disease class.

    Args:
        disease_class: PlantVillage-style label, e.g. 'Tomato___Early_blight'

    Returns:
        Advice string (from LLM or fallback).
    """
    api_key = os.getenv("HUGGINGFACE_TOKEN")
    if not api_key:
        return (
            _canned_advice(disease_class)
            + "\n\n(Note: Set HUGGINGFACE_TOKEN in .env for AI-generated advice.)"
        )

    try:
        from huggingface_hub import InferenceClient

        client = InferenceClient(provider="featherless-ai", api_key=api_key)
        prompt = _build_prompt(disease_class)
        response = client.text_generation(
            prompt,
            model=MODEL_ID,
            max_new_tokens=350,
            temperature=0.4,
            return_full_text=False,
        )
        text = response.strip() if isinstance(response, str) else str(response).strip()
        return text if text else _canned_advice(disease_class)

    except ImportError:
        return _canned_advice(disease_class)
    except Exception as exc:
        err = str(exc).lower()
        if any(k in err for k in ("timeout", "rate", "429", "503", "401", "403")):
            return _canned_advice(disease_class) + f"\n\n(API unavailable: {type(exc).__name__})"
        return _canned_advice(disease_class)


if __name__ == "__main__":
    print(get_care_advice("Tomato___Early_blight"))
