"""Hotspot analysis — identifies the most problematic zones.

Ranks zones by violation count and violation rate (violations per scan)
to identify safety hotspots that need attention.

Usage:
    from backend.src.analytics.event_logger import EventLogger
    from backend.src.analytics.hotspot_analysis import get_hotspots
    logger = EventLogger()
    hotspots = get_hotspots(logger, top_n=3)
"""

from __future__ import annotations

from backend.src.analytics.event_logger import EventLogger
from backend.src.rules.zone_config import get_zone


def get_hotspots(
    logger: EventLogger,
    top_n: int = 3,
) -> list[dict[str, object]]:
    """Identify the top-N most problematic zones by violation count.

    Ties are broken by violation rate (violations per scan).

    Args:
        logger: The EventLogger instance.
        top_n: Number of top zones to return.

    Returns:
        List of dicts sorted by violation count (descending):
        [{"zone_id": 3, "zone_name": "Welding Zone", "violations": 8,
          "scans": 5, "violation_rate": 1.6, "rank": 1}, ...]
        Returns fewer than top_n if not enough zones have violations.
    """
    zone_stats = logger.get_zone_stats()

    hotspots: list[dict[str, object]] = []
    for zone_id, stats in zone_stats.items():
        scans = stats["scans"]
        violations = stats["violations"]
        violation_rate = violations / scans if scans > 0 else 0.0

        if violations > 0:
            zone = get_zone(zone_id)
            hotspots.append({
                "zone_id": zone_id,
                "zone_name": zone.name,
                "violations": violations,
                "scans": scans,
                "violation_rate": round(violation_rate, 2),
            })

    # Sort by violations (desc), then by violation_rate (desc)
    hotspots.sort(key=lambda x: (x["violations"], x["violation_rate"]), reverse=True)

    # Assign ranks and limit to top_n
    for i, h in enumerate(hotspots[:top_n]):
        h["rank"] = i + 1

    return hotspots[:top_n]


def get_zone_risk_level(
    logger: EventLogger,
    zone_id: int,
) -> str:
    """Classify a zone's risk level based on its violation rate.

    Args:
        logger: The EventLogger instance.
        zone_id: The zone to assess.

    Returns:
        'critical' (rate >= 1.0), 'high' (rate >= 0.5),
        'moderate' (rate >= 0.25), 'low' (rate < 0.25), or 'none' (no scans).
    """
    zone_stats = logger.get_zone_stats()
    if zone_id not in zone_stats:
        return "none"

    stats = zone_stats[zone_id]
    scans = stats["scans"]
    if scans == 0:
        return "none"

    rate = stats["violations"] / scans
    if rate >= 1.0:
        return "critical"
    if rate >= 0.5:
        return "high"
    if rate >= 0.25:
        return "moderate"
    return "low"
