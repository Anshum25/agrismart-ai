"""
AgriSmart AI — Smart irrigation logic (Bonus A).

Recommends watering schedules based on crop type, disease status, and soil moisture.
"""

from __future__ import annotations

# Base water need in mm/day by crop category (simplified lookup)
CROP_WATER_NEED = {
    "tomato": 6.0,
    "potato": 5.0,
    "corn": 7.0,
    "maize": 7.0,
    "grape": 4.5,
    "apple": 5.5,
    "pepper": 5.5,
    "peach": 5.0,
    "cherry": 4.5,
    "strawberry": 4.0,
    "blueberry": 4.0,
    "soybean": 5.5,
    "squash": 5.0,
    "orange": 5.0,
    "raspberry": 4.0,
}

# Diseases that worsen with overhead watering / excess moisture
MOISTURE_SENSITIVE = {
    "blight", "mildew", "mold", "rust", "spot", "scab", "rot",
}


def _normalize_crop(crop: str) -> str:
    return crop.lower().replace("_", " ").split("(")[0].strip()


def _is_diseased(disease_class: str) -> bool:
    if "___" in disease_class:
        _, disease = disease_class.split("___", 1)
        return "healthy" not in disease.lower()
    return "healthy" not in disease_class.lower()


def _disease_moisture_risk(disease_class: str) -> str:
    disease = disease_class.split("___")[-1].lower() if "___" in disease_class else disease_class.lower()
    if any(k in disease for k in MOISTURE_SENSITIVE):
        return "high"
    return "low"


def get_irrigation_advice(
    disease_class: str,
    soil_moisture_pct: float = 50.0,
    temperature_c: float = 28.0,
) -> dict:
    """
    Compute irrigation recommendation for a detected crop/disease.

    Args:
        disease_class: PlantVillage label, e.g. 'Tomato___Early_blight'
        soil_moisture_pct: Current soil moisture (0-100)
        temperature_c: Ambient temperature in Celsius

    Returns:
        dict with keys: recommendation, daily_water_mm, next_watering_hours, notes
    """
    crop_raw = disease_class.split("___")[0] if "___" in disease_class else disease_class
    crop_key = _normalize_crop(crop_raw)

    base_need = 5.0
    for key, need in CROP_WATER_NEED.items():
        if key in crop_key:
            base_need = need
            break

    # Adjust for temperature
    temp_factor = 1.0 + max(0, (temperature_c - 25)) * 0.03
    daily_water = round(base_need * temp_factor, 1)

    diseased = _is_diseased(disease_class)
    moisture_risk = _disease_moisture_risk(disease_class)

    if soil_moisture_pct >= 70:
        recommendation = "Hold irrigation — soil moisture is adequate."
        next_hours = 24
    elif soil_moisture_pct >= 45:
        recommendation = "Light irrigation recommended."
        next_hours = 12
    else:
        recommendation = "Irrigate soon — soil moisture is low."
        next_hours = 4

    notes = []
    if diseased and moisture_risk == "high":
        notes.append("Use drip irrigation at soil level; avoid wetting foliage.")
        notes.append("Reduce duration by ~20% until recovery signs appear.")
        daily_water = round(daily_water * 0.8, 1)
    elif not diseased:
        notes.append("Maintain consistent moisture to prevent stress-related disease.")

    if temperature_c > 35:
        notes.append("High heat — consider early morning or evening watering.")

    return {
        "recommendation": recommendation,
        "daily_water_mm": daily_water,
        "next_watering_hours": next_hours,
        "crop": crop_raw.replace("_", " "),
        "notes": notes,
    }


if __name__ == "__main__":
    result = get_irrigation_advice("Tomato___Early_blight", soil_moisture_pct=35)
    print(result)
