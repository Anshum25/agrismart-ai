"""
AgriSmart AI — GenAI farmer assistant (Bonus D).

Generates plain-language treatment and prevention advice after CNN prediction,
using the Groq API (llama3-8b-8192).
"""

from __future__ import annotations

import os
import json
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

MODEL_ID = "llama3-8b-8192"


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
            f"You are an expert agricultural advisor helping smallholder farmers.\n"
            f"The crop appears healthy: {crop} — {disease}.\n"
            f"Provide concise, practical advice. Output ONLY a valid JSON object with the following exact keys:\n"
            f' - "advice": general ongoing care, nutrition, and early signs of problems (under 150 words)\n'
            f' - "irrigation_advice": practical watering advice for this crop\n'
            f' - "weather_risk": weather conditions to be careful about\n'
            f' - "sustainability": sustainable and organic practices to maintain crop health'
        )

    return (
        f"You are an expert agricultural advisor helping smallholder farmers.\n"
        f"Detected condition: {crop} — {disease}.\n"
        f"Provide concise, practical advice. Output ONLY a valid JSON object with the following exact keys:\n"
        f' - "advice": immediate treatment steps, preventive practices, and general crop care (under 150 words)\n'
        f' - "irrigation_advice": watering advice based on this condition\n'
        f' - "weather_risk": weather conditions that increase the risk or spread of this disease\n'
        f' - "sustainability": organic options and sustainable treatment practices'
    )


def _canned_advice(disease_class: str) -> dict:
    crop, disease = _parse_crop_and_disease(disease_class)
    if "healthy" in disease.lower():
        adv = (
            f"Your {crop} appears healthy. Continue regular watering, balanced fertilization, "
            f"and monitor leaves weekly for early spots or discoloration."
        )
    elif "blight" in disease.lower():
        adv = (
            f"For {disease} on {crop}: remove infected tissue, improve spacing for airflow, "
            f"avoid wetting foliage, and apply a copper-based fungicide if approved locally."
        )
    elif "rust" in disease.lower() or "mildew" in disease.lower():
        adv = (
            f"For {disease} on {crop}: prune affected areas, reduce humidity around plants, "
            f"and consider sulfur or fungicide treatment per local guidelines."
        )
    else:
        adv = (
            f"For {disease} on {crop}: isolate affected plants, remove damaged leaves, "
            f"sanitize tools, and seek region-specific treatment from an extension agent."
        )
        
    return {
        "advice": adv,
        "irrigation_advice": "Avoid overhead watering. Maintain proper drainage.",
        "weather_risk": "Monitor for high humidity and prolonged moisture which favor disease.",
        "sustainability": "Use crop rotation and organic compost to maintain soil health."
    }


def _append_error_note(advice_dict: dict, note: str) -> dict:
    new_dict = dict(advice_dict)
    new_dict["advice"] = new_dict.get("advice", "") + f"\n\n({note})"
    return new_dict


def get_care_advice(disease_class: str) -> dict:
    """
    Return plain-language care advice and additional insights for a predicted disease class.

    Args:
        disease_class: PlantVillage-style label, e.g. 'Tomato___Early_blight'

    Returns:
        Dictionary containing advice, irrigation_advice, weather_risk, sustainability.
    """
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key or api_key.strip() in ("", "your_key_here"):
        return _append_error_note(_canned_advice(disease_class), "Note: Set GROQ_API_KEY in .env for AI-generated advice.")

    try:
        from groq import Groq
        client = Groq(api_key=api_key)
        
        prompt = _build_prompt(disease_class)

        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            model=MODEL_ID,
            temperature=0.7,
            max_tokens=600,
            response_format={"type": "json_object"},
        )

        text = chat_completion.choices[0].message.content.strip()
        if text:
            parsed = json.loads(text)
            # fallback to canned if any key is missing
            canned = _canned_advice(disease_class)
            for k in ["advice", "irrigation_advice", "weather_risk", "sustainability"]:
                if k not in parsed or not parsed[k]:
                    parsed[k] = canned[k]
            return parsed
        return _canned_advice(disease_class)

    except ImportError:
        return _canned_advice(disease_class)
    except Exception as exc:
        err = str(exc).lower()
        if any(k in err for k in ("timeout", "rate", "429", "503", "401", "403", "quota", "key")):
            return _append_error_note(_canned_advice(disease_class), f"API unavailable: {type(exc).__name__}")
        return _canned_advice(disease_class)


if __name__ == "__main__":
    print(json.dumps(get_care_advice("Tomato___Early_blight"), indent=2))

