"""Tests for the zone rule engine (violation_engine.py).

Tests cover the 6 required scenarios from STAGES.md:
  1. Person + helmet + vest → no violations
  2. Person + no helmet → helmet violation
  3. Person + no helmet + no vest → two violations
  4. Person in welding zone without gloves → gloves violation
  5. No person detected → no violations
  6. Two persons, one compliant, one not → correct per-person attribution

Additional tests:
  - Containment logic (PPE center inside person bbox)
  - Severity assignment (high/medium/low)
  - Zone config loading
  - Violation dataclass to_dict()
"""

from __future__ import annotations

from backend.src.rules.models import Violation
from backend.src.rules.violation_engine import (
    _associate_ppe_to_persons,
    _bbox_center,
    _determine_severity,
    _is_inside,
    check_compliance,
)
from backend.src.rules.zone_config import get_required_ppe, get_zone

# ---- Helper: create mock detections ----


def make_person(x1: int, y1: int, x2: int, y2: int) -> dict:
    """Create a person detection dict."""
    return {
        "class_name": "person",
        "confidence": 0.95,
        "bbox": [x1, y1, x2, y2],
    }


def make_ppe(ppe_type: str, x1: int, y1: int, x2: int, y2: int) -> dict:
    """Create a PPE detection dict."""
    return {
        "class_name": ppe_type,
        "confidence": 0.85,
        "bbox": [x1, y1, x2, y2],
    }


# ---- Test Scenario 1: Fully compliant person ----


class TestCompliantPerson:
    """Person with all required PPE → no violations."""

    def test_person_helmet_vest_no_violations(self) -> None:
        """Zone 1 (Entry Gate): person + helmet + vest → no violations."""
        # Person bbox: [100, 100, 300, 600]
        # Helmet center should be inside person bbox (on their head)
        # Vest center should be inside person bbox (on their torso)
        detections = [
            make_person(100, 100, 300, 600),
            make_ppe("helmet", 150, 80, 250, 180),    # center (200, 130) inside
            make_ppe("vest", 130, 250, 270, 450),     # center (200, 350) inside
        ]
        violations = check_compliance(detections, zone_id=1)
        assert len(violations) == 0

    def test_person_helmet_vest_gloves_no_violations(self) -> None:
        """Zone 3 (Welding): person + helmet + vest + gloves → no violations."""
        detections = [
            make_person(100, 100, 300, 600),
            make_ppe("helmet", 150, 80, 250, 180),
            make_ppe("vest", 130, 250, 270, 450),
            make_ppe("gloves", 140, 500, 200, 560),
        ]
        violations = check_compliance(detections, zone_id=3)
        assert len(violations) == 0


# ---- Test Scenario 2: Missing helmet ----


class TestMissingHelmet:
    """Person missing helmet → helmet violation."""

    def test_person_no_helmet(self) -> None:
        """Zone 1: person + vest (no helmet) → helmet violation."""
        detections = [
            make_person(100, 100, 300, 600),
            make_ppe("vest", 130, 250, 270, 450),
        ]
        violations = check_compliance(detections, zone_id=1)
        assert len(violations) == 1
        assert "helmet" in violations[0].missing_ppe
        assert "vest" not in violations[0].missing_ppe
        assert violations[0].severity == "medium"  # 1 missing, non-welding

    def test_helmet_outside_person_bbox_not_associated(self) -> None:
        """Helmet detected but its center is outside the person bbox → violation."""
        detections = [
            make_person(100, 100, 300, 600),
            # Helmet center at (500, 130) — outside person bbox [100,100,300,600]
            make_ppe("helmet", 450, 80, 550, 180),
            make_ppe("vest", 130, 250, 270, 450),
        ]
        violations = check_compliance(detections, zone_id=1)
        assert len(violations) == 1
        assert "helmet" in violations[0].missing_ppe


# ---- Test Scenario 3: Missing helmet and vest ----


class TestMultipleMissing:
    """Person missing multiple PPE items."""

    def test_person_no_helmet_no_vest(self) -> None:
        """Zone 1: person alone (no helmet, no vest) → two violations."""
        detections = [
            make_person(100, 100, 300, 600),
        ]
        violations = check_compliance(detections, zone_id=1)
        assert len(violations) == 1  # One violation object per person
        assert len(violations[0].missing_ppe) == 2
        assert "helmet" in violations[0].missing_ppe
        assert "vest" in violations[0].missing_ppe
        assert violations[0].severity == "high"  # 2+ missing


