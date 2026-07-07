"""Tests for the EventLogger class.

Tests cover:
  - Logging violations and scans
  - get_all_events(), get_violations(), get_scans()
  - get_zone_stats() per-zone breakdown
  - get_summary() overall metrics
  - clear()
  - Session ID handling
"""

from __future__ import annotations

from backend.src.analytics.event_logger import EventLogger
from backend.src.rules.models import Violation


def _make_violation(
    zone_id: int = 1,
    missing: list[str] | None = None,
    severity: str = "medium",
) -> Violation:
    """Create a mock Violation for testing."""
    if missing is None:
        missing = ["helmet"]
    zone_names = {
        1: "Entry Gate", 2: "Scaffold Zone", 3: "Welding Zone",
        4: "Concrete Zone", 5: "Loading Zone", 6: "Material Yard",
    }
    return Violation(
        zone_id=zone_id,
        zone_name=zone_names[zone_id],
        person_bbox=(100, 100, 300, 600),
        missing_ppe=missing,
        severity=severity,
    )


class TestEventLoggerBasic:
    """Basic logging and retrieval tests."""

    def test_empty_logger(self) -> None:
        """A new logger should have no events."""
        logger = EventLogger()
        assert len(logger.get_all_events()) == 0
        assert len(logger.get_violations()) == 0
        assert len(logger.get_scans()) == 0

    def test_log_single_violation(self) -> None:
        """log_violation should add one event."""
        logger = EventLogger()
        logger.log_violation(_make_violation(zone_id=1, missing=["helmet"]))
        assert len(logger.get_violations()) == 1
        assert len(logger.get_all_events()) == 1

    def test_log_scan_with_no_violations(self) -> None:
        """log_scan with no violations should add only a scan event."""
        logger = EventLogger()
        logger.log_scan(zone_id=1, detections=[{"class_name": "person"}], violations=[])
        assert len(logger.get_scans()) == 1
        assert len(logger.get_violations()) == 0
        assert len(logger.get_all_events()) == 1  # just the scan

    def test_log_scan_with_violations(self) -> None:
        """log_scan with violations should add scan + violation events."""
        logger = EventLogger()
        v = _make_violation(zone_id=1, missing=["helmet"])
        logger.log_scan(zone_id=1, detections=[{"class_name": "person"}], violations=[v])
        assert len(logger.get_scans()) == 1
        assert len(logger.get_violations()) == 1
        assert len(logger.get_all_events()) == 2  # scan + violation

    def test_session_id_auto_generated(self) -> None:
        """Session ID should be auto-generated if not provided."""
        logger = EventLogger()
        assert logger.session_id is not None
        assert len(logger.session_id) > 0

    def test_session_id_custom(self) -> None:
        """Custom session ID should be used."""
        logger = EventLogger(session_id="test-session-123")
        assert logger.session_id == "test-session-123"


class TestEventLoggerZoneStats:
    """Tests for get_zone_stats()."""

    def test_zone_stats_empty(self) -> None:
        """Empty logger should return empty zone stats."""
        logger = EventLogger()
        stats = logger.get_zone_stats()
        assert len(stats) == 0

    def test_zone_stats_with_violations(self) -> None:
        """Zone stats should correctly count violations per zone."""
        logger = EventLogger()
        logger.log_violation(_make_violation(zone_id=1, missing=["helmet"]))
        logger.log_violation(_make_violation(zone_id=1, missing=["vest"]))
        logger.log_violation(_make_violation(zone_id=3, missing=["gloves"]))

        stats = logger.get_zone_stats()
        assert stats[1]["violations"] == 2
        assert stats[3]["violations"] == 1
        assert stats[1]["missing_ppe_counts"]["helmet"] == 1
        assert stats[1]["missing_ppe_counts"]["vest"] == 1
        assert stats[3]["missing_ppe_counts"]["gloves"] == 1

    def test_zone_stats_with_scans(self) -> None:
        """Zone stats should count scans per zone."""
        logger = EventLogger()
        logger.log_scan(zone_id=1, detections=[], violations=[])
        logger.log_scan(zone_id=1, detections=[], violations=[])
        logger.log_scan(zone_id=3, detections=[], violations=[])

        stats = logger.get_zone_stats()
        assert stats[1]["scans"] == 2
        assert stats[3]["scans"] == 1

    def test_zone_stats_severity_counts(self) -> None:
        """Zone stats should count severities."""
        logger = EventLogger()
        logger.log_violation(_make_violation(zone_id=1, severity="high"))
        logger.log_violation(_make_violation(zone_id=1, severity="medium"))
        logger.log_violation(_make_violation(zone_id=1, severity="high"))

        stats = logger.get_zone_stats()
        assert stats[1]["severity_counts"]["high"] == 2
        assert stats[1]["severity_counts"]["medium"] == 1


