"""PDF report generator — supervisor-grade daily safety report.

Generates a multi-section PDF using reportlab from the event log.
Returns PDF as bytes for the FastAPI /api/report endpoint.

PDF sections:
  1. Header — site name, date, timestamp
  2. Executive Summary — totals, compliance rate, most unsafe zone
  3. Zone-Wise Violation Table
  4. PPE Violation Breakdown
  5. Zone Hotspot Ranking
  6. Incident Log (recent 20)
  7. Supervisor Summary (LLM or rule-based)
  8. Recommendations
  9. Footer

Usage:
    from backend.src.reporting.pdf_generator import generate_daily_report
    pdf_bytes = generate_daily_report(event_log, "Construction Site", "2026-07-07")
"""

from __future__ import annotations

import io
import logging
from collections import defaultdict
from datetime import UTC, datetime
from typing import Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from backend.src.reporting.recommendations import generate_recommendations
from backend.src.reporting.summary_generator import generate_summary

logger = logging.getLogger(__name__)


def generate_daily_report(
    event_log: list[dict[str, Any]],
    site_name: str = "Construction Site",
    date: str | None = None,
) -> bytes:
    """Generate a daily safety report PDF from the event log.

    Args:
        event_log: List of event dicts from EventLogger.get_all_events().
        site_name: Name of the construction site.
        date: Report date string (YYYY-MM-DD). Defaults to today.

    Returns:
        PDF as bytes.
    """
    if date is None:
        date = datetime.now(UTC).strftime("%Y-%m-%d")

    # Compute metrics from event log
    metrics = _compute_metrics(event_log)

    # Build the PDF
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=0.5 * inch,
        leftMargin=0.5 * inch,
        topMargin=0.5 * inch,
        bottomMargin=0.5 * inch,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "CustomTitle", parent=styles["Title"], fontSize=18, spaceAfter=6
    )
    heading_style = ParagraphStyle(
        "CustomHeading", parent=styles["Heading2"], fontSize=13,
        spaceBefore=12, spaceAfter=6, textColor=colors.HexColor("#0369a1"),
    )
    body_style = ParagraphStyle(
        "CustomBody", parent=styles["Normal"], fontSize=10, spaceAfter=6,
        leading=14,
    )
    footer_style = ParagraphStyle(
        "Footer", parent=styles["Normal"], fontSize=8, textColor=colors.grey,
        alignment=1,  # center
    )

    story: list[Any] = []

    # 1. Header
    story.append(Paragraph("Construction Site Safety Report", title_style))
    story.append(Paragraph(f"Site: {site_name}", body_style))
    story.append(Paragraph(f"Date: {date}", body_style))
    story.append(Paragraph(
        f"Generated: {datetime.now(UTC).strftime('%Y-%m-%d %H:%M UTC')}",
        body_style,
    ))
    story.append(Spacer(1, 0.2 * inch))

    # 2. Executive Summary
    story.append(Paragraph("Executive Summary", heading_style))
    total_scans = metrics["total_scans"]
    total_violations = metrics["total_violations"]
    compliance_pct = metrics["compliance_rate"] * 100
    most_unsafe = metrics.get("most_unsafe_zone_name", "N/A")

    story.append(Paragraph(
        f"Total Scans: {total_scans}<br/>"
        f"Total Violations: {total_violations}<br/>"
        f"Compliance Rate: {compliance_pct:.1f}%<br/>"
        f"Most Unsafe Zone: {most_unsafe}",
        body_style,
    ))
    story.append(Spacer(1, 0.15 * inch))

    # 3. Zone-Wise Violation Table
    story.append(Paragraph("Zone-Wise Violation Summary", heading_style))
    zone_data = [["Zone", "Scans", "Violations", "Compliance %"]]
    for zone_id in range(1, 7):
        from backend.src.rules.zone_config import get_zone

        zone = get_zone(zone_id)
        z_stats = metrics["zone_stats"].get(zone_id, {})
        scans = z_stats.get("scans", 0)
        violations = z_stats.get("violations", 0)
        comp = f"{((1 - violations / scans) * 100):.0f}%" if scans > 0 else "N/A"
        zone_data.append([zone.name, str(scans), str(violations), comp])

    zone_table = Table(zone_data, colWidths=[2 * inch, 1 * inch, 1.2 * inch, 1.2 * inch])
    zone_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0ea5e9")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ALIGN", (1, 0), (-1, -1), "CENTER"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f0f9ff")]),
    ]))
    story.append(zone_table)
    story.append(Spacer(1, 0.15 * inch))

    # 4. PPE Violation Breakdown
    story.append(Paragraph("PPE Violation Breakdown", heading_style))
    ppe_data = [["PPE Type", "Violation Count"]]
    for ppe, count in sorted(
        metrics["violations_per_ppe"].items(), key=lambda x: -x[1]
    ):
        ppe_data.append([ppe.capitalize(), str(count)])
    if len(ppe_data) == 1:
        ppe_data.append(["No violations", "0"])

    ppe_table = Table(ppe_data, colWidths=[2.5 * inch, 1.5 * inch])
    ppe_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0ea5e9")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ALIGN", (1, 0), (-1, -1), "CENTER"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
    ]))
    story.append(ppe_table)
    story.append(Spacer(1, 0.15 * inch))

    # 5. Zone Hotspot Ranking
    story.append(Paragraph("Zone Hotspot Ranking", heading_style))
    hotspots = sorted(
        metrics["zone_stats"].items(),
        key=lambda x: x[1].get("violations", 0),
        reverse=True,
    )[:3]
    if any(s.get("violations", 0) > 0 for _, s in hotspots):
        hotspot_data = [["Rank", "Zone", "Violations", "Scans", "Rate"]]
        for i, (zone_id, stats) in enumerate(hotspots):
            if stats.get("violations", 0) == 0:
                continue
            from backend.src.rules.zone_config import get_zone

            zone = get_zone(zone_id)
            scans = stats.get("scans", 0)
            violations = stats.get("violations", 0)
            rate = f"{violations / scans:.1f}" if scans > 0 else "N/A"
            hotspot_data.append([str(i + 1), zone.name, str(violations), str(scans), rate])

        if len(hotspot_data) > 1:
            hs_table = Table(hotspot_data, colWidths=[0.5 * inch, 2 * inch, 1 * inch, 0.8 * inch, 0.8 * inch])
            hs_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#ef4444")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("ALIGN", (1, 0), (-1, -1), "CENTER"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ]))
            story.append(hs_table)
    else:
        story.append(Paragraph("No zone hotspots — no violations detected.", body_style))
    story.append(Spacer(1, 0.15 * inch))

    # 6. Incident Log (recent 20)
    story.append(Paragraph("Incident Log (Recent 20)", heading_style))
    violations = [e for e in event_log if e.get("type") == "violation"][-20:]
    if violations:
        incident_data = [["Time", "Zone", "Missing PPE", "Severity"]]
        for v in reversed(violations):
            ts = v.get("timestamp", "")[:19]
            zone = v.get("zone_name", "")
            ppe = ", ".join(v.get("missing_ppe", []))
            sev = v.get("severity", "")
            incident_data.append([ts, zone, ppe, sev])

        inc_table = Table(incident_data, colWidths=[1.5 * inch, 1.2 * inch, 2 * inch, 0.8 * inch])
        inc_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0ea5e9")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("ALIGN", (3, 0), (3, -1), "CENTER"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#fef2f2")]),
        ]))
        story.append(inc_table)
    else:
        story.append(Paragraph("No violations detected during this period.", body_style))
    story.append(Spacer(1, 0.15 * inch))

    # 7. Supervisor Summary
    story.append(Paragraph("Supervisor Summary", heading_style))
    summary_text = generate_summary(event_log, metrics)

    # Try LLM if enabled
    try:
        from backend.config.settings import settings

        if settings.llm_enabled:
            from backend.src.reporting.llm_client import generate_llm_summary

            llm_summary = generate_llm_summary(metrics)
            if llm_summary:
                summary_text = llm_summary
    except Exception as e:
        logger.warning("LLM summary failed, using rule-based: %s", e)

    story.append(Paragraph(summary_text, body_style))
    story.append(Spacer(1, 0.15 * inch))

    # 8. Recommendations
    story.append(Paragraph("Recommendations", heading_style))
    recs = generate_recommendations(metrics)
    for i, rec in enumerate(recs, 1):
        story.append(Paragraph(f"{i}. {rec}", body_style))
    story.append(Spacer(1, 0.2 * inch))

    # 9. Footer
    story.append(Spacer(1, 0.3 * inch))
    story.append(Paragraph(
        "Generated by AI Construction Safety Monitor | "
        "This report is automated and should be reviewed by a qualified safety officer.",
        footer_style,
    ))

    # Build the PDF
    doc.build(story)
    pdf_bytes = buffer.getvalue()
    buffer.close()

    logger.info("Generated PDF report: %d bytes, %d events", len(pdf_bytes), len(event_log))
    return pdf_bytes


