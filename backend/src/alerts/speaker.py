"""Zone-to-speaker (voice) mapping.

Each zone can optionally use a different edge-tts voice. This module
resolves which voice to use for a given zone, falling back to the
default voice from settings.

Usage:
    from backend.src.alerts.speaker import get_voice_for_zone
    voice = get_voice_for_zone(3)  # "en-US-GuyNeural" (Welding Zone)
    voice = get_voice_for_zone(1)  # "en-US-AriaNeural" (default)
"""

from __future__ import annotations

from backend.config.settings import settings
from backend.config.tts_config import ZONE_VOICE_MAP


def get_voice_for_zone(zone_id: int) -> str:
    """Get the edge-tts voice ID for a specific zone.

    Falls back to the default voice from settings if the zone has no
    specific mapping.

    Args:
        zone_id: The zone ID (1-6).

    Returns:
        edge-tts voice ID string (e.g. "en-US-AriaNeural").
    """
    return ZONE_VOICE_MAP.get(zone_id, settings.tts_voice)


def get_all_zone_voices() -> dict[int, str]:
    """Get the voice mapping for all zones.

    Returns:
        Dict mapping zone_id to voice ID. Zones not in ZONE_VOICE_MAP
        use the default voice.
    """
    result: dict[int, str] = {}
    for zone_id in range(1, 7):
        result[zone_id] = get_voice_for_zone(zone_id)
    return result
