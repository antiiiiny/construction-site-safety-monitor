"""Event logger — stores violation events and scan records in memory.

The EventLogger is session-scoped: each session (identified by a
session_id) has its own event log. No database — all data is lost on
backend restart. This is intentional for a demo/capstone project.

Usage:
    from backend.src.analytics.event_logger import EventLogger
    logger = EventLogger()
    logger.log_scan(zone_id=1, detections=[...], violations=[...])
    summary = logger.get_summary()
"""

from __future__ import annotations

import uuid
from collections import defaultdict
from datetime import UTC, datetime
from typing import Any

from backend.src.rules.models import Violation


class EventLogger:
    """In-memory event store for violation events and scan records.

    Attributes:
        session_id: Unique identifier for this session.
        events: List of all event dicts (violations + scans).
    """

    def __init__(self, session_id: str | None = None) -> None:
        """Initialize a new event logger.

        Args:
            session_id: Optional session ID. Auto-generated if not provided.
        """
        self.session_id: str = session_id or str(uuid.uuid4())
        self._events: list[dict[str, Any]] = []
        self._scans: list[dict[str, Any]] = []
        self._violations: list[dict[str, Any]] = []

    def log_violation(self, violation: Violation) -> None:
        """Log a single violation event.

        Args:
            violation: The Violation object to log.
        """
        event = {
            "type": "violation",
            "timestamp": violation.timestamp,
            "zone_id": violation.zone_id,
            "zone_name": violation.zone_name,
            "person_bbox": list(violation.person_bbox),
            "missing_ppe": violation.missing_ppe,
            "severity": violation.severity,
            "session_id": self.session_id,
        }
        self._events.append(event)
        self._violations.append(event)

    def log_scan(
        self,
        zone_id: int,
        detections: list[dict],
        violations: list[Violation],
    ) -> None:
        """Log a complete scan event (one camera image processed).

        Args:
            zone_id: The zone that was scanned.
            detections: Raw detections from the predictor.
            violations: Violations found by the rule engine.
        """
        timestamp = datetime.now(UTC).isoformat()

        # Log the scan record
        scan_event = {
            "type": "scan",
            "timestamp": timestamp,
            "zone_id": zone_id,
            "detection_count": len(detections),
            "violation_count": len(violations),
            "detected_classes": list(
                {d["class_name"] for d in detections if "class_name" in d}
            ),
            "session_id": self.session_id,
        }
        self._events.append(scan_event)
        self._scans.append(scan_event)

        # Log each violation from this scan
        for v in violations:
            self.log_violation(v)

    def get_all_events(self) -> list[dict[str, Any]]:
        """Return all events (scans + violations) in chronological order.

        Returns:
            List of event dicts.
        """
        return list(self._events)

    def get_violations(self) -> list[dict[str, Any]]:
        """Return only violation events.

        Returns:
            List of violation event dicts.
        """
        return list(self._violations)

    def get_scans(self) -> list[dict[str, Any]]:
        """Return only scan events.

        Returns:
            List of scan event dicts.
        """
        return list(self._scans)

    def get_zone_stats(self) -> dict[int, dict[str, Any]]:
        """Get per-zone statistics.

        Returns:
            Dict keyed by zone_id, each containing:
            - scans: number of scans in this zone
            - violations: number of violations in this zone
            - missing_ppe_counts: {ppe_name: count}
            - severity_counts: {severity: count}
        """
        stats: dict[int, dict[str, Any]] = defaultdict(
            lambda: {
                "scans": 0,
                "violations": 0,
                "missing_ppe_counts": defaultdict(int),
                "severity_counts": defaultdict(int),
            }
        )

        for scan in self._scans:
            stats[scan["zone_id"]]["scans"] += 1

        for v in self._violations:
            zid = v["zone_id"]
            stats[zid]["violations"] += 1
            for ppe in v["missing_ppe"]:
                stats[zid]["missing_ppe_counts"][ppe] += 1
            stats[zid]["severity_counts"][v["severity"]] += 1

        # Convert defaultdicts to regular dicts for serialization
        result: dict[int, dict[str, Any]] = {}
        for zid, data in stats.items():
            result[zid] = {
                "scans": data["scans"],
                "violations": data["violations"],
                "missing_ppe_counts": dict(data["missing_ppe_counts"]),
                "severity_counts": dict(data["severity_counts"]),
            }
        return result

    def get_summary(self) -> dict[str, Any]:
        """Get overall summary metrics for the session.

        Returns:
            Dict with:
            - total_scans: total number of scans
            - total_violations: total number of violations
            - total_persons_violated: unique persons with violations
            - compliance_rate: (scans_without_violation / total_scans)
            - violations_per_zone: {zone_id: count}
            - violations_per_ppe: {ppe_name: count}
            - severity_breakdown: {severity: count}
            - most_unsafe_zone: zone_id with most violations (or None)
            - session_id: this session's ID
        """
        total_scans = len(self._scans)
        total_violations = len(self._violations)

        # Scans without any violations
        scans_with_violations = sum(
            1 for s in self._scans if s["violation_count"] > 0
        )
        compliance_rate = (
            (total_scans - scans_with_violations) / total_scans
            if total_scans > 0
            else 1.0
        )

        # Violations per zone
        violations_per_zone: dict[int, int] = defaultdict(int)
        for v in self._violations:
            violations_per_zone[v["zone_id"]] += 1

        # Violations per PPE type
        violations_per_ppe: dict[str, int] = defaultdict(int)
        for v in self._violations:
            for ppe in v["missing_ppe"]:
                violations_per_ppe[ppe] += 1

        # Severity breakdown
        severity_breakdown: dict[str, int] = defaultdict(int)
        for v in self._violations:
            severity_breakdown[v["severity"]] += 1

        # Most unsafe zone
        most_unsafe_zone: int | None = None
        if violations_per_zone:
            most_unsafe_zone = max(
                violations_per_zone, key=lambda k: violations_per_zone[k]
            )

        return {
            "total_scans": total_scans,
            "total_violations": total_violations,
            "scans_with_violations": scans_with_violations,
            "compliance_rate": round(compliance_rate, 4),
            "violations_per_zone": dict(violations_per_zone),
            "violations_per_ppe": dict(violations_per_ppe),
            "severity_breakdown": dict(severity_breakdown),
            "most_unsafe_zone": most_unsafe_zone,
            "session_id": self.session_id,
        }

    def clear(self) -> None:
        """Clear all events from the logger."""
        self._events.clear()
        self._scans.clear()
        self._violations.clear()
