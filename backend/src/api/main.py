"""FastAPI application entry point.

Mounts all route routers, configures CORS for the Vite dev server,
and exposes a /health endpoint.
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.src.api.routes import alerts, analytics, detection, reports

app = FastAPI(
    title="Construction Site Safety Monitor API",
    description=(
        "Backend for the Construction Site Safety Monitor. Handles YOLOv8 "
        "PPE detection, zone compliance rules, TTS voice alerts, analytics, "
        "and PDF report generation."
    ),
    version="0.1.0",
)

# Allow the Vite dev server (default port 5173) to call the API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount route routers
app.include_router(detection.router, prefix="/api")
app.include_router(analytics.router, prefix="/api")
app.include_router(alerts.router, prefix="/api")
app.include_router(reports.router, prefix="/api")


@app.get("/health")
async def health() -> dict[str, str]:
    """Health check endpoint for uptime verification.

    Returns:
        Dict with status "ok" if the server is running.
    """
    return {"status": "ok"}