# ---- Test Scenario 4: Welding zone gloves violation ----


class TestWeldingZoneGloves:
    """Person in welding zone without gloves → gloves violation (high severity)."""

    def test_welding_zone_missing_gloves(self) -> None:
        """Zone 3: person + helmet + vest (no gloves) → gloves violation, high."""
        detections = [
            make_person(100, 100, 300, 600),
            make_ppe("helmet", 150, 80, 250, 180),
            make_ppe("vest", 130, 250, 270, 450),
        ]
        violations = check_compliance(detections, zone_id=3)
        assert len(violations) == 1
        assert "gloves" in violations[0].missing_ppe
        assert violations[0].severity == "high"  # Welding zone = always high

    def test_welding_zone_all_missing(self) -> None:
        """Zone 3: person alone → all 3 missing, high severity."""
        detections = [
            make_person(100, 100, 300, 600),
        ]
        violations = check_compliance(detections, zone_id=3)
        assert len(violations) == 1
        assert len(violations[0].missing_ppe) == 3
        assert violations[0].severity == "high"


# ---- Test Scenario 5: No person detected ----


class TestNoPerson:
    """No person in detections → no violations."""

    def test_no_person_no_violations(self) -> None:
        """No person detected → no violations, even if PPE is present."""
        detections = [
            make_ppe("helmet", 150, 80, 250, 180),
            make_ppe("vest", 130, 250, 270, 450),
        ]
        violations = check_compliance(detections, zone_id=1)
        assert len(violations) == 0

    def test_empty_detections(self) -> None:
        """Empty detections list → no violations."""
        violations = check_compliance([], zone_id=1)
        assert len(violations) == 0


# ---- Test Scenario 6: Multiple persons, mixed compliance ----


class TestMultiplePersons:
    """Two persons — one compliant, one not → correct per-person attribution."""

    def test_two_persons_one_compliant(self) -> None:
        """Two persons: one has helmet+vest, other has nothing."""
        # Person 1: [100, 100, 300, 600] — has helmet and vest
        # Person 2: [400, 100, 600, 600] — no PPE
        detections = [
            make_person(100, 100, 300, 600),
            make_person(400, 100, 600, 600),
            # Helmet and vest for person 1 only
            make_ppe("helmet", 150, 80, 250, 180),
            make_ppe("vest", 130, 250, 270, 450),
        ]
        violations = check_compliance(detections, zone_id=1)
        assert len(violations) == 1  # Only person 2 has a violation
        assert "helmet" in violations[0].missing_ppe
        assert "vest" in violations[0].missing_ppe

    def test_two_persons_both_non_compliant(self) -> None:
        """Two persons, both missing PPE → two violations."""
        detections = [
            make_person(100, 100, 300, 600),
            make_person(400, 100, 600, 600),
        ]
        violations = check_compliance(detections, zone_id=1)
        assert len(violations) == 2

    def test_two_persons_both_compliant(self) -> None:
        """Two persons, both with all PPE → no violations."""
        detections = [
            make_person(100, 100, 300, 600),
            make_person(400, 100, 600, 600),
            # PPE for person 1
            make_ppe("helmet", 150, 80, 250, 180),
            make_ppe("vest", 130, 250, 270, 450),
            # PPE for person 2
            make_ppe("helmet", 450, 80, 550, 180),
            make_ppe("vest", 430, 250, 570, 450),
        ]
        violations = check_compliance(detections, zone_id=1)
        assert len(violations) == 0


# ---- Containment logic tests ----


