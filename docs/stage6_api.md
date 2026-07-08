# Stage 6 — API Layer (FastAPI Routes)

## Overview

The API layer exposes the backend's detection, rules, analytics, TTS,
and reporting capabilities via REST endpoints. All routes are mounted
under `/api` and documented via OpenAPI at `/docs`.

## Endpoints

### Detection

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/zones` | List all 6 zone configurations |
| POST | `/api/scan` | Upload image + zone_id → run full pipeline |

### Analytics

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/metrics` | Summary metrics (totals, compliance, per-zone/PPE) |
| GET | `/api/kpi` | KPI card data (scans, violations, compliance, most unsafe) |
| GET | `/api/events` | Recent events (filterable by type, paginated) |
| GET | `/api/charts/violations-per-zone` | Bar chart data (all 6 zones) |
| GET | `/api/charts/violations-per-ppe` | Pie chart data (per PPE type) |
| GET | `/api/charts/timeline` | Timeline chart data (chronological) |
| GET | `/api/hotspots` | Zone hotspot ranking (top-N) |
| GET | `/api/export/csv` | Download all events as CSV |
| GET | `/api/export/summary-csv` | Download per-zone summary as CSV |
| POST | `/api/clear` | Clear session event log |

### Alerts

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/tts` | Text → MP3 audio bytes (content-type: audio/mpeg) |

### Reports

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/report` | Generate PDF safety report (placeholder until Stage 8) |

### Health

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check (returns `{"status": "ok"}`) |

## Request/Response Schemas

### POST /api/scan

**Request:** multipart/form-data
- `zone_id`: int (1-6)
- `image`: file (JPEG/PNG)

**Response:** `ScanResponse`
```json
{
  "zone_id": 1,
  "zone_name": "Entry Gate",
  "detections": [
    {"class_name": "person", "confidence": 0.95, "bbox": [100, 100, 300, 600]}
  ],
  "violations": [
    {"zone_id": 1, "zone_name": "Entry Gate", "person_bbox": [...],
     "missing_ppe": ["helmet"], "severity": "medium", "timestamp": "..."}
  ],
  "tts_message": "Attention, Entry Gate. Hard hat is required.",
  "tts_audio_available": true,
  "detection_count": 2,
  "violation_count": 1
}
```

### POST /api/tts

**Request:** application/json
```json
{"message": "Attention, Entry Gate. Hard hat is required."}
```

**Response:** audio/mpeg (raw MP3 bytes)

## Session Handling

The API uses a singleton `EventLogger` — one session per backend
process. No session IDs are passed in requests. The "Clear Session"
button calls `POST /api/clear` to reset the log.

## Pipeline Architecture

`POST /api/scan` calls `run_zone_pipeline()` which orchestrates:
1. Load image bytes
2. Run YOLOv8 detection (Predictor)
3. Check zone compliance (violation_engine)
4. Log scan + violations (EventLogger)
5. Build TTS message (message_builder)
6. Return structured result

## Test Coverage

21 tests covering all endpoints:

| Category | Tests | Endpoints |
|----------|-------|-----------|
| Health | 1 | GET /health |
| Zones | 1 | GET /api/zones |
| Scan | 3 | POST /api/scan (invalid zone, empty image, success) |
| Metrics | 10 | GET /api/metrics, /kpi, /events, /charts/*, /hotspots, /export/*, /clear |
| TTS | 3 | POST /api/tts (success, empty, failure) |
| Report | 2 | GET /api/report (default, with site_name) |

## Files

- `backend/src/api/schemas/models.py` — Pydantic models
- `backend/src/api/pipeline.py` — pipeline orchestrator
- `backend/src/api/routes/detection.py` — scan + zones
- `backend/src/api/routes/analytics.py` — metrics + charts + export
- `backend/src/api/routes/alerts.py` — TTS
- `backend/src/api/routes/reports.py` — PDF report
- `backend/src/api/main.py` — FastAPI app, router mounting
- `backend/tests/test_api.py` — 21 endpoint tests
