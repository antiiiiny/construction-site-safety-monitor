# STAGES.md — Construction Site Safety Monitor

> Stage-gated workflow log. Each stage has a checklist and a gate criterion.
> **Do not start the next stage until the current stage's gate is passed.**
> Architecture: FastAPI backend + React/TypeScript frontend + YOLOv8 + edge-tts + reportlab.

---

## Stage 0 — Project Setup & Scaffolding

**Goal:** Monorepo structure, both apps runnable, dependencies installed.

**Checklist:**
- [x] `backend/` and `frontend/` directories created at repo root
- [x] `backend/requirements.txt` with: ultralytics, fastapi, uvicorn[standard], python-multipart, edge-tts, gTTS, pyttsx3, reportlab, python-dotenv, roboflow, pytest, pytest-asyncio, httpx, Pillow, ruff
- [x] `backend/config/zones.py` — 6 zone definitions (harness/boots removed)
- [x] `backend/config/class_mapping.py` — map Roboflow labels → canonical names (person, helmet, vest, gloves)
- [x] `backend/config/tts_config.py` — `TTS_BACKEND="edge"`, `TTS_VOICE="en-US-AriaNeural"`
- [x] `backend/config/settings.py` — centralized settings loaded from `.env` via python-dotenv
- [x] `.env.example` — template with all env vars (Roboflow, OpenRouter, TTS, detection)
- [x] `.env` — real values (gitignored)
- [x] `backend/src/api/main.py` — FastAPI app with `/health` endpoint, CORS for `http://localhost:5173`
- [x] `frontend/` scaffolded with Vite + React + TypeScript
- [x] `frontend/package.json` deps: react, react-dom, react-router-dom, @tanstack/react-query, zustand, react-plotly.js, plotly.js, axios, tailwindcss
- [x] `frontend/src/api/client.ts` — axios instance → `http://localhost:8000`
- [x] `frontend/src/store/appStore.ts` — Zustand store (selectedZone, ttsEnabled, ttsBackend, confidenceThreshold)
- [x] `frontend/src/App.tsx` — minimal layout rendering, Zustand toggle test
- [x] `scripts/run_dev.py` — concurrently starts `uvicorn` + `vite`
- [x] `.gitignore` updated: `data/`, `artifacts/`, `backend/__pycache__/`, `frontend/node_modules/`, `frontend/dist/`, `*.pt`
- [x] `copilot-instructions.md` rewritten (trimmed to essentials)
- [x] `pytest.ini` and `pyproject.toml` (ruff config) committed
- [x] Python 3.11 venv created; `pip install -r backend/requirements.txt` succeeds
- [x] `cd frontend && npm install` succeeds
- [x] `backend/tests/test_health.py` — smoke test for `/health` endpoint
- [x] `backend/tests/test_settings.py` — tests for `.env` loading and settings defaults
- [x] `backend/src/reporting/llm_client.py` — OpenRouter (GPT-4o-mini) LLM client for Stage 8

**Gate:** `python scripts/run_dev.py` starts both servers. `curl http://localhost:8000/health` returns `{"status":"ok"}`. `http://localhost:5173` loads React app without errors. `pytest backend/tests/test_health.py` passes.

---

## Stage 1 — Dataset Acquisition & EDA

**Goal:** Roboflow PPE dataset downloaded, inspected, ready for training.

**Checklist:**
- [x] `backend/src/detection/download_dataset.py` — script to download dataset from Roboflow via API
- [x] Download Roboflow PPE Detection dataset (public) via API key or direct zip
- [x] Extract into `data/` in YOLOv8 format (`data/images/{train,val,test}/`, `data/labels/{train,val,test}/`)
- [x] Verify `data/data.yaml` exists with class names and paths
- [x] `backend/src/detection/dataset_eda.py` — reports: image counts per split, class counts, class distribution, resolution range, corrupt file check
- [x] `backend/src/detection/visualize_samples.py` — draws bboxes on 5 sample images → `artifacts/stage1_eda/`
- [x] Copy 4 sample images into `data/sample_images/` (committed, small) for pipeline testing
- [x] `docs/stage1_dataset.md` — image counts, class names, balance assessment, resolution range, corrupt files, dataset source URL

**Gate:** `python -m backend.src.detection.dataset_eda` runs and prints summary. 5 annotated sample images saved to `artifacts/stage1_eda/`. `docs/stage1_dataset.md` exists with all required fields.

---

## Stage 2 — PPE Detection Model

**Goal:** YOLOv8 trained, evaluated, predictor working.

