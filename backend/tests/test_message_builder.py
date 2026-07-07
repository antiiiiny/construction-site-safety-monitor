"""Tests for the alert message builder.

Tests cover:
  - Message generation for each severity (high/medium/low)
  - Single vs multiple missing PPE
  - All 6 zones
  - Scan summary message (multiple violations)
  - PPE display name formatting
"""

from __future__ import annotations

from backend.src.alerts.message_builder import (
    _format_ppe_list,
    build_alert_message,
    build_scan_summary_message,
)
from backend.src.rules.models import Violation


def _make_violation(
    zone_id: int = 1,
    zone_name: str = "Entry Gate",
    missing: list[str] | None = None,
    severity: str = "medium",
) -> Violation:
    """Create a mock Violation for testing."""
    if missing is None:
        missing = ["helmet"]
    return Violation(
        zone_id=zone_id,
        zone_name=zone_name,
        person_bbox=(100, 100, 300, 600),
        missing_ppe=missing,
        severity=severity,
    )


class TestFormatPpeList:
    """Tests for _format_ppe_list helper."""

    def test_single_item(self) -> None:
        assert _format_ppe_list(["helmet"]) == "hard hat"

    def test_two_items(self) -> None:
        assert _format_ppe_list(["helmet", "vest"]) == "hard hat and safety vest"

    def test_three_items(self) -> None:
        result = _format_ppe_list(["helmet", "vest", "gloves"])
        assert result == "hard hat, safety vest, and safety gloves"

    def test_unknown_ppe(self) -> None:
        """Unknown PPE names should pass through unchanged."""
        assert _format_ppe_list(["unknown"]) == "unknown"


class TestBuildAlertMessage:
    """Tests for build_alert_message()."""

    def test_high_severity_single(self) -> None:
        """High severity, single missing PPE."""
        v = _make_violation(
            zone_name="Welding Zone",
            missing=["gloves"],
            severity="high",
        )
        msg = build_alert_message(v)
        assert "Warning" in msg
        assert "Welding Zone" in msg
        assert "Safety gloves" in msg
        assert "high-risk" in msg
        assert "is" in msg  # singular verb

    def test_high_severity_multiple(self) -> None:
        """High severity, multiple missing PPE."""
        v = _make_violation(
            zone_name="Welding Zone",
            missing=["helmet", "gloves"],
            severity="high",
        )
        msg = build_alert_message(v)
        assert "Warning" in msg
        assert "are" in msg  # plural verb
        assert "high-risk" in msg

    def test_medium_severity(self) -> None:
        """Medium severity message."""
        v = _make_violation(
            zone_name="Entry Gate",
            missing=["helmet"],
            severity="medium",
        )
        msg = build_alert_message(v)
        assert "Attention" in msg
        assert "Entry Gate" in msg
        assert "Hard hat" in msg
        assert "required" in msg

    def test_low_severity(self) -> None:
        """Low severity message."""
        v = _make_violation(
            zone_name="Material Yard",
            missing=["vest"],
            severity="low",
        )
        msg = build_alert_message(v)
        assert "Notice" in msg
        assert "Material Yard" in msg
        assert "recommended" in msg

    def test_all_six_zones(self) -> None:
        """Message should include the zone name for all 6 zones."""
        zones = [
            (1, "Entry Gate"), (2, "Scaffold Zone"), (3, "Welding Zone"),
            (4, "Concrete Zone"), (5, "Loading Zone"), (6, "Material Yard"),
        ]
        for zone_id, name in zones:
            v = _make_violation(zone_id=zone_id, zone_name=name, missing=["helmet"])
            msg = build_alert_message(v)
            assert name in msg


class TestBuildScanSummary:
    """Tests for build_scan_summary_message()."""

    def test_no_violations(self) -> None:
        """No violations should return empty string."""
        assert build_scan_summary_message("Entry Gate", []) == ""

    def test_single_violation(self) -> None:
        """Single violation should return the individual alert message."""
        v = _make_violation(missing=["helmet"], severity="medium")
        msg = build_scan_summary_message("Entry Gate", [v])
        assert "Attention" in msg
        assert "Hard hat" in msg

    def test_multiple_violations(self) -> None:
        """Multiple violations should return a summary with count."""
        violations = [
            _make_violation(missing=["helmet"], severity="high"),
            _make_violation(missing=["vest"], severity="medium"),
        ]
        msg = build_scan_summary_message("Welding Zone", violations)
        assert "2 workers" in msg
        assert "Welding Zone" in msg

    def test_multiple_high_severity(self) -> None:
        """Multiple high-severity violations should mention high-risk."""
        violations = [
            _make_violation(missing=["helmet"], severity="high"),
            _make_violation(missing=["gloves"], severity="high"),
        ]
        msg = build_scan_summary_message("Welding Zone", violations)
        assert "high-risk" in msg
