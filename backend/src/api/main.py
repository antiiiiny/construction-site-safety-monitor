"""FastAPI application entry point.

Stage 0 scaffold: mounts routers, configures CORS for the Vite dev server,
and exposes a /health endpoint. Route modules are added in Stage 6.
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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
# In production, tighten this to the deployed frontend origin.
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


@app.get("/health")
async def health() -> dict[str, str]:
    """Health check endpoint for uptime verification.

    Returns:
        Dict with status "ok" if the server is running.
    """
    return {"status": "ok"}


# Route routers will be mounted here in Stage 6, e.g.:
# from backend.src.api.routes import detection, analytics, alerts, reports
# app.include_router(detection.router, prefix="/api")
# app.include_router(analytics.router, prefix="/api")
# app.include_router(alerts.router, prefix="/api")
# app.include_router(reports.router, prefix="/api")
