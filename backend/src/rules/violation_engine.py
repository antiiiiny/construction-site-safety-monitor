"""Zone compliance violation engine.

Core logic that converts raw YOLOv8 detections into PPE compliance
violations per zone. This is a pure-function module — no side effects,
no I/O. Given detections and a zone ID, it returns a list of violations.

Association logic: PPE bbox center must fall inside the person bbox
(containment). This is more robust than nearest-center-distance in
crowded scenes.

Severity assignment:
  - 'high': Welding Zone (zone 3) OR 2+ missing PPE items
  - 'medium': 1 missing PPE item in a non-welding zone
  - 'low': informational only (currently unused, reserved for future)

Usage:
    from backend.src.rules.violation_engine import check_compliance
    violations = check_compliance(detections, zone_id=3)
    for v in violations:
        print(f"{v.zone_name}: missing {v.missing_ppe} ({v.severity})")
"""

from __future__ import annotations

from backend.src.rules.models import Detection, Violation
from backend.src.rules.zone_config import get_zone

# Zone 3 (Welding Zone) is considered high-risk — any violation there
# is automatically 'high' severity.
HIGH_RISK_ZONES = {3}


def _bbox_center(bbox: list[int] | tuple[int, int, int, int]) -> tuple[float, float]:
    """Calculate the center point of a bounding box.

    Args:
        bbox: [x1, y1, x2, y2] coordinates.

    Returns:
        (center_x, center_y) as floats.
    """
    x1, y1, x2, y2 = bbox
    return ((x1 + x2) / 2.0, (y1 + y2) / 2.0)


def _is_inside(
    point: tuple[float, float],
    bbox: list[int] | tuple[int, int, int, int],
) -> bool:
    """Check if a 2D point falls inside a bounding box.

    Args:
        point: (x, y) coordinates.
        bbox: [x1, y1, x2, y2] — the containing box.

    Returns:
        True if point is inside the bbox (inclusive of edges).
    """
    px, py = point
    x1, y1, x2, y2 = bbox
    return x1 <= px <= x2 and y1 <= py <= y2


def _associate_ppe_to_persons(
    persons: list[Detection],
    ppe_items: list[Detection],
) -> dict[int, set[str]]:
    """Associate PPE detections with persons using containment logic.

    For each PPE item, its bbox center is checked against each person's
    bbox. If the center falls inside, the PPE is associated with that
    person. A PPE item can be associated with at most one person (the
    first match).

    Args:
        persons: List of detection dicts with class_name == 'person'.
        ppe_items: List of detection dicts with class_name in
            {'helmet', 'vest', 'gloves'}.

    Returns:
        Dict mapping person index (in the persons list) to a set of
        PPE class names associated with that person.
    """
    # Initialize: each person has an empty set of PPE
    person_ppe: dict[int, set[str]] = {i: set() for i in range(len(persons))}

    for ppe in ppe_items:
        ppe_center = _bbox_center(ppe["bbox"])  # type: ignore[index]
        ppe_class = ppe["class_name"]

        # Find the first person whose bbox contains this PPE's center
        for i, person in enumerate(persons):
            if _is_inside(ppe_center, person["bbox"]):  # type: ignore[index]
                person_ppe[i].add(ppe_class)
                break  # PPE assigned to first matching person only

    return person_ppe


def _determine_severity(
    zone_id: int,
    missing_count: int,
) -> str:
    """Determine the severity level of a violation.

    Args:
        zone_id: The zone where the violation occurred.
        missing_count: Number of missing PPE items.

    Returns:
        'high', 'medium', or 'low'.
    """
    if zone_id in HIGH_RISK_ZONES:
        return "high"
    if missing_count >= 2:
        return "high"
    if missing_count == 1:
        return "medium"
    return "low"


def check_compliance(
    detections: list[Detection],
    zone_id: int,
) -> list[Violation]:
    """Check PPE compliance for a set of detections in a specific zone.

    This is the main entry point for the rule engine. Given detections
    from one camera image and a zone ID, it returns a list of violations
    (missing PPE per person).

    A violation is created when:
      1. A 'person' is detected.
      2. A required PPE item for that zone is NOT detected on that person
         (i.e., no PPE bbox of that type is contained within the person's
         bbox).

    Args:
        detections: List of detection dicts from the predictor:
            {"class_name": str, "confidence": float, "bbox": [x1,y1,x2,y2]}
        zone_id: Integer zone identifier (1-6).

    Returns:
        List of Violation objects, one per non-compliant person.
        Compliant persons (all required PPE present) produce no violation.
    """
    zone = get_zone(zone_id)
    required_ppe = set(zone.required_ppe)

    # Separate persons from PPE items
    persons: list[Detection] = []
    ppe_items: list[Detection] = []

    for det in detections:
        class_name = det.get("class_name", "")
        if class_name == "person":
            persons.append(det)
        elif class_name in ("helmet", "vest", "gloves"):
            ppe_items.append(det)

    # No persons detected → no violations possible
    if not persons:
        return []

    # Associate PPE to persons via containment
    person_ppe = _associate_ppe_to_persons(persons, ppe_items)

    # Check each person for missing PPE
    violations: list[Violation] = []
    for i, person in enumerate(persons):
        detected_ppe = person_ppe[i]
        missing = required_ppe - detected_ppe

        if missing:
            missing_list = sorted(missing)  # Deterministic order
            severity = _determine_severity(zone_id, len(missing_list))

            violations.append(Violation(
                zone_id=zone_id,
                zone_name=zone.name,
                person_bbox=tuple(person["bbox"]),  # type: ignore[index]
                missing_ppe=missing_list,
                severity=severity,
            ))

    return violations