def _compute_metrics(event_log: list[dict[str, Any]]) -> dict[str, Any]:
    """Compute summary metrics from the event log.

    This mirrors EventLogger.get_summary() but works on a raw event list,
    so the PDF generator can be called from tests without a live EventLogger.

    Args:
        event_log: List of event dicts.

    Returns:
        Metrics dict matching EventLogger.get_summary() format.
    """
    scans = [e for e in event_log if e.get("type") == "scan"]
    violations = [e for e in event_log if e.get("type") == "violation"]

    total_scans = len(scans)
    total_violations = len(violations)
    scans_with_violations = sum(1 for s in scans if s.get("violation_count", 0) > 0)
    compliance_rate = (
        (total_scans - scans_with_violations) / total_scans
        if total_scans > 0
        else 1.0
    )

    violations_per_zone: dict[int, int] = defaultdict(int)
    violations_per_ppe: dict[str, int] = defaultdict(int)
    severity_breakdown: dict[str, int] = defaultdict(int)
    zone_stats: dict[int, dict[str, Any]] = defaultdict(
        lambda: {"scans": 0, "violations": 0, "missing_ppe_counts": {}, "severity_counts": {}}
    )

    for s in scans:
        zone_stats[s["zone_id"]]["scans"] += 1

    for v in violations:
        zid = v["zone_id"]
        violations_per_zone[zid] += 1
        zone_stats[zid]["violations"] += 1
        for ppe in v.get("missing_ppe", []):
            violations_per_ppe[ppe] += 1
        severity_breakdown[v.get("severity", "")] += 1

    most_unsafe_zone = max(violations_per_zone, key=violations_per_zone.get) if violations_per_zone else None
    most_unsafe_zone_name = None
    if most_unsafe_zone is not None:
        try:
            from backend.src.rules.zone_config import get_zone

            most_unsafe_zone_name = get_zone(most_unsafe_zone).name
        except ValueError:
            pass

    return {
        "total_scans": total_scans,
        "total_violations": total_violations,
        "scans_with_violations": scans_with_violations,
        "compliance_rate": round(compliance_rate, 4),
        "violations_per_zone": dict(violations_per_zone),
        "violations_per_ppe": dict(violations_per_ppe),
        "severity_breakdown": dict(severity_breakdown),
        "most_unsafe_zone": most_unsafe_zone,
        "most_unsafe_zone_name": most_unsafe_zone_name,
        "zone_stats": dict(zone_stats),
    }
