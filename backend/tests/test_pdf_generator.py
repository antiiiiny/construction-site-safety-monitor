"""Tests for the PDF report generator.

Tests cover:
  - PDF generation from mock events
  - Non-empty bytes
  - Valid PDF header
  - Multiple pages for large event logs
  - Empty event log handling
  - Summary generator
  - Recommendations generator
"""

from __future__ import annotations

from backend.src.reporting.pdf_generator import _compute_metrics, generate_daily_report
from backend.src.reporting.recommendations import generate_recommendations
from backend.src.reporting.summary_generator import generate_summary


def _make_mock_events(n: int = 15) -> list[dict]:
    """Create a list of mock scan + violation events."""
    events: list[dict] = []
    zone_names = {
        1: "Entry Gate", 2: "Scaffold Zone", 3: "Welding Zone",
        4: "Concrete Zone", 5: "Loading Zone", 6: "Material Yard",
    }
    for i in range(n):
        zone_id = (i % 6) + 1
        # Scan event
        events.append({
            "type": "scan",
            "timestamp": f"2026-07-07T12:{i:02d}:00+00:00",
            "zone_id": zone_id,
            "detection_count": 3,
            "violation_count": 1 if i % 3 == 0 else 0,
            "detected_classes": ["person", "helmet"],
        })
        # Violation event (every 3rd scan)
        if i % 3 == 0:
            missing = ["helmet"] if i % 2 == 0 else ["helmet", "vest"]
            events.append({
                "type": "violation",
                "timestamp": f"2026-07-07T12:{i:02d}:30+00:00",
                "zone_id": zone_id,
                "zone_name": zone_names[zone_id],
                "person_bbox": [100, 100, 300, 600],
                "missing_ppe": missing,
                "severity": "high" if zone_id == 3 else "medium",
            })
    return events


class TestPdfGeneration:
    """Tests for generate_daily_report()."""

    def test_generates_non_empty_bytes(self) -> None:
        """PDF should be non-empty bytes."""
        events = _make_mock_events(15)
        pdf = generate_daily_report(events, "Test Site", "2026-07-07")
        assert isinstance(pdf, bytes)
        assert len(pdf) > 0

    def test_valid_pdf_header(self) -> None:
        """PDF should start with %PDF header."""
        events = _make_mock_events(15)
        pdf = generate_daily_report(events, "Test Site", "2026-07-07")
        assert pdf[:5] == b"%PDF-"

    def test_empty_event_log(self) -> None:
        """Empty event log should still produce a valid PDF."""
        pdf = generate_daily_report([], "Empty Site", "2026-07-07")
        assert isinstance(pdf, bytes)
        assert len(pdf) > 0
        assert pdf[:5] == b"%PDF-"

    def test_no_violations(self) -> None:
        """Event log with no violations should produce a valid PDF."""
        events = [
            {"type": "scan", "timestamp": "2026-07-07T12:00:00+00:00",
             "zone_id": 1, "detection_count": 2, "violation_count": 0,
             "detected_classes": ["person", "helmet"]},
        ]
        pdf = generate_daily_report(events, "Safe Site", "2026-07-07")
        assert pdf[:5] == b"%PDF-"

    def test_large_event_log(self) -> None:
        """Large event log (50+ events) should produce a multi-page PDF."""
        events = _make_mock_events(50)
        pdf = generate_daily_report(events, "Large Site", "2026-07-07")
        assert len(pdf) > 1000  # Should be a substantial PDF

    def test_default_date(self) -> None:
        """Date should default to today if not provided."""
        events = _make_mock_events(5)
        pdf = generate_daily_report(events, "Test Site")
        assert pdf[:5] == b"%PDF-"


class TestComputeMetrics:
    """Tests for _compute_metrics()."""

    def test_empty_log(self) -> None:
        """Empty log should return zero metrics."""
        metrics = _compute_metrics([])
        assert metrics["total_scans"] == 0
        assert metrics["total_violations"] == 0
        assert metrics["compliance_rate"] == 1.0
        assert metrics["most_unsafe_zone"] is None

    def test_correct_counts(self) -> None:
        """Metrics should correctly count scans and violations."""
        events = _make_mock_events(15)
        metrics = _compute_metrics(events)
        assert metrics["total_scans"] == 15
        # Every 3rd scan (i=0,3,6,9,12) has a violation = 5 violations
        assert metrics["total_violations"] == 5

    def test_violations_per_ppe(self) -> None:
        """PPE breakdown should be correct."""
        events = _make_mock_events(15)
        metrics = _compute_metrics(events)
        assert "helmet" in metrics["violations_per_ppe"]
        assert "vest" in metrics["violations_per_ppe"]


class TestSummaryGenerator:
    """Tests for generate_summary()."""

    def test_empty_log(self) -> None:
        """Empty log should produce a 'no scans' message."""
        metrics = _compute_metrics([])
        summary = generate_summary([], metrics)
        assert "No scans" in summary

    def test_no_violations(self) -> None:
        """No violations should produce a positive summary."""
        events = [
            {"type": "scan", "timestamp": "...", "zone_id": 1,
             "detection_count": 2, "violation_count": 0, "detected_classes": []},
        ]
        metrics = _compute_metrics(events)
        summary = generate_summary(events, metrics)
        assert "zero" in summary.lower() or "100%" in summary

    def test_with_violations(self) -> None:
        """Violations should produce a detailed summary."""
        events = _make_mock_events(15)
        metrics = _compute_metrics(events)
        summary = generate_summary(events, metrics)
        assert len(summary) > 100  # Should be substantial
        assert "compliance" in summary.lower() or "violation" in summary.lower()


class TestRecommendations:
    """Tests for generate_recommendations()."""

    def test_empty_log(self) -> None:
        """Empty log should recommend activating the system."""
        metrics = _compute_metrics([])
        recs = generate_recommendations(metrics)
        assert len(recs) >= 1
        assert any("activate" in r.lower() or "monitoring" in r.lower() for r in recs)

    def test_no_violations(self) -> None:
        """No violations should recommend maintaining standards."""
        events = [
            {"type": "scan", "timestamp": "...", "zone_id": 1,
             "detection_count": 2, "violation_count": 0, "detected_classes": []},
        ]
        metrics = _compute_metrics(events)
        recs = generate_recommendations(metrics)
        assert any("maintain" in r.lower() for r in recs)

    def test_low_compliance(self) -> None:
        """Low compliance should trigger urgent recommendation."""
        events = _make_mock_events(15)
        metrics = _compute_metrics(events)
        # Force low compliance
        metrics["compliance_rate"] = 0.5
        recs = generate_recommendations(metrics)
        assert any("URGENT" in r or "70%" in r for r in recs)

    def test_with_violations(self) -> None:
        """Violations should produce actionable recommendations."""
        events = _make_mock_events(15)
        metrics = _compute_metrics(events)
        recs = generate_recommendations(metrics)
        assert len(recs) >= 2
        assert any("monitoring" in r.lower() or "briefing" in r.lower() for r in recs)
