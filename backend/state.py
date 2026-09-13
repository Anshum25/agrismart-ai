"""Process-wide state shared by the API routes."""

from __future__ import annotations

from typing import Any

from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)


class ModelState:
    engine: Any = None
    error: str | None = None


model_state = ModelState()