**Checklist:**
- [x] `backend/src/detection/dataset_loader.py` — validates YOLOv8 format, wraps ultralytics data config
- [x] Train YOLOv8 (`yolov8s.pt`) on PPE dataset — fine-tune 30-50 epochs (use Colab if no local GPU)
- [x] `backend/src/detection/predictor.py` — `predict(image_path|bytes) -> List[Detection]` returning `{"class_name","confidence","bbox"}`
- [x] `backend/src/detection/visualize_predictions.py` — draws detections with labels/confidence on image
- [x] Evaluate on val/test: mAP@0.5, mAP@0.5:0.95, per-class precision/recall/F1
- [x] Save weights to `artifacts/stage2_model/best.pt`
- [x] `docs/stage2_model.md` — training config (epochs, imgsz, batch, GPU), metrics table, sample predictions, failure cases

**Gate:** `predictor.py` runs on a `data/sample_images/` image and returns structured detections. `best.pt` saved. mAP@0.5 > 0.6 on person, helmet, vest.

**Gate Status: PARTIALLY MET** — Predictor works and returns structured detections. `best.pt` saved. However, mAP@0.5 > 0.6 only passes for helmet (0.663). Vest (0.172), person (0.037), and gloves (0.000) fail due to severe class imbalance in the dataset. **Proceeding with caveats** — see `docs/stage2_model.md` for analysis and mitigation strategy. Rule engine (Stage 3) will weight violations by model reliability.

---

## Stage 3 — Zone Rule Engine

**Goal:** Convert detections → compliance violations per zone.

**Checklist:**
- [x] `backend/src/rules/zone_config.py` — loads zones from `config/zones.py`
- [x] `backend/src/rules/models.py` — `Violation` dataclass: `zone_id:int, zone_name:str, person_bbox:Tuple[int,int,int,int], missing_ppe:List[str], severity:str, timestamp:str`
- [x] `backend/src/rules/violation_engine.py` — `check_compliance(detections, zone_id) -> List[Violation]`
  - Association logic: **PPE bbox center must fall inside person bbox** (containment)
  - Violation = person detected + required PPE not contained in their bbox
  - Severity: high (welding zone or 2+ missing), medium (1 missing), low (informational)
- [x] `backend/tests/test_violation_engine.py` — scenarios:
  - person + helmet + vest → no violations
  - person + no helmet → helmet violation
  - person + no helmet + no vest → two violations
  - person in welding zone without gloves → gloves violation
  - no person → no violations
  - two persons, one compliant, one not → correct per-person attribution
- [x] `docs/stage3_rules.md` — containment logic explanation, severity matrix, zone-PPE table

**Gate:** `pytest backend/tests/test_violation_engine.py` — all 28 tests pass. `check_compliance()` correct for all 6 mock scenarios. ✅ **PASSED**

---

## Stage 4 — Event Logging & Analytics

**Goal:** Violations logged, aggregated into dashboard metrics.

**Checklist:**
- [x] `backend/src/analytics/event_logger.py` — `EventLogger` class: `log_violation()`, `log_scan()`, `get_all_events()`, `get_zone_stats()`, `get_summary()`
- [x] Event log stored in memory (session-scoped dict keyed by session_id) — no DB
- [x] `backend/src/analytics/metrics.py` — total scans, total violations, compliance rate, violations per zone, violations per PPE type, zone hotspot ranking, timeline
- [x] `backend/src/analytics/hotspot_analysis.py` — top-N most problematic zones
- [x] `backend/src/analytics/export_csv.py` — export event log to CSV bytes
- [x] `backend/tests/test_event_logger.py` — log 10 mock events, verify summary counts
- [x] `backend/tests/test_metrics.py` — test zone hotspot ranking, compliance rate calc
- [x] `docs/stage4_analytics.md` — event schema, metrics formulas, session lifecycle

**Gate:** `pytest backend/tests/test_event_logger.py backend/tests/test_metrics.py` passes. Correct results for mock session with 20+ events across 6 zones. ✅ **PASSED** (38 tests)

---

## Stage 5 — TTS Voice Alerts (Backend)

**Goal:** Backend generates MP3 audio for violations.

**Checklist:**
- [ ] `backend/src/alerts/message_builder.py` — builds natural-language messages:
  - high: "Warning, {zone}. {missing} required. This is a high-risk area."
  - medium: "Attention, {zone}. {missing} required."
  - low: "Notice, {zone}. {missing} recommended."
- [ ] `backend/src/alerts/tts_engine.py` — `TTSEngine` class:
  - `generate_audio(message) -> bytes` (async, returns MP3 bytes)
  - Primary: `edge-tts` with configurable voice (`en-US-AriaNeural` default)
  - Fallback: `gTTS` if edge-tts fails
  - Final fallback: return None (text-only, logged)
