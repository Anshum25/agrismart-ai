"""
AgriSmart AI — Sustainability score (Bonus C).

Estimates environmental impact of recommended crop management practices.
"""

from __future__ import annotations

from typing import Any

# Impact weights (lower is more sustainable)
TREATMENT_IMPACT = {
    "organic": 0.1,
    "cultural": 0.15,
    "biological": 0.2,
    "chemical_low": 0.45,
    "chemical_high": 0.7,
}

DISEASE_TREATMENT_MAP = {
    "healthy": ["cultural"],
    "blight": ["cultural", "organic", "chemical_low"],
    "rust": ["cultural", "organic"],
    "mildew": ["cultural", "organic", "chemical_low"],
    "spot": ["cultural", "biological"],
    "mold": ["cultural", "organic"],
    "virus": ["cultural"],
    "mite": ["biological", "organic"],
    "scorch": ["cultural", "organic"],
    "rot": ["cultural", "organic"],
}


def _detect_disease_keywords(disease_class: str) -> list[str]:
    disease = disease_class.split("___")[-1].lower() if "___" in disease_class else disease_class.lower()
    matched = []
    for keyword, treatments in DISEASE_TREATMENT_MAP.items():
        if keyword in disease:
            matched.extend(treatments)
    return matched or ["cultural", "organic"]


def compute_sustainability_score(
    disease_class: str,
    uses_chemical: bool = False,
    water_efficiency: float = 0.7,
    crop_rotation: bool = True,
) -> dict[str, Any]:
    """
    Compute a sustainability score (0-100, higher is better).

    Args:
        disease_class: PlantVillage label
        uses_chemical: Whether chemical pesticides are applied
        water_efficiency: Drip/smart irrigation factor (0-1)
        crop_rotation: Whether crop rotation is practiced

    Returns:
        dict with score, grade, breakdown, and improvement tips
    """
    base_score = 80.0
    breakdown: dict[str, float] = {"base": base_score}
    tips: list[str] = []

    if "healthy" in disease_class.lower():
        breakdown["disease_impact"] = 10.0
        tips.append("Maintain IPM scouting to keep plants healthy.")
    else:
        breakdown["disease_impact"] = -15.0
        tips.append("Prioritize cultural controls before chemical treatments.")

    if uses_chemical:
        breakdown["chemical_penalty"] = -20.0
        tips.append("Switch to neem oil or copper sprays where effective to reduce chemical load.")
    else:
        breakdown["chemical_bonus"] = 10.0

    breakdown["water"] = round((water_efficiency - 0.5) * 20, 1)
    if water_efficiency < 0.6:
        tips.append("Install drip irrigation to improve water efficiency.")

    breakdown["rotation"] = 5.0 if crop_rotation else -10.0
    if not crop_rotation:
        tips.append("Adopt crop rotation to reduce soil-borne disease pressure.")

    treatments = _detect_disease_keywords(disease_class)
    min_impact = min(TREATMENT_IMPACT.get(t, 0.3) for t in treatments)
    breakdown["treatment_path"] = round((1 - min_impact) * 10, 1)

    score = max(0, min(100, sum(breakdown.values())))

    if score >= 80:
        grade = "A"
    elif score >= 65:
        grade = "B"
    elif score >= 50:
        grade = "C"
    elif score >= 35:
        grade = "D"
    else:
        grade = "F"

    return {
        "score": round(score, 1),
        "grade": grade,
        "breakdown": breakdown,
        "recommended_treatments": list(dict.fromkeys(treatments)),
        "improvement_tips": tips,
    }


if __name__ == "__main__":
    print(compute_sustainability_score("Tomato___Early_blight", uses_chemical=False))
