# Stage 7 — React Frontend (Dashboard UI)

## Overview

The frontend is a React + TypeScript single-page app built with Vite.
It renders a 6-camera grid for image upload, live metrics via React
Query polling, Plotly charts, TTS audio playback, and a PDF download
button.

## Component Tree

```
App
├── Header (title + subtitle)
└── Dashboard
    ├── Sidebar
    │   ├── Confidence slider
    │   ├── TTS toggle + backend selector
    │   ├── Clear Session button
    │   └── Download PDF button
    ├── KPI Cards (4x grid)
    │   ├── Total Scans
    │   ├── Total Violations
    │   ├── Compliance Rate
    │   └── Most Unsafe Zone
    ├── Camera Grid (3x2)
    │   └── CameraTile (x6)
    │       ├── File upload
    │       ├── Image preview
    │       ├── Detection badges
    │       ├── Violation warnings
    │       └── AlertPlayer (TTS)
    ├── Charts
    │   ├── ViolationsPerZoneBar (Plotly bar)
    │   ├── PPEBreakdownPie (Plotly pie)
    │   └── ViolationTimeline (Plotly scatter)
    ├── Hotspot Ranking
    └── Recent Alerts Table
```

## State Flow

1. **UI state** (Zustand): `selectedZone`, `ttsEnabled`, `ttsBackend`,
   `confidenceThreshold` — lives in `appStore.ts`
2. **Server cache** (React Query): metrics, events, charts, zones —
   auto-refetches every 5s, invalidates on scan success
3. **Scan flow**: User uploads image → `useScan` mutation →
   `POST /api/scan` → response stored in `CameraTile` local state →
   metrics/charts invalidated and refetch

## Data Fetching

All API calls go through `src/api/endpoints.ts` using the pre-configured
axios client. React Query hooks in `src/hooks/useApi.ts` provide:

- `useZones()` — static, never refetches
- `useMetrics()`, `useKpi()`, `useEvents()` — poll every 5s
- `useScan()` — mutation, invalidates all data queries on success
- `useClearSession()` — mutation, invalidates everything
- `useDownloadReport()` — mutation, triggers browser download

## TTS Playback

When a scan produces violations and TTS is enabled:
1. `CameraTile` renders `<AlertPlayer message={tts_message} />`
2. `AlertPlayer` calls `POST /api/tts` to get MP3 bytes
3. Creates a blob URL and assigns to `<audio>` element
4. Attempts autoplay (may be blocked by browser — user clicks play)

## Responsive Design

- **Desktop (1280px+)**: 3-column camera grid, sidebar on left
- **Tablet (768px)**: 2-column camera grid
- **Mobile (375px)**: 1-column camera grid, sidebar stacks on top

Tailwind CSS breakpoints: `md:grid-cols-2 lg:grid-cols-3`

## Files

- `frontend/src/types/index.ts` — TS interfaces matching Pydantic schemas
- `frontend/src/api/endpoints.ts` — typed API functions
- `frontend/src/hooks/useApi.ts` — React Query hooks
- `frontend/src/store/appStore.ts` — Zustand UI state
- `frontend/src/components/CameraTile.tsx` — upload + detection + violations
- `frontend/src/components/MetricCard.tsx` — KPI card
- `frontend/src/components/ChartBuilder.tsx` — Plotly chart factory
- `frontend/src/components/AlertPlayer.tsx` — TTS audio playback
- `frontend/src/components/Sidebar.tsx` — controls
- `frontend/src/pages/Dashboard.tsx` — main page
- `frontend/src/App.tsx` — root component