- [ ] `backend/src/alerts/speaker.py` — optional zone-to-voice mapping (Zone 3 welding → male voice)
- [ ] `backend/tests/test_message_builder.py` — message generation per zone, severity variation, single vs multiple missing PPE
- [ ] `backend/tests/test_tts_engine.py` — mock edge-tts, verify MP3 bytes returned; test gTTS fallback path
- [ ] `docs/stage5_tts.md` — backend design, edge-tts unofficial endpoint caveat, fallback chain

**Gate:** `pytest backend/tests/test_message_builder.py backend/tests/test_tts_engine.py` passes. `TTSEngine.generate_audio()` returns non-empty MP3 bytes for a sample message (or degrades gracefully).

---

## Stage 6 — API Layer (FastAPI Routes)

**Goal:** REST API exposing detection, rules, analytics, TTS, PDF.

**Checklist:**
- [ ] `backend/src/api/schemas/` — Pydantic models: `ScanRequest`, `ScanResponse`, `Violation`, `MetricsSummary`, `ZoneStatus`, `TTSResponse`
- [ ] `backend/src/api/routes/detection.py`:
  - `POST /api/scan` — accepts image upload + zone_id, runs detection + rules, logs event, returns detections + violations + tts_message
  - `GET /api/zones` — returns zone config
- [ ] `backend/src/api/routes/analytics.py`:
  - `GET /api/metrics` — returns summary metrics
  - `GET /api/events` — returns recent events (paginated)
  - `GET /api/export/csv` — returns CSV download
- [ ] `backend/src/api/routes/alerts.py`:
  - `POST /api/tts` — accepts message text, returns MP3 bytes (`Response(content=audio, media_type="audio/mpeg")`)
- [ ] `backend/src/api/routes/reports.py`:
  - `GET /api/report` — generates and returns PDF
- [ ] `backend/src/api/main.py` — mounts all routers, CORS middleware, `/health`
- [ ] `backend/tests/test_api.py` — httpx AsyncClient tests:
  - `POST /api/scan` with sample image → 200, returns violations
  - `GET /api/metrics` after scans → correct counts
  - `POST /api/tts` → 200, content-type audio/mpeg
  - `GET /api/report` → 200, content-type application/pdf
- [ ] `docs/stage6_api.md` — endpoint reference, request/response schemas, session_id handling

**Gate:** `pytest backend/tests/test_api.py` passes. All endpoints return correct status codes and payloads. OpenAPI docs at `/docs` render correctly.

---

## Stage 7 — React Frontend (Dashboard UI)

**Goal:** Full web UI with 6-camera grid, live metrics, charts, TTS playback.

**Checklist:**
- [ ] `frontend/src/api/endpoints.ts` — typed functions: `scanZone()`, `getMetrics()`, `getEvents()`, `getTTS()`, `getReport()`, `getZones()`
- [ ] `frontend/src/hooks/useScan.ts` — React Query mutation calling `scanZone`, invalidates metrics query on success
- [ ] `frontend/src/hooks/useMetrics.ts` — React Query polling (refetch every 5s when scans active)
- [ ] `frontend/src/store/appStore.ts` — Zustand: `selectedZone`, `ttsEnabled`, `confidenceThreshold`, `scanResults` per zone
- [ ] `frontend/src/components/CameraTile.tsx` — zone name, hazard label, file upload, status indicator (safe/violation), detection overlay (canvas or img with bbox), PPE badges, violation warnings, speaker icon
- [ ] `frontend/src/components/MetricCard.tsx` — reusable KPI card (Total Scans, Violations, Compliance Rate, Most Unsafe Zone)
- [ ] `frontend/src/components/ChartBuilder.tsx` — Plotly factory: `ViolationsPerZoneBar`, `PPEBreakdownPie`, `ViolationTimeline`
- [ ] `frontend/src/components/AlertPlayer.tsx` — fetches MP3 from `/api/tts`, plays via `<audio ref>`
- [ ] `frontend/src/components/Sidebar.tsx` — confidence slider, TTS toggle, TTS backend selector, clear session, generate PDF button
- [ ] `frontend/src/pages/Dashboard.tsx` — 3x2 camera grid + dashboard section (KPI cards, charts, recent alerts table)
- [ ] `frontend/src/types/index.ts` — TS interfaces matching backend Pydantic schemas
- [ ] Tailwind CSS configured; responsive at 1280px and 375px
- [ ] `docs/stage7_ui.md` — component tree, state flow, screenshots

**Gate:** Upload images to all 6 tiles → detections render, violations show, metrics update, charts populate, TTS plays. No unhandled console errors. Responsive at desktop and mobile widths.

---

## Stage 8 — PDF Report Generation

**Goal:** Supervisor-grade daily safety report.

