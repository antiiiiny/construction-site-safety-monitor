"""Pydantic schemas for API request/response models.

These models define the shape of data exchanged between the React
frontend and the FastAPI backend. They mirror the internal data
structures but add validation and OpenAPI documentation.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class DetectionOut(BaseModel):
    """A single detection result returned by the predictor."""

    class_name: str = Field(..., description="Canonical class name (person, helmet, vest, gloves)")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score 0-1")
    bbox: list[int] = Field(..., min_length=4, max_length=4, description="[x1, y1, x2, y2] pixel coords")


class ViolationOut(BaseModel):
    """A PPE compliance violation for one person."""

    zone_id: int
    zone_name: str
    person_bbox: list[int]
    missing_ppe: list[str]
    severity: str
    timestamp: str


class ZoneOut(BaseModel):
    """Zone configuration."""

    zone_id: int
    name: str
    required_ppe: list[str]
    hazard_description: str


class ScanResponse(BaseModel):
    """Response from POST /api/scan — full pipeline result."""

    zone_id: int
    zone_name: str
    detections: list[DetectionOut]
    violations: list[ViolationOut]
    tts_message: str
    tts_audio_available: bool = False
    detection_count: int
    violation_count: int


class MetricsSummary(BaseModel):
    """Dashboard summary metrics."""

    total_scans: int
    total_violations: int
    scans_with_violations: int
    compliance_rate: float
    violations_per_zone: dict[int, int]
    violations_per_ppe: dict[str, int]
    severity_breakdown: dict[str, int]
    most_unsafe_zone: int | None
    session_id: str


class KpiCards(BaseModel):
    """KPI card data for the dashboard."""

    total_scans: int
    total_violations: int
    compliance_rate: float
    most_unsafe_zone: str | None


class BarChartData(BaseModel):
    """Bar chart data point."""

    zone_id: int
    zone_name: str
    violations: int


class PieChartData(BaseModel):
    """Pie chart data point."""

    ppe: str
    count: int


class TimelineEntry(BaseModel):
    """Timeline chart entry."""

    index: int
    timestamp: str
    zone_id: int
    zone_name: str
    severity: str
    missing_ppe: list[str]


class HotspotEntry(BaseModel):
    """Hotspot ranking entry."""

    zone_id: int
    zone_name: str
    violations: int
    scans: int
    violation_rate: float
    rank: int


class TTSRequest(BaseModel):
    """Request body for POST /api/tts."""

    message: str = Field(..., min_length=1, description="Text to convert to speech")


class EventOut(BaseModel):
    """A single event from the event log."""

    type: str
    timestamp: str
    zone_id: int | None = None
    zone_name: str | None = None
    severity: str | None = None
    missing_ppe: list[str] | None = None
    detection_count: int | None = None
    violation_count: int | None = None
