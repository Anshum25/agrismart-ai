"""AgriSmart AI — plant disease detection model package.

`model.runtime` (ONNX, used by the API) must stay importable without TensorFlow,
so the TensorFlow-based helpers are loaded lazily.
"""

__all__ = ["predict", "predict_from_array", "load_model"]


def __getattr__(name):
    if name in __all__:
        from model import predict as _predict

        return getattr(_predict, name)
    raise AttributeError(f"module 'model' has no attribute {name!r}")