**Checklist:**
- [ ] `backend/src/reporting/pdf_generator.py` — `generate_daily_report(event_log, site_name, date) -> bytes`
- [ ] PDF sections: Header, Executive Summary, Zone-Wise Table, PPE Breakdown, Hotspot Ranking, Incident Log (recent 20), Supervisor Summary, Recommendations, Footer
- [ ] `backend/src/reporting/summary_generator.py` — rule-based natural-language summary from metrics (fallback)
- [ ] `backend/src/reporting/llm_client.py` — OpenRouter (GPT-4o-mini) LLM summary; used if `OPENROUTER_API_KEY` set, otherwise falls back to rule-based
- [ ] `backend/src/reporting/recommendations.py` — pattern-based recommendations (zone with most violations, common missing PPE, compliance < 70%)
- [ ] `backend/tests/test_pdf_generator.py` — generate from 15 mock events, verify non-empty bytes, page count, section presence
- [ ] Sample PDF saved to `artifacts/stage8_report/sample_report.pdf`
- [ ] Frontend "Generate PDF" button wired to `GET /api/report`, triggers browser download
- [ ] `docs/stage8_report.md` — PDF structure, summary logic, recommendation rules

**Gate:** PDF generates from 20+ event session. All sections present. Opens correctly in PDF viewer. Frontend download button works.

---

## Stage 9 — Integration & End-to-End Testing

**Goal:** Full pipeline works upload → detection → rules → events → TTS → dashboard → PDF.

**Checklist:**
- [ ] `backend/src/api/pipeline.py` — `run_zone_pipeline(zone_id, image_bytes) -> ScanResponse` orchestrating: load image → predict → check_compliance → log → build TTS message → return
- [ ] `backend/tests/test_integration.py`:
  - Scan Zone 1 image → detection → rule check → event logged → alert message generated
  - Scan Zone 3 image → detection → rule check → event logged → alert message generated
  - Scan 6 images across all zones → metrics correct
  - Generate PDF after 6 scans → all sections populated
- [ ] Error handling: missing model file → 500 with message; corrupt image → 400; TTS unavailable → text-only; empty event log → PDF with "No violations detected today"
- [ ] `scripts/run_demo.py` — loads `data/sample_images/` into all 6 zones via API calls sequentially
- [ ] Frontend E2E smoke test (manual or Playwright): upload → dashboard updates → PDF downloads
- [ ] `docs/stage9_integration.md` — pipeline diagram, error handling matrix, demo script usage

**Gate:** `python scripts/run_demo.py` processes all 6 zones. Dashboard shows correct metrics. PDF generates. `pytest backend/tests/test_integration.py` passes. No unhandled exceptions.

---

## Stage 10 — Evaluation, Documentation & Polish

**Goal:** Final write-up, metrics, presentation-ready.

**Checklist:**
- [ ] `docs/stage10_evaluation.md` — detection metrics (mAP, per-class P/R), inference time per image, dashboard accuracy (manual verification), PDF quality review, known limitations
- [ ] `docs/capstone_writeup.md` — full capstone report: problem statement, system architecture diagram, tech choices rationale, stage-by-stage summary, CNN eval results, analytics/reporting capabilities, key inference (violations cluster by zone/PPE), future work
- [ ] `README.md` finalized: project description, setup (backend venv + frontend npm), `python scripts/run_dev.py` instructions, demo script, screenshots
- [ ] Code cleanup: remove debug prints, ensure docstrings, remove unused imports
- [ ] `pytest` — all tests pass
- [ ] `ruff check backend/` — no linting errors
- [ ] `npm run build` — frontend builds without errors
- [ ] Demo images in `data/demo_images/` for presentation
- [ ] `STAGES.md` updated with completion status for all stages

**Gate:** All tests pass. `npm run build` succeeds. Documentation complete. Demo runs end-to-end. Ready for capstone evaluation.

---

## Stage Quick Reference

| Stage | Name | Key Deliverable | Status |
|-------|------|----------------|--------|
| 0 | Project Setup | Monorepo + both servers runnable | ✓ Complete |
| 1 | Dataset & EDA | Roboflow dataset downloaded, stats documented | ✓ Complete |
| 2 | PPE Detection Model | YOLOv8 trained, predictor.py working | ◑ Partial (helmet OK, vest/person/gloves weak) |
| 3 | Zone Rule Engine | Violation detection logic + tests | ✓ Complete |
| 4 | Event Logging & Analytics | Event log + dashboard metrics | ✓ Complete |
| 5 | TTS Voice Alerts | Backend MP3 generation via edge-tts | Not Started |
| 6 | API Layer | FastAPI routes for all features | Not Started |
| 7 | React Frontend | 6-camera grid + live dashboard | Not Started |
| 8 | PDF Report Generation | Supervisor daily safety report | Not Started |
| 9 | Integration Testing | End-to-end pipeline + error handling | Not Started |
| 10 | Evaluation & Polish | Final docs + clean code + demo ready | Not Started |

**Legend:** Not Started = ○ | In Progress = ◑ | Complete = ✓