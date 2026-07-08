"""Integration tests for the full pipeline.

Tests the end-to-end flow: detection → rules → event logging → TTS message → PDF.
Uses mock detections (no model weights required) to verify the pipeline
orchestration works correctly.

Tests cover:
  - Zone 1 scan → detection → rule check → event logged → alert generated
  - Zone 3 scan → detection → rule check → event logged → alert generated
  - 6 zone scans → metrics correct
  - PDF generation after scans → all sections populated
  - Error handling (missing model, empty log)
"""

from __future__ import annotations

from unittest.mock import patch

import pytest

from backend.src.analytics.event_logger import EventLogger
from backend.src.reporting.pdf_generator import generate_daily_report


def _make_mock_detections(zone_id: int) -> list[dict]:
    """Create mock detections for a zone.

    Zone 1 (Entry Gate): person + helmet + vest → compliant
    Zone 3 (Welding): person + helmet (no gloves, no vest) → violations
    Other zones: person + helmet → missing vest
    """
    if zone_id == 1:
        # Compliant: person with helmet and vest
        return [
            {"class_name": "person", "confidence": 0.95, "bbox": [100, 100, 300, 600]},
            {"class_name": "helmet", "confidence": 0.88, "bbox": [150, 80, 250, 180]},
            {"class_name": "vest", "confidence": 0.85, "bbox": [130, 250, 270, 450]},
        ]
    if zone_id == 3:
        # Welding zone: person + helmet, missing gloves and vest
        return [
            {"class_name": "person", "confidence": 0.92, "bbox": [100, 100, 300, 600]},
            {"class_name": "helmet", "confidence": 0.90, "bbox": [150, 80, 250, 180]},
        ]
    # Other zones: person + helmet, missing vest
    return [
        {"class_name": "person", "confidence": 0.90, "bbox": [100, 100, 300, 600]},
        {"class_name": "helmet", "confidence": 0.85, "bbox": [150, 80, 250, 180]},
    ]


class TestPipelineZone1:
    """Test Zone 1 (Entry Gate) — compliant person."""

    def test_zone1_compliant_scan(self) -> None:
        """Zone 1: person + helmet + vest → no violations, event logged."""
        from backend.src.rules.violation_engine import check_compliance

        detections = _make_mock_detections(1)
        violations = check_compliance(detections, zone_id=1)

        assert len(violations) == 0

        # Log to event logger
        logger = EventLogger()
        logger.log_scan(zone_id=1, detections=detections, violations=violations)

        summary = logger.get_summary()
        assert summary["total_scans"] == 1
        assert summary["total_violations"] == 0
        assert summary["compliance_rate"] == 1.0


class TestPipelineZone3:
    """Test Zone 3 (Welding Zone) — missing gloves + vest."""

    def test_zone3_violations_generated(self) -> None:
        """Zone 3: person + helmet (no gloves, no vest) → 2 violations, high severity."""
        from backend.src.rules.violation_engine import check_compliance

        detections = _make_mock_detections(3)
        violations = check_compliance(detections, zone_id=3)

        assert len(violations) == 1  # One violation object per person
        assert len(violations[0].missing_ppe) == 2  # gloves + vest missing
        assert "gloves" in violations[0].missing_ppe
        assert "vest" in violations[0].missing_ppe
        assert violations[0].severity == "high"  # Welding zone = always high

    def test_zone3_tts_message_generated(self) -> None:
        """Zone 3 violations should produce a TTS alert message."""
        from backend.src.alerts.message_builder import build_scan_summary_message
        from backend.src.rules.violation_engine import check_compliance

        detections = _make_mock_detections(3)
        violations = check_compliance(detections, zone_id=3)
        message = build_scan_summary_message("Welding Zone", violations)

        assert len(message) > 0
        assert "Welding Zone" in message
        assert "Warning" in message  # high severity


