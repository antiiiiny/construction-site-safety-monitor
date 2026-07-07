# Stage 4 — Event Logging & Analytics

## Overview

The analytics module stores violation events and scan records in memory,
aggregates them into dashboard metrics, identifies hotspot zones, and
exports data to CSV. All data is session-scoped — no database, no
persistence beyond the backend process lifetime.

## Event Schema

### Violation Event

```json
{
  "type": "violation",
  "timestamp": "2026-07-07T12:34:56.789+00:00",
  "zone_id": 3,
  "zone_name": "Welding Zone",
  "person_bbox": [100, 100, 300, 600],
  "missing_ppe": ["helmet", "gloves"],
  "severity": "high",
  "session_id": "uuid-string"
}
```

### Scan Event

```json
{
  "type": "scan",
  "timestamp": "2026-07-07T12:34:56.789+00:00",
  "zone_id": 1,
  "detection_count": 5,
  "violation_count": 1,
  "detected_classes": ["person", "helmet", "vest"],
  "session_id": "uuid-string"
}
```

## Metrics Formulas

| Metric | Formula |
|--------|---------|
| Compliance Rate | (scans without violations) / (total scans) |
| Violation Rate | violations / scans (per zone) |
| Most Unsafe Zone | Zone with highest violation count |
| Hotspot Rank | Sorted by violation count (desc), then violation rate (desc) |

## Session Lifecycle

1. **Creation**: `EventLogger()` auto-generates a UUID session ID
2. **Logging**: `log_scan()` and `log_violation()` append events
3. **Querying**: `get_summary()`, `get_zone_stats()`, `get_all_events()`
4. **Export**: `export_events_csv()`, `export_summary_csv()` → CSV bytes
5. **Clear**: `clear()` wipes all events (used by "Clear Session" button)

**No persistence**: All data is lost on backend restart. This is
intentional for a demo/capstone project. Documented in README.

## Modules

### `event_logger.py` — `EventLogger` class

- `log_violation(violation)` — append a violation event
- `log_scan(zone_id, detections, violations)` — append a scan + its violations
- `get_all_events()` — all events (scans + violations) in order
- `get_violations()` — only violation events
- `get_scans()` — only scan events
- `get_zone_stats()` — per-zone breakdown (scans, violations, PPE counts, severity)
- `get_summary()` — overall metrics (totals, compliance rate, per-zone, per-PPE, severity)
- `clear()` — wipe all events

### `metrics.py` — Chart-ready aggregation functions

- `get_violations_per_zone()` — bar chart data (all 6 zones)
- `get_violations_per_ppe()` — pie chart data
- `get_severity_breakdown()` — high/medium/low counts
- `get_violation_timeline()` — chronological violation list
- `get_compliance_rate()` — float 0.0–1.0
- `get_kpi_cards()` — dashboard KPI card data

### `hotspot_analysis.py` — Zone risk ranking

- `get_hotspots(top_n=3)` — top-N zones by violation count
- `get_zone_risk_level(zone_id)` — 'critical', 'high', 'moderate', 'low', 'none'

### `export_csv.py` — CSV export

- `export_events_csv()` — all events as CSV bytes
- `export_summary_csv()` — per-zone summary as CSV bytes

## Test Coverage

38 tests across two test files:

| File | Tests | Coverage |
|------|-------|----------|
| `test_event_logger.py` | 18 | Basic logging, zone stats, summary, clear, mock session |
| `test_metrics.py` | 20 | Bar/pie/timeline data, KPIs, hotspots, risk levels, CSV export |

Mock session: 10 scans, 10 violations across all 6 zones — verifies
correct counts, compliance rate, hotspot ranking, and CSV output.

## Files

- `backend/src/analytics/event_logger.py`
- `backend/src/analytics/metrics.py`
- `backend/src/analytics/hotspot_analysis.py`
- `backend/src/analytics/export_csv.py`
- `backend/tests/test_event_logger.py`
- `backend/tests/test_metrics.py`
