"""End-to-end pipeline orchestrator.

Runs the full flow: load image → YOLOv8 detection → check compliance →
log events → build TTS message → return structured result.

This module is used by the /api/scan endpoint and the demo script.

Usage:
    from backend.src.api.pipeline import run_zone_pipeline
    result = run_zone_pipeline(zone_id=1, image_bytes=img_bytes)
"""

from __future__ import annotations

import logging
from typing import Any

from backend.src.alerts.message_builder import build_scan_summary_message
from backend.src.analytics.event_logger import EventLogger
from backend.src.detection.predictor import Predictor
from backend.src.rules.violation_engine import check_compliance
from backend.src.rules.zone_config import get_zone

logger = logging.getLogger(__name__)

# Singleton predictor — loaded once on first use
_predictor: Predictor | None = None
# Singleton event logger — one session per backend process
_event_logger: EventLogger | None = None


def get_predictor() -> Predictor:
    """Get or create the singleton Predictor instance.

    Returns:
        The shared Predictor instance.
    """
    global _predictor
    if _predictor is None:
        _predictor = Predictor()
    return _predictor


def get_event_logger() -> EventLogger:
    """Get or create the singleton EventLogger instance.

    Returns:
        The shared EventLogger instance.
    """
    global _event_logger
    if _event_logger is None:
        _event_logger = EventLogger()
    return _event_logger


def reset_event_logger() -> None:
    """Clear the event logger (used by 'Clear Session' button)."""
    global _event_logger
    if _event_logger is not None:
        _event_logger.clear()
    else:
        _event_logger = EventLogger()


def run_zone_pipeline(
    zone_id: int,
    image_bytes: bytes,
    confidence: float | None = None,
) -> dict[str, Any]:
    """Run the full pipeline for one zone scan.

    Args:
        zone_id: The zone to check (1-6).
        image_bytes: Raw image bytes (JPEG/PNG).
        confidence: Optional confidence override.

    Returns:
        Dict with: zone_id, zone_name, detections, violations,
        tts_message, tts_audio_available, detection_count, violation_count.

    Raises:
        ValueError: If zone_id is invalid.
        FileNotFoundError: If model weights are missing.
    """
    zone = get_zone(zone_id)
    predictor = get_predictor()
    logger_obj = get_event_logger()

    # 1. Run detection
    detections = predictor.predict(image_bytes, confidence=confidence)

    # 2. Check compliance
    violations = check_compliance(detections, zone_id)

    # 3. Log the scan + violations
    logger_obj.log_scan(zone_id, detections, violations)

    # 4. Build TTS message
    tts_message = build_scan_summary_message(zone.name, violations)

    # 5. Return structured result
    return {
        "zone_id": zone_id,
        "zone_name": zone.name,
        "detections": detections,
        "violations": [v.to_dict() for v in violations],
        "tts_message": tts_message,
        "tts_audio_available": bool(tts_message),
        "detection_count": len(detections),
        "violation_count": len(violations),
    }
