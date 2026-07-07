"""Export event log to CSV format.

Provides a function to serialize the event log as CSV bytes for
download via the FastAPI `/api/export/csv` endpoint.

Usage:
    from backend.src.analytics.event_logger import EventLogger
    from backend.src.analytics.export_csv import export_events_csv
    logger = EventLogger()
    csv_bytes = export_events_csv(logger)
"""

from __future__ import annotations

import csv
import io

from backend.src.analytics.event_logger import EventLogger


def export_events_csv(logger: EventLogger) -> bytes:
    """Export all violation events as CSV bytes.

    Args:
        logger: The EventLogger instance.

    Returns:
        CSV content as UTF-8 encoded bytes.
    """
    output = io.StringIO()
    writer = csv.writer(output)

    # Header row
    writer.writerow([
        "timestamp",
        "type",
        "zone_id",
        "zone_name",
        "severity",
        "missing_ppe",
        "detection_count",
        "violation_count",
    ])

    # Write all events (scans + violations)
    for event in logger.get_all_events():
        writer.writerow([
            event.get("timestamp", ""),
            event.get("type", ""),
            event.get("zone_id", ""),
            event.get("zone_name", ""),
            event.get("severity", ""),
            "|".join(event.get("missing_ppe", [])) if event.get("missing_ppe") else "",
            event.get("detection_count", ""),
            event.get("violation_count", ""),
        ])

    return output.getvalue().encode("utf-8")


def export_summary_csv(logger: EventLogger) -> bytes:
    """Export per-zone summary as CSV bytes.

    Args:
        logger: The EventLogger instance.

    Returns:
        CSV content with one row per zone.
    """
    output = io.StringIO()
    writer = csv.writer(output)

    # Header
    writer.writerow([
        "zone_id",
        "zone_name",
        "scans",
        "violations",
        "compliance_rate",
        "most_common_missing_ppe",
    ])

    zone_stats = logger.get_zone_stats()

    for zone_id in range(1, 7):
        from backend.src.rules.zone_config import get_zone

        zone = get_zone(zone_id)
        stats = zone_stats.get(zone_id, {})
        scans = stats.get("scans", 0)
        violations = stats.get("violations", 0)
        compliance = 1.0 - (violations / scans) if scans > 0 else 1.0

        # Most common missing PPE in this zone
        ppe_counts = stats.get("missing_ppe_counts", {})
        most_common = max(ppe_counts, key=ppe_counts.get) if ppe_counts else "N/A"

        writer.writerow([
            zone_id,
            zone.name,
            scans,
            violations,
            f"{compliance:.2%}",
            most_common,
        ])

    return output.getvalue().encode("utf-8")
