"""Data models for the rule engine.

Defines the Violation dataclass returned by check_compliance() and the
Detection type alias used as input.

A Violation represents a single person who is missing one or more
required PPE items in a specific zone.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime


@dataclass
class Violation:
    """A PPE compliance violation for a single person in a zone.

    Attributes:
        zone_id: ID of the zone where the violation was detected.
        zone_name: Human-readable name of the zone.
        person_bbox: Bounding box of the person [x1, y1, x2, y2].
        missing_ppe: List of canonical PPE names that are missing.
        severity: 'high', 'medium', or 'low'.
        timestamp: ISO 8601 formatted timestamp of when the violation
            was detected.
    """

    zone_id: int
    zone_name: str
    person_bbox: tuple[int, int, int, int]
    missing_ppe: list[str]
    severity: str
    timestamp: str = field(
        default_factory=lambda: datetime.now(UTC).isoformat()
    )

    def to_dict(self) -> dict:
        """Convert to a dict for JSON serialization (API responses, logging).

        Returns:
            Dict representation of the violation.
        """
        return {
            "zone_id": self.zone_id,
            "zone_name": self.zone_name,
            "person_bbox": list(self.person_bbox),
            "missing_ppe": self.missing_ppe,
            "severity": self.severity,
            "timestamp": self.timestamp,
        }


# Type alias for a detection result from the predictor.
# Format: {"class_name": str, "confidence": float, "bbox": [x1, y1, x2, y2]}
Detection = dict[str, object]
