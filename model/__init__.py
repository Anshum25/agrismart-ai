"""AgriSmart AI — plant disease detection model package."""

from model.predict import load_model, predict, predict_from_array

__all__ = ["predict", "predict_from_array", "load_model"]
