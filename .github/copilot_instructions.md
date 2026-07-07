# Copilot Instructions — Construction Site Safety Monitor

## What This Project Does

A full-stack web app that simulates a construction site with 6 fixed camera zones. Users upload images into camera tiles in a React frontend, a FastAPI backend runs YOLOv8 PPE detection, checks zone compliance, generates TTS voice alerts, maintains live analytics, and produces a downloadable PDF safety report.

Pipeline: Image Upload (6 zones) → YOLOv8 Detection → Zone Rule Engine → Violation Events → TTS Alert + Dashboard + PDF Report

## Tech Stack

- **Backend**: Python 3.11, FastAPI, Ultralytics (YOLOv8), edge-tts, reportlab, python-dotenv
- **Frontend**: Vite + React + TypeScript, Tailwind CSS, react-plotly.js
- **State**: React Query (server cache) + Zustand (UI state)
- **TTS**: edge-tts (primary), gTTS (fallback) — backend generates MP3, frontend plays via `<audio>`
- **LLM** (optional): OpenRouter (OpenAI-compatible) with GPT-4o-mini for PDF supervisor summary. Falls back to rule-based if no key.
- **Testing**: pytest + httpx (backend), pytest-asyncio
- **Linting**: ruff (backend)

## Directory Structure

```
construction-site-safety-monitor/
├── backend/
│   ├── config/              # zones.py, class_mapping.py, tts_config.py, settings.py
│   ├── src/
│   │   ├── detection/       # YOLOv8 loading, inference, visualization
│   │   ├── rules/           # zone config, violation engine, data models
│   │   ├── alerts/          # TTS engine, message building
│   │   ├── analytics/       # event logging, metrics, hotspot analysis
│   │   ├── reporting/       # PDF generation, summary, recommendations, llm_client
│   │   └── api/             # FastAPI app, routes, Pydantic schemas
│   ├── tests/
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/      # CameraTile, MetricCard, ChartBuilder, AlertPlayer
│   │   ├── pages/           # Dashboard
│   │   ├── hooks/           # useScan, useMetrics
│   │   ├── store/           # Zustand store
│   │   ├── api/             # axios client, typed endpoints
│   │   └── types/           # TS interfaces matching Pydantic schemas
│   └── package.json
├── scripts/                 # run_dev.py, run_demo.py
├── data/                    # dataset (gitignored)
├── docs/                    # stage documentation
└── STAGES.md
```

## Zones

| Zone | Name | Required PPE |
|------|------|--------------|
| 1 | Entry Gate | Helmet, Vest |
| 2 | Scaffold Zone | Helmet, Vest |
| 3 | Welding Zone | Helmet, Gloves, Vest |
| 4 | Concrete Zone | Helmet, Vest |
| 5 | Loading Zone | Helmet, Vest |
| 6 | Material Yard | Helmet, Vest |

Zone rules are config-driven (`backend/config/zones.py`), not hardcoded in detection or alert modules.

## PPE Classes to Detect

Primary: `person`, `helmet`, `vest`
Secondary: `gloves`

Map dataset labels to these canonical names in `backend/config/class_mapping.py`. Harness and boots are intentionally excluded — most public PPE datasets do not label them.

## Conventions

- PEP 8, type hints on all public functions, Google-style docstrings
- `test_<module>.py` for tests; run with `pytest backend/tests/`
- Detection results are a list of dicts: `{"class_name", "confidence", "bbox"}`
- Rule engine is pure functions — no side effects
- PPE→person association: PPE bbox center must fall inside person bbox (containment)
- TTS messages name the zone and missing PPE: "Attention, Welding Zone. Safety gloves and helmet are required in this area."
- State is in-memory session-scoped (no database) — React Query for server cache, Zustand for UI state
- PDF sections: Header, Executive Summary, Zone-Wise Table, PPE Breakdown, Hotspot Ranking, Incident Log, Supervisor Summary, Recommendations, Footer
- Supervisor Summary: uses LLM (GPT-4o-mini via OpenRouter) if `OPENROUTER_API_KEY` is set, otherwise rule-based
- All secrets/API keys live in `.env` (gitignored). Use `.env.example` as template. Read via `backend/config/settings.py`.
- Start both servers with `python scripts/run_dev.py`

## Do NOT

- No live RTSP / CCTV video streaming
- No user authentication or accounts
- No direct PyTorch usage — Ultralytics package only
- No worker re-identification or tracking
- No storing images beyond the session
- No hardcoded API keys — all secrets via `.env` and `settings.py`
