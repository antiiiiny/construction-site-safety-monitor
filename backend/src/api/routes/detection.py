"""Detection routes — POST /api/scan, GET /api/zones.

POST /api/scan accepts an image upload + zone_id, runs the full pipeline
(detection → rules → logging → TTS message), and returns the result.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from backend.src.api.pipeline import run_zone_pipeline
from backend.src.api.schemas.models import ScanResponse, ZoneOut
from backend.src.rules.zone_config import get_all_zones, get_zone

logger = logging.getLogger(__name__)

router = APIRouter(tags=["detection"])


@router.get("/zones", response_model=list[ZoneOut])
async def list_zones() -> list[ZoneOut]:
    """Get all zone configurations.

    Returns:
        List of 6 zones with their required PPE and hazard descriptions.
    """
    return [
        ZoneOut(
            zone_id=z.zone_id,
            name=z.name,
            required_ppe=z.required_ppe,
            hazard_description=z.hazard_description,
        )
        for z in get_all_zones()
    ]


@router.post("/scan", response_model=ScanResponse)
async def scan_zone(
    zone_id: int = Form(...),
    image: UploadFile = File(...),  # noqa: B008
) -> ScanResponse:
    """Run PPE detection and compliance check on an uploaded image.

    Args:
        zone_id: The zone to check (1-6).
        image: Uploaded image file (JPEG/PNG).

    Returns:
        ScanResponse with detections, violations, and TTS message.
    """
    # Validate zone_id
    try:
        get_zone(zone_id)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid zone_id: {zone_id}") from None

    # Read image bytes
    image_bytes = await image.read()
    if not image_bytes:
        raise HTTPException(status_code=400, detail="Empty image file")

    # Run the pipeline
    try:
        result = run_zone_pipeline(zone_id, image_bytes)
    except FileNotFoundError as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
    except Exception as e:
        logger.error("Pipeline error: %s", e)
        raise HTTPException(status_code=500, detail="Detection pipeline failed") from e

    return ScanResponse(**result)
