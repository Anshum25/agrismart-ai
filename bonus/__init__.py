"""Bonus modules for AgriSmart AI."""

from bonus.assistant import get_care_advice
from bonus.irrigation import get_irrigation_advice
from bonus.sustainability import compute_sustainability_score
from bonus.weather import get_weather_risk

__all__ = [
    "get_care_advice",
    "get_irrigation_advice",
    "get_weather_risk",
    "compute_sustainability_score",
]
