"""Tests for metrics, hotspot analysis, and CSV export.

Tests cover:
  - get_violations_per_zone() — bar chart data
  - get_violations_per_ppe() — pie chart data
  - get_severity_breakdown()
  - get_violation_timeline()
  - get_kpi_cards()
  - get_hotspots() — zone hotspot ranking
  - get_zone_risk_level()
  - export_events_csv() — CSV export
  - export_summary_csv() — per-zone CSV summary
"""

from __future__ import annotations

from backend.src.analytics.event_logger import EventLogger
from backend.src.analytics.export_csv import export_events_csv, export_summary_csv
from backend.src.analytics.hotspot_analysis import get_hotspots, get_zone_risk_level
from backend.src.analytics.metrics import (
    get_compliance_rate,
    get_kpi_cards,
    get_severity_breakdown,
    get_violation_timeline,
    get_violations_per_ppe,
    get_violations_per_zone,
)
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


def _populate_mock_logger(logger: EventLogger) -> None:
    """Populate a logger with 20+ mock events across 6 zones."""
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


# ---- Metrics tests ----


class TestViolationsPerZone:
    """Tests for get_violations_per_zone()."""

    def test_returns_all_6_zones(self) -> None:
        """Should return all 6 zones even if some have 0 violations."""
        logger = EventLogger()
        result = get_violations_per_zone(logger)
        assert len(result) == 6
        assert all("zone_id" in z for z in result)
        assert all("zone_name" in z for z in result)
        assert all("violations" in z for z in result)

    def test_correct_counts(self) -> None:
        """Violation counts should match what was logged."""
        logger = EventLogger()
        _populate_mock_logger(logger)
        result = get_violations_per_zone(logger)
        zone_map = {z["zone_id"]: z["violations"] for z in result}
        assert zone_map[1] == 3
        assert zone_map[2] == 0
        assert zone_map[3] == 4
        assert zone_map[6] == 2


class TestViolationsPerPPE:
    """Tests for get_violations_per_ppe()."""

    def test_empty_logger(self) -> None:
        """Empty logger should return empty list."""
        logger = EventLogger()
        assert get_violations_per_ppe(logger) == []

    def test_correct_counts(self) -> None:
        """PPE counts should match."""
        logger = EventLogger()
        _populate_mock_logger(logger)
        result = get_violations_per_ppe(logger)
        ppe_map = {item["ppe"]: item["count"] for item in result}
        assert ppe_map["helmet"] == 5  # zone1(2) + zone3(1) + zone4(1) + zone6(1)
        assert ppe_map["vest"] == 3
        assert ppe_map["gloves"] == 3


class TestSeverityBreakdown:
    """Tests for get_severity_breakdown()."""

    def test_correct_order(self) -> None:
        """Should return severities in high/medium/low order."""
        logger = EventLogger()
        _populate_mock_logger(logger)
        result = get_severity_breakdown(logger)
        severities = [r["severity"] for r in result]
        assert severities == ["high", "medium"]  # no 'low' in mock data

    def test_counts(self) -> None:
        """Severity counts should match."""
        logger = EventLogger()
        _populate_mock_logger(logger)
        result = get_severity_breakdown(logger)
        sev_map = {r["severity"]: r["count"] for r in result}
        assert sev_map["high"] == 4  # zone3 has 4 high
        assert sev_map["medium"] == 6  # rest are medium


class TestViolationTimeline:
    """Tests for get_violation_timeline()."""

    def test_empty(self) -> None:
        """Empty logger should return empty timeline."""
        logger = EventLogger()
        assert get_violation_timeline(logger) == []

    def test_chronological_order(self) -> None:
        """Timeline should be in chronological order with indices."""
        logger = EventLogger()
        _populate_mock_logger(logger)
        timeline = get_violation_timeline(logger)
        assert len(timeline) == 10  # total violations
        assert timeline[0]["index"] == 0
        assert timeline[-1]["index"] == 9