class TestContainmentLogic:
    """Tests for the bbox center containment logic."""

    def test_bbox_center(self) -> None:
        """Center of [0, 0, 100, 100] should be (50, 50)."""
        assert _bbox_center([0, 0, 100, 100]) == (50.0, 50.0)

    def test_is_inside_true(self) -> None:
        """Point (50, 50) is inside [0, 0, 100, 100]."""
        assert _is_inside((50, 50), [0, 0, 100, 100]) is True

    def test_is_inside_false(self) -> None:
        """Point (150, 50) is NOT inside [0, 0, 100, 100]."""
        assert _is_inside((150, 50), [0, 0, 100, 100]) is False

    def test_is_inside_edge(self) -> None:
        """Point on the edge should be considered inside (inclusive)."""
        assert _is_inside((0, 0), [0, 0, 100, 100]) is True
        assert _is_inside((100, 100), [0, 0, 100, 100]) is True

    def test_associate_ppe_to_persons(self) -> None:
        """PPE center inside person bbox → associated."""
        persons = [make_person(100, 100, 300, 600)]
        ppe_items = [
            make_ppe("helmet", 150, 80, 250, 180),  # center (200, 130) inside
            make_ppe("vest", 130, 250, 270, 450),   # center (200, 350) inside
        ]
        result = _associate_ppe_to_persons(persons, ppe_items)
        assert result[0] == {"helmet", "vest"}

    def test_associate_ppe_outside_not_associated(self) -> None:
        """PPE center outside person bbox → not associated."""
        persons = [make_person(100, 100, 300, 600)]
        ppe_items = [
            make_ppe("helmet", 450, 80, 550, 180),  # center (500, 130) outside
        ]
        result = _associate_ppe_to_persons(persons, ppe_items)
        assert result[0] == set()


# ---- Severity tests ----


class TestSeverity:
    """Tests for severity assignment."""

    def test_welding_zone_always_high(self) -> None:
        """Zone 3 (Welding) violations are always 'high'."""
        assert _determine_severity(3, 1) == "high"
        assert _determine_severity(3, 3) == "high"

    def test_two_missing_is_high(self) -> None:
        """2+ missing PPE in non-welding zone → 'high'."""
        assert _determine_severity(1, 2) == "high"
        assert _determine_severity(5, 3) == "high"

    def test_one_missing_is_medium(self) -> None:
        """1 missing PPE in non-welding zone → 'medium'."""
        assert _determine_severity(1, 1) == "medium"
        assert _determine_severity(4, 1) == "medium"

    def test_zero_missing_is_low(self) -> None:
        """0 missing PPE → 'low' (shouldn't happen in practice)."""
        assert _determine_severity(1, 0) == "low"


# ---- Zone config tests ----


class TestZoneConfig:
    """Tests for zone configuration loading."""

    def test_get_zone_valid(self) -> None:
        """get_zone should return the correct zone for valid IDs."""
        zone = get_zone(1)
        assert zone.zone_id == 1
        assert zone.name == "Entry Gate"

    def test_get_zone_welding(self) -> None:
        """Zone 3 should be the Welding Zone with gloves required."""
        zone = get_zone(3)
        assert zone.name == "Welding Zone"
        assert "gloves" in zone.required_ppe

    def test_get_zone_invalid(self) -> None:
        """get_zone should raise ValueError for invalid IDs."""
        import pytest

        with pytest.raises(ValueError):
            get_zone(99)

    def test_get_required_ppe(self) -> None:
        """get_required_ppe should return the correct PPE list."""
        ppe = get_required_ppe(1)
        assert "helmet" in ppe
        assert "vest" in ppe
        assert "gloves" not in ppe  # Zone 1 doesn't require gloves


# ---- Violation dataclass tests ----


class TestViolationDataclass:
    """Tests for the Violation dataclass."""

    def test_violation_to_dict(self) -> None:
        """to_dict should return a serializable dict."""
        v = Violation(
            zone_id=1,
            zone_name="Entry Gate",
            person_bbox=(100, 100, 300, 600),
            missing_ppe=["helmet"],
            severity="medium",
        )
        d = v.to_dict()
        assert d["zone_id"] == 1
        assert d["zone_name"] == "Entry Gate"
        assert d["person_bbox"] == [100, 100, 300, 600]
        assert d["missing_ppe"] == ["helmet"]
        assert d["severity"] == "medium"
        assert "timestamp" in d

    def test_violation_timestamp_auto(self) -> None:
        """Timestamp should be auto-generated if not provided."""
        v = Violation(
            zone_id=1,
            zone_name="Entry Gate",
            person_bbox=(100, 100, 300, 600),
            missing_ppe=["helmet"],
            severity="medium",
        )
        assert v.timestamp is not None
        assert "T" in v.timestamp  # ISO format
