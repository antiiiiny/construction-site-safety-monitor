"""LLM client for natural-language report summaries via OpenRouter.

OpenRouter is an OpenAI-compatible gateway. This module uses the
standard `requests` library (already a dependency via ultralytics) to
call the chat completions endpoint.

If OPENROUTER_API_KEY is not set, callers should fall back to the
rule-based summary generator. Use settings.llm_enabled to check.

Stage 8 usage:
    from backend.config.settings import settings
    from backend.reporting.llm_client import generate_llm_summary

    if settings.llm_enabled:
        summary = generate_llm_summary(event_data)
    else:
        summary = rule_based_summary(event_data)
"""

from __future__ import annotations

import json
import logging
from typing import Any

import requests

from backend.config.settings import settings

logger = logging.getLogger(__name__)

# OpenRouter chat completions endpoint (OpenAI-compatible)
_CHAT_ENDPOINT = "/chat/completions"

# System prompt that frames the LLM as a construction safety supervisor
_SYSTEM_PROMPT = (
    "You are a construction site safety supervisor. Given structured "
    "violation data from a day of safety monitoring, write a concise "
    "3-4 paragraph narrative summary of the day's safety status. "
    "Highlight the most problematic zones, common PPE violations, and "
    "overall compliance trends. Be professional and actionable. "
    "Do not use markdown — plain text only."
)


def generate_llm_summary(event_data: dict[str, Any]) -> str | None:
    """Generate a natural-language summary via OpenRouter GPT-4o-mini.

    Args:
        event_data: Structured dict containing metrics, zone stats, and
            recent violations. Typically the output of
            EventLogger.get_summary().

    Returns:
        Summary text string, or None if the API call fails (caller
        should fall back to rule-based summary).
    """
    if not settings.llm_enabled:
        logger.warning("OpenRouter API key not set — cannot use LLM summary.")
        return None

    url = f"{settings.openrouter_base_url}{_CHAT_ENDPOINT}"

    headers = {
        "Authorization": f"Bearer {settings.openrouter_api_key}",
        "Content-Type": "application/json",
        # OpenRouter recommends these for attribution
        "HTTP-Referer": "http://localhost:5173",
        "X-Title": "Construction Site Safety Monitor",
    }

    payload = {
        "model": settings.openrouter_model,
        "messages": [
            {"role": "system", "content": _SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    "Here is today's safety monitoring data as JSON. "
                    "Write the supervisor summary.\n\n"
                    f"{json.dumps(event_data, indent=2, default=str)}"
                ),
            },
        ],
        "temperature": 0.7,
        "max_tokens": 500,
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        result = response.json()
        content = result["choices"][0]["message"]["content"]
        logger.info("LLM summary generated successfully via OpenRouter.")
        return content
    except requests.exceptions.HTTPError as e:
        logger.error("OpenRouter API error: %s — %s", e, response.text[:500])
        return None
    except (KeyError, IndexError) as e:
        logger.error("Unexpected OpenRouter response format: %s", e)
        return None
    except requests.exceptions.RequestException as e:
        logger.error("OpenRouter request failed: %s", e)
        return None