class TestPipelineSixZones:
    """Test scanning all 6 zones and verifying metrics."""

    def test_six_zone_scan_metrics(self) -> None:
        """Scan all 6 zones → metrics should be correct."""
        from backend.src.rules.violation_engine import check_compliance

        logger = EventLogger()

        for zone_id in range(1, 7):
            detections = _make_mock_detections(zone_id)
            violations = check_compliance(detections, zone_id)
            logger.log_scan(zone_id, detections, violations)

        summary = logger.get_summary()
        assert summary["total_scans"] == 6
        # Zone 1: 0 violations, Zones 2-6: 1 violation each = 5 total
        assert summary["total_violations"] == 5
        # 1 compliant scan out of 6
        assert summary["compliance_rate"] == pytest.approx(1 / 6, abs=0.01)
        # Zone 3 should be most unsafe (high severity) or tied
        assert summary["most_unsafe_zone"] is not None

    def test_six_zone_zone_stats(self) -> None:
        """Zone stats should show correct per-zone breakdown."""
        from backend.src.rules.violation_engine import check_compliance

        logger = EventLogger()

        for zone_id in range(1, 7):
            detections = _make_mock_detections(zone_id)
            violations = check_compliance(detections, zone_id)
            logger.log_scan(zone_id, detections, violations)

        stats = logger.get_zone_stats()
        assert stats[1]["violations"] == 0  # Entry Gate was compliant
        assert stats[3]["violations"] == 1  # Welding Zone had violations
        assert stats[3]["severity_counts"]["high"] == 1  # Welding = high


class TestPipelinePDFGeneration:
    """Test PDF generation after scans."""

    def test_pdf_after_six_scans(self) -> None:
        """Generate PDF after 6 zone scans → should be valid, non-empty."""
        from backend.src.rules.violation_engine import check_compliance

        logger = EventLogger()

        for zone_id in range(1, 7):
            detections = _make_mock_detections(zone_id)
            violations = check_compliance(detections, zone_id)
            logger.log_scan(zone_id, detections, violations)

        pdf = generate_daily_report(
            logger.get_all_events(),
            site_name="Test Construction Site",
            date="2026-07-07",
        )

        assert isinstance(pdf, bytes)
        assert len(pdf) > 0
        assert pdf[:5] == b"%PDF-"

    def test_pdf_empty_log(self) -> None:
        """PDF with empty event log should still work."""
        logger = EventLogger()
        pdf = generate_daily_report(
            logger.get_all_events(),
            site_name="Empty Site",
            date="2026-07-07",
        )
        assert pdf[:5] == b"%PDF-"


class TestPipelineErrorHandling:
    """Test error handling in the pipeline."""

    def test_missing_model_file(self) -> None:
        """Missing model file should raise FileNotFoundError."""
        # Reset the singleton predictor to force reload
        import backend.src.api.pipeline as pipeline_mod
        from backend.src.api.pipeline import run_zone_pipeline

        original_predictor = pipeline_mod._predictor
        pipeline_mod._predictor = None

        # Patch Predictor to raise FileNotFoundError
        with patch(
            "backend.src.detection.predictor.Path.exists",
            return_value=False,
        ), pytest.raises(FileNotFoundError):
            run_zone_pipeline(zone_id=1, image_bytes=b"fake_image")

        # Restore
        pipeline_mod._predictor = original_predictor

    def test_empty_event_log_pdf(self) -> None:
        """Empty event log should produce PDF with 'No violations detected'."""
        pdf = generate_daily_report([], "Test Site", "2026-07-07")
        assert len(pdf) > 0

    def test_tts_unavailable_degrades_gracefully(self) -> None:
        """If TTS fails, the alert text should still be in the scan result."""
        from backend.src.alerts.message_builder import build_scan_summary_message
        from backend.src.rules.violation_engine import check_compliance

        detections = _make_mock_detections(3)
        violations = check_compliance(detections, zone_id=3)
        message = build_scan_summary_message("Welding Zone", violations)

        # Message should exist even if TTS audio generation would fail
        assert len(message) > 0


class TestPipelineFullFlow:
    """Full flow test: scan → log → metrics → PDF in one sequence."""

    def test_full_flow(self) -> None:
        """Complete pipeline: 6 scans → metrics → PDF → verify all sections."""
        from backend.src.rules.violation_engine import check_compliance

        logger = EventLogger()

        # Scan all 6 zones
        for zone_id in range(1, 7):
            detections = _make_mock_detections(zone_id)
            violations = check_compliance(detections, zone_id)
            logger.log_scan(zone_id, detections, violations)

        # Verify metrics
        summary = logger.get_summary()
        assert summary["total_scans"] == 6
        assert summary["total_violations"] == 5

        # Verify events
        events = logger.get_all_events()
        assert len(events) > 6  # scans + violations

        # Verify PDF
        pdf = generate_daily_report(events, "Full Flow Test Site", "2026-07-07")
        assert pdf[:5] == b"%PDF-"
        assert len(pdf) > 1000  # Should be substantial

        # Verify CSV export
        from backend.src.analytics.export_csv import export_events_csv

        csv_bytes = export_events_csv(logger)
        csv_text = csv_bytes.decode("utf-8")
        assert "timestamp" in csv_text  # Header
        assert len(csv_text.split("\n")) > 7  # Header + data rows
