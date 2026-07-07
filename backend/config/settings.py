"""Centralized settings loaded from environment variables.

This module is the single source of truth for runtime configuration.
All other modules read from here — never call os.getenv() directly
outside this file.

Usage:
    from backend.config.settings import settings
    print(settings.roboflow_api_key)
    print(settings.openrouter_model)

If a required key is missing, the corresponding feature degrades
gracefully (e.g. LLM summary falls back to rule-based).
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

# Load .env from repo root (one level above backend/)
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
load_dotenv(_REPO_ROOT / ".env")


@dataclass(frozen=True)
class Settings:
    """Application settings loaded from environment variables."""

    # ---- Roboflow ----
    roboflow_api_key: str | None

    # ---- OpenRouter (LLM) ----
    openrouter_api_key: str | None
    openrouter_base_url: str
    openrouter_model: str

    # ---- Backend ----
    backend_host: str
    backend_port: int

    # ---- Frontend ----
    frontend_port: int

    # ---- TTS ----
    tts_backend: str
    tts_voice: str
    tts_enabled: bool

    # ---- Detection ----
    model_path: str
    confidence_threshold: float

    @property
    def llm_enabled(self) -> bool:
        """True if OpenRouter key is set — enables LLM summaries in Stage 8."""
        return bool(self.openrouter_api_key and self.openrouter_api_key.strip())

    @property
    def roboflow_configured(self) -> bool:
        """True if Roboflow API key is set — enables dataset download."""
        return bool(self.roboflow_api_key and self.roboflow_api_key.strip())


def _get_str(key: str, default: str = "") -> str:
    """Get a string env var, returning default if unset or empty."""
    val = os.getenv(key, default)
    return val if val else default


def _get_int(key: str, default: int) -> int:
    """Get an int env var, returning default if unset or invalid."""
    try:
        return int(os.getenv(key, str(default)))
    except (ValueError, TypeError):
        return default


def _get_float(key: str, default: float) -> float:
    """Get a float env var, returning default if unset or invalid."""
    try:
        return float(os.getenv(key, str(default)))
    except (ValueError, TypeError):
        return default


def _get_bool(key: str, default: bool) -> bool:
    """Get a bool env var (true/false/1/0)."""
    raw = os.getenv(key, str(default)).strip().lower()
    return raw in ("true", "1", "yes", "on")


def _get_optional(key: str) -> str | None:
    """Get an env var that may be absent (returns None if empty)."""
    raw = os.getenv(key)
    if raw is None or raw.strip() == "":
        return None
    return raw.strip()


settings = Settings(
    roboflow_api_key=_get_optional("ROBOFLOW_API_KEY"),
    openrouter_api_key=_get_optional("OPENROUTER_API_KEY"),
    openrouter_base_url=_get_str("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
    openrouter_model=_get_str("OPENROUTER_MODEL", "openai/gpt-4o-mini"),
    backend_host=_get_str("BACKEND_HOST", "0.0.0.0"),
    backend_port=_get_int("BACKEND_PORT", 8000),
    frontend_port=_get_int("FRONTEND_PORT", 5173),
    tts_backend=_get_str("TTS_BACKEND", "edge"),
    tts_voice=_get_str("TTS_VOICE", "en-US-AriaNeural"),
    tts_enabled=_get_bool("TTS_ENABLED", True),
    model_path=_get_str("MODEL_PATH", "artifacts/stage2_model/best.pt"),
    confidence_threshold=_get_float("CONFIDENCE_THRESHOLD", 0.5),
)
