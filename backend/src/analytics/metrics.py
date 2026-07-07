"""Metrics aggregation functions for the analytics dashboard.

Provides functions to compute chart-ready data from the EventLogger:
  - Violations per zone (bar chart)
  - Violations per PPE type (pie chart)
  - Zone hotspot ranking
  - Hourly/batch-wise violation timeline

Usage:
    from backend.src.analytics.event_logger import EventLogger
    from backend.src.analytics.metrics import get_violations_per_zone
    logger = EventLogger()
    bar_data = get_violations_per_zone(logger)
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from backend.src.analytics.event_logger import EventLogger
from backend.src.rules.zone_config import get_zone


def get_violations_per_zone(logger: EventLogger) -> list[dict[str, Any]]:
    """Get violation counts per zone for bar chart.

    Args:
        logger: The EventLogger instance.

    Returns:
        List of dicts: [{"zone_id": 1, "zone_name": "Entry Gate", "violations": 5}, ...]
        Includes all 6 zones, even those with 0 violations.
    """
    zone_counts: dict[int, int] = defaultdict(int)
    for v in logger.get_violations():
        zone_counts[v["zone_id"]] += 1

    result: list[dict[str, Any]] = []
    for zone_id in range(1, 7):
        zone = get_zone(zone_id)
        result.append({
            "zone_id": zone_id,
            "zone_name": zone.name,
            "violations": zone_counts.get(zone_id, 0),
        })
    return result


def get_violations_per_ppe(logger: EventLogger) -> list[dict[str, Any]]:
    """Get violation counts per PPE type for pie chart.

    Args:
        logger: The EventLogger instance.

    Returns:
        List of dicts: [{"ppe": "helmet", "count": 12}, ...]
    """
    ppe_counts: dict[str, int] = defaultdict(int)
    for v in logger.get_violations():
        for ppe in v["missing_ppe"]:
            ppe_counts[ppe] += 1

    return [{"ppe": ppe, "count": count} for ppe, count in sorted(ppe_counts.items())]


def get_severity_breakdown(logger: EventLogger) -> list[dict[str, Any]]:
    """Get violation counts by severity level for chart.

    Args:
        logger: The EventLogger instance.

    Returns:
        List of dicts: [{"severity": "high", "count": 5}, ...]
    """
    severity_counts: dict[str, int] = defaultdict(int)
    for v in logger.get_violations():
        severity_counts[v["severity"]] += 1

    # Return in order: high, medium, low
    order = ["high", "medium", "low"]
    return [
        {"severity": s, "count": severity_counts.get(s, 0)}
        for s in order
        if s in severity_counts
    ]


def get_violation_timeline(logger: EventLogger) -> list[dict[str, Any]]:
    """Get violations in chronological order for timeline chart.

    Args:
        logger: The EventLogger instance.

    Returns:
        List of dicts: [{"index": 0, "timestamp": "...", "zone_name": "...", "severity": "high"}, ...]
    """
    violations = logger.get_violations()
    return [
        {
            "index": i,
            "timestamp": v["timestamp"],
            "zone_id": v["zone_id"],
            "zone_name": v["zone_name"],
            "severity": v["severity"],
            "missing_ppe": v["missing_ppe"],
        }
        for i, v in enumerate(violations)
    ]


def get_compliance_rate(logger: EventLogger) -> float:
    """Calculate the overall compliance rate.

    Compliance rate = (scans without violations) / (total scans)

    Args:
        logger: The EventLogger instance.

    Returns:
        Float between 0.0 and 1.0. Returns 1.0 if no scans.
    """
    summary = logger.get_summary()
    return summary["compliance_rate"]


def get_kpi_cards(logger: EventLogger) -> dict[str, Any]:
    """Get KPI card data for the dashboard.

    Args:
        logger: The EventLogger instance.

    Returns:
        Dict with: total_scans, total_violations, compliance_rate,
        most_unsafe_zone (name or None).
    """
    summary = logger.get_summary()
    most_unsafe_zone_name: str | None = None
    if summary["most_unsafe_zone"] is not None:
        most_unsafe_zone_name = get_zone(summary["most_unsafe_zone"]).name

    return {
        "total_scans": summary["total_scans"],
        "total_violations": summary["total_violations"],
        "compliance_rate": summary["compliance_rate"],
        "most_unsafe_zone": most_unsafe_zone_name,
    }
