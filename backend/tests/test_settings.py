"""Tests for the settings module — verifies .env loading and defaults."""

from backend.config.settings import settings


def test_settings_loads_from_env() -> None:
    """Settings should be instantiated without error."""
    assert settings is not None


def test_backend_defaults() -> None:
    """Backend host/port should have sensible defaults."""
    assert settings.backend_host in ("0.0.0.0", "127.0.0.1", "localhost")
    assert settings.backend_port == 8000


def test_frontend_port_default() -> None:
    """Frontend port should default to 5173 (Vite)."""
    assert settings.frontend_port == 5173


def test_tts_defaults() -> None:
    """TTS should default to edge-tts with Aria voice."""
    assert settings.tts_backend == "edge"
    assert settings.tts_voice == "en-US-AriaNeural"
    assert settings.tts_enabled is True


def test_openrouter_defaults() -> None:
    """OpenRouter should default to GPT-4o-mini via openrouter.ai."""
    assert settings.openrouter_base_url == "https://openrouter.ai/api/v1"
    assert settings.openrouter_model == "openai/gpt-4o-mini"


def test_llm_enabled_flag() -> None:
    """llm_enabled should be True only if API key is set and non-empty."""
    # In test env, key is not set, so should be False
    assert settings.llm_enabled is False


def test_roboflow_configured_flag() -> None:
    """roboflow_configured should be True if key is set in .env."""
    # If .env has a real key, this is True; if not, False.
    # Either way, it should match the underlying key presence.
    assert settings.roboflow_configured is bool(settings.roboflow_api_key)


def test_confidence_threshold_default() -> None:
    """Confidence threshold should default to 0.5."""
    assert settings.confidence_threshold == 0.5
