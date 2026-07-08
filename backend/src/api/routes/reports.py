"""Report routes — GET /api/report.

Generates a PDF safety report from the event log and returns it for
download. The actual PDF generation is implemented in Stage 8 — this
route returns a placeholder until then.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response

from backend.src.api.pipeline import get_event_logger

logger = logging.getLogger(__name__)

router = APIRouter(tags=["reports"])


@router.get("/report")
async def generate_report(site_name: str = "Construction Site") -> Response:
    """Generate a PDF safety report and return it for download.

    Args:
        site_name: Name of the construction site for the report header.

    Returns:
        Response with PDF bytes (content-type: application/pdf).

    Note:
        Stage 8 will implement the full PDF generator. For now, this
        returns a minimal placeholder PDF so the endpoint works.
    """
    logger_obj = get_event_logger()
    summary = logger_obj.get_summary()

    # Try the real PDF generator (Stage 8)
    try:
        from backend.src.reporting.pdf_generator import generate_daily_report

        pdf_bytes = generate_daily_report(
            event_log=logger_obj.get_all_events(),
            site_name=site_name,
            date=datetime.now(UTC).strftime("%Y-%m-%d"),
        )
        if pdf_bytes:
            return Response(
                content=pdf_bytes,
                media_type="application/pdf",
                headers={
                    "Content-Disposition": 'attachment; filename="safety_report.pdf"'
                },
            )
    except ImportError:
        logger.warning("PDF generator not yet implemented (Stage 8). Returning placeholder.")
    except Exception as e:
        logger.error("PDF generation failed: %s", e)

    # Placeholder: return a minimal valid PDF
    placeholder = _generate_placeholder_pdf(site_name, summary)
    return Response(
        content=placeholder,
        media_type="application/pdf",
        headers={"Content-Disposition": 'attachment; filename="safety_report.pdf"'},
    )


def _generate_placeholder_pdf(site_name: str, summary: dict) -> bytes:
    """Generate a minimal placeholder PDF.

    This will be replaced by the full reportlab generator in Stage 8.

    Args:
        site_name: Site name for the header.
        summary: Summary metrics dict.

    Returns:
        Minimal PDF bytes.
    """
    try:
        import io

        from reportlab.lib.pagesizes import letter
        from reportlab.pdfgen import canvas

        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=letter)

        c.drawString(100, 750, "Construction Site Safety Report")
        c.drawString(100, 730, f"Site: {site_name}")
        c.drawString(100, 710, f"Date: {datetime.now(UTC).strftime('%Y-%m-%d')}")
        c.drawString(100, 680, f"Total Scans: {summary.get('total_scans', 0)}")
        c.drawString(100, 660, f"Total Violations: {summary.get('total_violations', 0)}")
        c.drawString(100, 640, f"Compliance Rate: {summary.get('compliance_rate', 0):.1%}")
        c.drawString(100, 600, "(Full report will be implemented in Stage 8)")

        c.showPage()
        c.save()
        return buffer.getvalue()
    except Exception as e:
        logger.error("Placeholder PDF failed: %s", e)
        raise HTTPException(status_code=500, detail="PDF generation failed") from e