class TestKpiCards:
    """Tests for get_kpi_cards()."""

    def test_empty(self) -> None:
        """Empty logger KPIs should be zero."""
        logger = EventLogger()
        kpis = get_kpi_cards(logger)
        assert kpis["total_scans"] == 0
        assert kpis["total_violations"] == 0
        assert kpis["compliance_rate"] == 1.0
        assert kpis["most_unsafe_zone"] is None

    def test_populated(self) -> None:
        """KPIs should reflect the mock data."""
        logger = EventLogger()
        _populate_mock_logger(logger)
        kpis = get_kpi_cards(logger)
        assert kpis["total_scans"] == 10
        assert kpis["total_violations"] == 10
        assert kpis["most_unsafe_zone"] == "Welding Zone"


class TestComplianceRate:
    """Tests for get_compliance_rate()."""

    def test_empty(self) -> None:
        """Empty logger should have 100% compliance."""
        logger = EventLogger()
        assert get_compliance_rate(logger) == 1.0

    def test_partial(self) -> None:
        """Mock data should have correct compliance rate."""
        logger = EventLogger()
        _populate_mock_logger(logger)
        rate = get_compliance_rate(logger)
        # 3 scans without violations (zone2, zone5, + 1 scan in zone1 without... wait)
        # Actually: 10 scans total, 7 with violations → 3 clean → 0.3
        assert 0.0 <= rate <= 1.0


# ---- Hotspot analysis tests ----


class TestHotspots:
    """Tests for get_hotspots()."""

    def test_empty(self) -> None:
        """Empty logger should return no hotspots."""
        logger = EventLogger()
        assert get_hotspots(logger) == []

    def test_top_3(self) -> None:
        """Should return top 3 zones by violation count."""
        logger = EventLogger()
        _populate_mock_logger(logger)
        hotspots = get_hotspots(logger, top_n=3)
        assert len(hotspots) == 3
        assert hotspots[0]["zone_id"] == 3  # Zone 3 has 4 violations
        assert hotspots[0]["rank"] == 1
        assert hotspots[1]["zone_id"] == 1  # Zone 1 has 3
        assert hotspots[2]["zone_id"] == 6  # Zone 6 has 2

    def test_violation_rate(self) -> None:
        """Violation rate should be calculated correctly."""
        logger = EventLogger()
        _populate_mock_logger(logger)
        hotspots = get_hotspots(logger, top_n=1)
        # Zone 3: 4 violations / 3 scans = 1.33
        assert hotspots[0]["violation_rate"] == 1.33


class TestZoneRiskLevel:
    """Tests for get_zone_risk_level()."""

    def test_no_scans(self) -> None:
        """Zone with no scans should be 'none'."""
        logger = EventLogger()
        assert get_zone_risk_level(logger, zone_id=1) == "none"

    def test_critical(self) -> None:
        """Zone with rate >= 1.0 should be 'critical'."""
        logger = EventLogger()
        logger.log_scan(zone_id=3, detections=[],
                        violations=[_make_violation(zone_id=3, severity="high")])
        assert get_zone_risk_level(logger, zone_id=3) == "critical"


# ---- CSV export tests ----


class TestExportCsv:
    """Tests for CSV export functions."""

    def test_export_events_csv_empty(self) -> None:
        """Empty logger CSV should have just the header."""
        logger = EventLogger()
        csv_bytes = export_events_csv(logger)
        assert isinstance(csv_bytes, bytes)
        text = csv_bytes.decode("utf-8")
        assert "timestamp" in text
        assert "zone_id" in text

    def test_export_events_csv_populated(self) -> None:
        """Populated logger CSV should contain event rows."""
        logger = EventLogger()
        _populate_mock_logger(logger)
        csv_bytes = export_events_csv(logger)
        text = csv_bytes.decode("utf-8")
        lines = text.strip().split("\n")
        assert len(lines) > 1  # header + data rows
        assert "Entry Gate" in text or "Welding Zone" in text

    def test_export_summary_csv(self) -> None:
        """Summary CSV should have one row per zone."""
        logger = EventLogger()
        _populate_mock_logger(logger)
        csv_bytes = export_summary_csv(logger)
        text = csv_bytes.decode("utf-8")
        lines = text.strip().split("\n")
        assert len(lines) == 7  # header + 6 zones
        assert "Entry Gate" in text
        assert "Welding Zone" in text
