# Stage 3 — Zone Rule Engine

## Overview

The rule engine converts raw YOLOv8 detections into PPE compliance
violations per zone. It is implemented as **pure functions** — no side
effects, no I/O. Given a list of detections and a zone ID, it returns a
list of `Violation` objects.

## PPE-to-Person Association: Containment Logic

The core challenge is determining which PPE items belong to which person.
We use **bbox center containment**:

1. For each PPE detection, compute its bounding box center point:
   `center = ((x1+x2)/2, (y1+y2)/2)`
2. Check if that center falls **inside** a person's bounding box:
   `x1 <= center_x <= x2 and y1 <= center_y <= y2`
3. If yes, the PPE is associated with that person.
4. A PPE item is assigned to the **first matching person only** (no
   sharing).

### Why Containment (not center distance)?

- **Crowded scenes**: Nearest-center-distance misattributes PPE when
  persons are close together. Containment naturally handles this — a
  helmet's center is above the person's head, which is still inside
  their bbox.
- **Simplicity**: No distance threshold to tune.
- **Robustness**: Works for helmets (above head), vests (on torso),
  gloves (on hands) — all typically inside the person bbox.

### Edge Cases

- **PPE outside any person bbox**: The PPE is not associated with anyone.
  If a person is missing that PPE, they get a violation.
- **Multiple PPE of same type on one person**: Only the first is
  associated (set deduplication). This is fine — we only care about
  presence, not count.
- **PPE on the bbox edge**: Inclusive bounds (`<=`), so edge-touching
  counts as inside.

## Severity Assignment

| Condition | Severity |
|-----------|----------|
| Welding Zone (zone 3) — any violation | `high` |
| 2+ missing PPE items (any zone) | `high` |
| 1 missing PPE item (non-welding zone) | `medium` |
| 0 missing (shouldn't produce a violation) | `low` |

### Rationale

- **Welding Zone is high-risk** (burns, UV radiation) — any missing PPE
  there is immediately critical.
- **Multiple missing items** indicates a more severe negligence than a
  single missing item.
- **Single missing item** in a standard zone is a medium-priority
  alert.

## Zone-PPE Matrix

| Zone | Name | Required PPE | High-Risk? |
|------|------|-------------|------------|
| 1 | Entry Gate | helmet, vest | No |
| 2 | Scaffold Zone | helmet, vest | No |
| 3 | Welding Zone | helmet, gloves, vest | **Yes** |
| 4 | Concrete Zone | helmet, vest | No |
| 5 | Loading Zone | helmet, vest | No |
| 6 | Material Yard | helmet, vest | No |

## Violation Data Model

```python
@dataclass
class Violation:
    zone_id: int
    zone_name: str
    person_bbox: tuple[int, int, int, int]  # [x1, y1, x2, y2]
    missing_ppe: list[str]                   # e.g. ["helmet", "vest"]
    severity: str                            # "high", "medium", "low"
    timestamp: str                           # ISO 8601, auto-generated
```

The `to_dict()` method converts to a JSON-serializable dict for API
responses and event logging.

## Test Coverage

28 tests covering all 6 required scenarios plus edge cases:

| Scenario | Tests | Status |
|----------|-------|--------|
| Person + helmet + vest → no violations | 2 | ✅ |
| Person + no helmet → helmet violation | 2 | ✅ |
| Person + no helmet + no vest → two violations | 1 | ✅ |
| Welding zone without gloves → gloves violation | 2 | ✅ |
| No person → no violations | 2 | ✅ |
| Two persons, mixed compliance | 3 | ✅ |
| Containment logic (bbox center, is_inside) | 6 | ✅ |
| Severity assignment | 4 | ✅ |
| Zone config loading | 4 | ✅ |
| Violation dataclass | 2 | ✅ |

## Files

- `backend/src/rules/zone_config.py` — zone loader (wraps `config/zones.py`)
- `backend/src/rules/models.py` — `Violation` dataclass, `Detection` type alias
- `backend/src/rules/violation_engine.py` — `check_compliance()` pure function
- `backend/tests/test_violation_engine.py` — 28 unit tests
