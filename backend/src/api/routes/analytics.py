"""Analytics routes — GET /api/metrics, /api/events, /api/export/csv.

Provides dashboard data: summary metrics, recent events, CSV export,
hotspot ranking, and chart-ready data.
"""

from __future__ import annotations

from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse

from backend.src.analytics.export_csv import export_events_csv, export_summary_csv
from backend.src.analytics.hotspot_analysis import get_hotspots
from backend.src.analytics.metrics import (
    get_kpi_cards,
    get_violation_timeline,
    get_violations_per_ppe,
    get_violations_per_zone,
)
from backend.src.api.pipeline import get_event_logger
from backend.src.api.schemas.models import (
    BarChartData,
    EventOut,
    HotspotEntry,
    KpiCards,
    MetricsSummary,
    PieChartData,
    TimelineEntry,
)

router = APIRouter(tags=["analytics"])


@router.get("/metrics", response_model=MetricsSummary)
async def get_metrics() -> MetricsSummary:
    """Get overall summary metrics for the dashboard.

    Returns:
        MetricsSummary with totals, compliance rate, per-zone/PPE breakdowns.
    """
    logger_obj = get_event_logger()
    summary = logger_obj.get_summary()
    return MetricsSummary(**summary)


@router.get("/kpi", response_model=KpiCards)
async def get_kpi() -> KpiCards:
    """Get KPI card data (total scans, violations, compliance, most unsafe zone).

    Returns:
        KpiCards with dashboard summary numbers.
    """
    logger_obj = get_event_logger()
    kpis = get_kpi_cards(logger_obj)
    return KpiCards(**kpis)


@router.get("/events", response_model=list[EventOut])
async def get_events(
    limit: int = Query(50, ge=1, le=500, description="Max events to return"),
    event_type: str | None = Query(None, description="Filter by 'scan' or 'violation'"),
) -> list[EventOut]:
    """Get recent events from the event log.

    Args:
        limit: Maximum number of events to return (default 50).
        event_type: Optional filter — 'scan' or 'violation'.

    Returns:
        List of recent events, most recent first.
    """
    logger_obj = get_event_logger()
    if event_type == "violation":
        events = logger_obj.get_violations()
    elif event_type == "scan":
        events = logger_obj.get_scans()
    else:
        events = logger_obj.get_all_events()

    # Most recent first, limited
    events = list(reversed(events))[:limit]
    return [EventOut(**e) for e in events]


@router.get("/charts/violations-per-zone", response_model=list[BarChartData])
async def get_violations_per_zone_chart() -> list[BarChartData]:
    """Get violation counts per zone for bar chart.

    Returns:
        List of BarChartData for all 6 zones.
    """
    logger_obj = get_event_logger()

    data = get_violations_per_zone(logger_obj)
    return [BarChartData(**d) for d in data]


@router.get("/charts/violations-per-ppe", response_model=list[PieChartData])
async def get_violations_per_ppe_chart() -> list[PieChartData]:
    """Get violation counts per PPE type for pie chart.

    Returns:
        List of PieChartData.
    """
    logger_obj = get_event_logger()
    data = get_violations_per_ppe(logger_obj)
    return [PieChartData(**d) for d in data]


@router.get("/charts/timeline", response_model=list[TimelineEntry])
async def get_timeline() -> list[TimelineEntry]:
    """Get violation timeline for timeline chart.

    Returns:
        List of TimelineEntry in chronological order.
    """
    logger_obj = get_event_logger()
    data = get_violation_timeline(logger_obj)
    return [TimelineEntry(**d) for d in data]


@router.get("/hotspots", response_model=list[HotspotEntry])
async def get_hotspot_ranking(
    top_n: int = Query(3, ge=1, le=6, description="Number of hotspots"),
) -> list[HotspotEntry]:
    """Get zone hotspot ranking.

    Args:
        top_n: Number of top zones to return (default 3).

    Returns:
        List of HotspotEntry sorted by violation count.
    """
    logger_obj = get_event_logger()
    data = get_hotspots(logger_obj, top_n=top_n)
    return [HotspotEntry(**d) for d in data]


