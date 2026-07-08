# Stage 9 — Integration & End-to-End Testing

## Overview

This stage verifies the full pipeline works end-to-end: image upload →
YOLOv8 detection → zone compliance rules → event logging → TTS alert →
dashboard metrics → PDF report. Integration tests use mock detections
(no model weights required) to test the orchestration.

## Pipeline Flow

```
Image Upload → Predictor.predict() → check_compliance() → EventLogger.log_scan()
    → build_scan_summary_message() → Return ScanResponse
    → Frontend: metrics refetch, charts update, TTS plays
    → PDF: generate_daily_report() from event log
```

## Test Coverage

11 integration tests covering:

| Test | Scenario |
|------|----------|
| test_zone1_compliant_scan | Zone 1: person + helmet + vest → 0 violations |
| test_zone3_violations_generated | Zone 3: missing gloves + vest → 2 violations, high severity |
| test_zone3_tts_message_generated | Violations produce TTS alert message |
| test_six_zone_scan_metrics | All 6 zones scanned → correct totals + compliance rate |
| test_six_zone_zone_stats | Per-zone breakdown correct |
| test_pdf_after_six_scans | PDF generates from 6-scan session |
| test_pdf_empty_log | Empty log still produces valid PDF |
| test_missing_model_file | Missing model → FileNotFoundError |
| test_empty_event_log_pdf | Empty log → "No violations detected" |
| test_tts_unavailable_degrades_gracefully | TTS failure → text still in result |
| test_full_flow | Complete: 6 scans → metrics → PDF → CSV |

## Error Handling

| Error | Handling |
|-------|----------|
| Missing model file | 500 with descriptive message |
| Corrupt image upload | 400 "Empty image file" |
| TTS library unavailable | Alert text logged, no crash |
| Empty event log | PDF generates with "No violations detected today" |
| Invalid zone_id | 400 "Invalid zone_id" |

## Demo Script

`scripts/run_demo.py` simulates a user uploading images to all 6 zones:

1. Checks backend health
2. Clears session
3. Scans all 6 zones with sample images
4. Prints detections, violations, TTS messages
5. Fetches metrics, KPIs, hotspots
6. Generates PDF report
7. Exports CSV

Usage:
```bash
# Terminal 1: Start backend
python -m uvicorn backend.src.api.main:app --port 8000

# Terminal 2: Run demo
python scripts/run_demo.py
```

## Full Test Suite

All 154 tests across all stages pass:
- Stage 0: health + settings (10 tests)
- Stage 2: predictor + dataset loader (9 tests)
- Stage 3: violation engine (28 tests)
- Stage 4: event logger + metrics (38 tests)
- Stage 5: message builder + TTS engine (21 tests)
- Stage 6: API endpoints (21 tests)
- Stage 8: PDF generator + summary + recommendations (16 tests)
- Stage 9: integration (11 tests)

## Files

- `backend/tests/test_integration.py` — 11 integration tests
- `scripts/run_demo.py` — demo script