class TestEventLoggerSummary:
    """Tests for get_summary()."""

    def test_summary_empty(self) -> None:
        """Empty logger summary should have zeros."""
        logger = EventLogger()
        s = logger.get_summary()
        assert s["total_scans"] == 0
        assert s["total_violations"] == 0
        assert s["compliance_rate"] == 1.0
        assert s["most_unsafe_zone"] is None

    def test_summary_counts(self) -> None:
        """Summary should correctly count scans and violations."""
        logger = EventLogger()
        logger.log_scan(zone_id=1, detections=[], violations=[])
        logger.log_scan(
            zone_id=3,
            detections=[{"class_name": "person"}],
            violations=[_make_violation(zone_id=3, missing=["gloves"], severity="high")],
        )

        s = logger.get_summary()
        assert s["total_scans"] == 2
        assert s["total_violations"] == 1
        assert s["scans_with_violations"] == 1
        assert s["compliance_rate"] == 0.5  # 1 of 2 scans clean

    def test_summary_violations_per_zone(self) -> None:
        """Summary should break down violations per zone."""
        logger = EventLogger()
        logger.log_violation(_make_violation(zone_id=1))
        logger.log_violation(_make_violation(zone_id=1))
        logger.log_violation(_make_violation(zone_id=3))

        s = logger.get_summary()
        assert s["violations_per_zone"][1] == 2
        assert s["violations_per_zone"][3] == 1

    def test_summary_violations_per_ppe(self) -> None:
        """Summary should break down violations per PPE type."""
        logger = EventLogger()
        logger.log_violation(_make_violation(missing=["helmet"]))
        logger.log_violation(_make_violation(missing=["helmet", "vest"]))
        logger.log_violation(_make_violation(missing=["gloves"]))

        s = logger.get_summary()
        assert s["violations_per_ppe"]["helmet"] == 2
        assert s["violations_per_ppe"]["vest"] == 1
        assert s["violations_per_ppe"]["gloves"] == 1

    def test_summary_most_unsafe_zone(self) -> None:
        """Summary should identify the most unsafe zone."""
        logger = EventLogger()
        logger.log_violation(_make_violation(zone_id=1))
        logger.log_violation(_make_violation(zone_id=3))
        logger.log_violation(_make_violation(zone_id=3))
        logger.log_violation(_make_violation(zone_id=3))

        s = logger.get_summary()
        assert s["most_unsafe_zone"] == 3

    def test_summary_severity_breakdown(self) -> None:
        """Summary should break down by severity."""
        logger = EventLogger()
        logger.log_violation(_make_violation(severity="high"))
        logger.log_violation(_make_violation(severity="high"))
        logger.log_violation(_make_violation(severity="medium"))

        s = logger.get_summary()
        assert s["severity_breakdown"]["high"] == 2
        assert s["severity_breakdown"]["medium"] == 1


class TestEventLoggerClear:
    """Tests for clear()."""

    def test_clear(self) -> None:
        """clear() should remove all events."""
        logger = EventLogger()
        logger.log_violation(_make_violation())
        logger.log_scan(zone_id=1, detections=[], violations=[])
        assert len(logger.get_all_events()) > 0

        logger.clear()
        assert len(logger.get_all_events()) == 0
        assert len(logger.get_violations()) == 0
        assert len(logger.get_scans()) == 0


class TestEventLoggerMockSession:
    """Test with a mock session of 20+ events across 6 zones."""

    def test_mock_session_20_events(self) -> None:
        """Log 20+ events across 6 zones and verify summary."""
        logger = EventLogger(session_id="mock-test")

        # Zone 1: 2 scans, 3 violations
        logger.log_scan(zone_id=1, detections=[{"class_name": "person"}],
                        violations=[_make_violation(zone_id=1, missing=["helmet"])])
        logger.log_scan(zone_id=1, detections=[{"class_name": "person"}],
                        violations=[_make_violation(zone_id=1, missing=["helmet", "vest"]),
                                    _make_violation(zone_id=1, missing=["vest"])])

        # Zone 2: 1 scan, 0 violations
        logger.log_scan(zone_id=2, detections=[{"class_name": "person"}], violations=[])

        # Zone 3: 3 scans, 4 violations
        for _ in range(3):
            logger.log_scan(zone_id=3, detections=[{"class_name": "person"}],
                            violations=[_make_violation(zone_id=3, missing=["gloves"], severity="high")])
        logger.log_violation(_make_violation(zone_id=3, missing=["helmet"], severity="high"))

        # Zone 4: 1 scan, 1 violation
        logger.log_scan(zone_id=4, detections=[{"class_name": "person"}],
                        violations=[_make_violation(zone_id=4, missing=["helmet"])])

        # Zone 5: 1 scan, 0 violations
        logger.log_scan(zone_id=5, detections=[{"class_name": "person"}], violations=[])

        # Zone 6: 2 scans, 2 violations
        logger.log_scan(zone_id=6, detections=[{"class_name": "person"}],
                        violations=[_make_violation(zone_id=6, missing=["helmet"])])
        logger.log_scan(zone_id=6, detections=[{"class_name": "person"}],
                        violations=[_make_violation(zone_id=6, missing=["vest"])])

        s = logger.get_summary()
        assert s["total_scans"] == 10
        assert s["total_violations"] == 10
        assert s["most_unsafe_zone"] == 3  # Zone 3 has 4 violations
        assert s["violations_per_zone"][3] == 4
        assert s["violations_per_zone"][1] == 3
        assert s["violations_per_zone"][6] == 2
        assert s["violations_per_zone"][4] == 1