@router.get("/export/csv")
async def export_csv() -> StreamingResponse:
    """Export all events as CSV download.

    Returns:
        StreamingResponse with CSV content.
    """
    logger_obj = get_event_logger()
    csv_bytes = export_events_csv(logger_obj)
    return StreamingResponse(
        iter([csv_bytes]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=events.csv"},
    )


@router.get("/export/summary-csv")
async def export_summary_csv_route() -> StreamingResponse:
    """Export per-zone summary as CSV download.

    Returns:
        StreamingResponse with CSV content.
    """
    logger_obj = get_event_logger()
    csv_bytes = export_summary_csv(logger_obj)
    return StreamingResponse(
        iter([csv_bytes]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=summary.csv"},
    )


@router.post("/clear")
async def clear_session() -> dict[str, str]:
    """Clear all events from the session (Clear Session button).

    Returns:
        Dict with status message.
    """
    from backend.src.api.pipeline import reset_event_logger

    reset_event_logger()
    return {"status": "cleared"}


@router.post("/simulate")
async def simulate_session(
    num_scans: int = Query(24, ge=1, le=100, description="Number of mock scans"),
) -> dict[str, object]:
    """Populate the event log with simulated session data.

    Generates realistic mock scans and violations across all 6 zones.
    Useful for demos and testing the dashboard without uploading images.

    Args:
        num_scans: Number of scans to simulate (default 24).

    Returns:
        Dict with simulation summary (scans, violations, compliance rate).
    """
    import random
    from datetime import UTC, datetime, timedelta

    from backend.src.rules.models import Violation
    from backend.src.rules.zone_config import get_zone

    logger_obj = get_event_logger()
    logger_obj.clear()  # Start fresh

    random.seed(42)  # Reproducible
    zone_names = {z.zone_id: z.name for z in [get_zone(i) for i in range(1, 7)]}
    zone_required_ppe = {z.zone_id: z.required_ppe for z in [get_zone(i) for i in range(1, 7)]}
    base_time = datetime.now(UTC) - timedelta(hours=8)

    for i in range(num_scans):
        zone_id = (i % 6) + 1
        scan_time = base_time + timedelta(minutes=i * 20)
        required = zone_required_ppe[zone_id]
        has_violation = random.random() < 0.6

        if has_violation:
            num_missing = random.randint(1, min(2, len(required)))
            missing = random.sample(required, num_missing)
            severity = "high" if zone_id == 3 or num_missing >= 2 else "medium"

            v = Violation(
                zone_id=zone_id,
                zone_name=zone_names[zone_id],
                person_bbox=(
                    random.randint(50, 200),
                    random.randint(50, 200),
                    random.randint(300, 500),
                    random.randint(400, 700),
                ),
                missing_ppe=missing,
                severity=severity,
                timestamp=scan_time.isoformat(),
            )

            detections = [{"class_name": "person", "confidence": 0.92, "bbox": [100, 100, 300, 600]}]
            for ppe in required:
                if ppe not in missing:
                    detections.append({
                        "class_name": ppe,
                        "confidence": random.uniform(0.75, 0.95),
                        "bbox": [random.randint(120, 250), random.randint(80, 300),
                                 random.randint(200, 350), random.randint(200, 500)],
                    })

            logger_obj.log_scan(zone_id, detections, [v])
        else:
            detections = [{"class_name": "person", "confidence": 0.95, "bbox": [100, 100, 300, 600]}]
            for ppe in required:
                detections.append({
                    "class_name": ppe,
                    "confidence": random.uniform(0.80, 0.98),
                    "bbox": [random.randint(120, 250), random.randint(80, 300),
                             random.randint(200, 350), random.randint(200, 500)],
                })
            logger_obj.log_scan(zone_id, detections, [])

    summary = logger_obj.get_summary()
    return {
        "status": "simulated",
        "total_scans": summary["total_scans"],
        "total_violations": summary["total_violations"],
        "compliance_rate": summary["compliance_rate"],
        "most_unsafe_zone": summary.get("most_unsafe_zone"),
    }
