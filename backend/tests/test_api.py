"""Tests for the FastAPI API layer.

Tests cover all endpoints using FastAPI's TestClient:
  - GET /health
  - GET /api/zones
  - POST /api/scan (mocked pipeline)
  - GET /api/metrics
  - GET /api/kpi
  - GET /api/events
  - GET /api/charts/*
  - GET /api/hotspots
  - GET /api/export/csv
  - POST /api/clear
  - POST /api/tts (mocked TTS)
  - GET /api/report (placeholder PDF)
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient

from backend.src.api.main import app

client = TestClient(app)


class TestHealth:
    """Tests for /health endpoint."""

    def test_health(self) -> None:
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


class TestZones:
    """Tests for GET /api/zones."""

    def test_get_zones(self) -> None:
        response = client.get("/api/zones")
        assert response.status_code == 200
        zones = response.json()
        assert len(zones) == 6
        assert zones[0]["zone_id"] == 1
        assert zones[0]["name"] == "Entry Gate"
        assert "helmet" in zones[0]["required_ppe"]
        assert zones[2]["name"] == "Welding Zone"
        assert "gloves" in zones[2]["required_ppe"]


class TestScan:
    """Tests for POST /api/scan."""

    def test_scan_invalid_zone(self) -> None:
        """Invalid zone_id should return 400."""
        response = client.post(
            "/api/scan",
            data={"zone_id": 99},
            files={"image": ("test.jpg", b"fake_image", "image/jpeg")},
        )
        assert response.status_code == 400

    def test_scan_empty_image(self) -> None:
        """Empty image should return 400."""
        response = client.post(
            "/api/scan",
            data={"zone_id": 1},
            files={"image": ("test.jpg", b"", "image/jpeg")},
        )
        assert response.status_code == 400

    def test_scan_success(self) -> None:
        """Successful scan with mocked pipeline."""
        mock_result = {
            "zone_id": 1,
            "zone_name": "Entry Gate",
            "detections": [
                {"class_name": "person", "confidence": 0.95, "bbox": [100, 100, 300, 600]},
                {"class_name": "helmet", "confidence": 0.88, "bbox": [150, 80, 250, 180]},
            ],
            "violations": [],
            "tts_message": "",
            "tts_audio_available": False,
            "detection_count": 2,
            "violation_count": 0,
        }
        with patch("backend.src.api.routes.detection.run_zone_pipeline", return_value=mock_result):
            response = client.post(
                "/api/scan",
                data={"zone_id": 1},
                files={"image": ("test.jpg", b"fake_image_data", "image/jpeg")},
            )
        assert response.status_code == 200
        data = response.json()
        assert data["zone_id"] == 1
        assert data["zone_name"] == "Entry Gate"
        assert data["detection_count"] == 2
        assert data["violation_count"] == 0


class TestMetrics:
    """Tests for analytics endpoints."""

    def test_get_metrics(self) -> None:
        response = client.get("/api/metrics")
        assert response.status_code == 200
        data = response.json()
        assert "total_scans" in data
        assert "total_violations" in data
        assert "compliance_rate" in data

    def test_get_kpi(self) -> None:
        response = client.get("/api/kpi")
        assert response.status_code == 200
        data = response.json()
        assert "total_scans" in data
        assert "total_violations" in data

    def test_get_events(self) -> None:
        response = client.get("/api/events")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_get_events_with_limit(self) -> None:
        response = client.get("/api/events?limit=5")
        assert response.status_code == 200

    def test_get_violations_per_zone_chart(self) -> None:
        response = client.get("/api/charts/violations-per-zone")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 6  # all zones

    def test_get_violations_per_ppe_chart(self) -> None:
        response = client.get("/api/charts/violations-per-ppe")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_get_timeline(self) -> None:
        response = client.get("/api/charts/timeline")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_get_hotspots(self) -> None:
        response = client.get("/api/hotspots")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_export_csv(self) -> None:
        response = client.get("/api/export/csv")
        assert response.status_code == 200
        assert "text/csv" in response.headers.get("content-type", "")

    def test_export_summary_csv(self) -> None:
        response = client.get("/api/export/summary-csv")
        assert response.status_code == 200
        assert "text/csv" in response.headers.get("content-type", "")

    def test_clear_session(self) -> None:
        response = client.post("/api/clear")
        assert response.status_code == 200
        assert response.json()["status"] == "cleared"

    def test_simulate_session(self) -> None:
        """Simulate endpoint should populate the event log with mock data."""
        response = client.post("/api/simulate?num_scans=12")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "simulated"
        assert data["total_scans"] == 12
        assert data["total_violations"] > 0
        assert 0.0 <= data["compliance_rate"] <= 1.0

    def test_simulate_then_metrics(self) -> None:
        """After simulation, metrics should reflect the mock data."""
        client.post("/api/simulate?num_scans=12")
        response = client.get("/api/metrics")
        assert response.status_code == 200
        data = response.json()
        assert data["total_scans"] == 12


class TestTTS:
    """Tests for POST /api/tts."""

    def test_tts_success(self) -> None:
        """TTS endpoint should return audio when engine succeeds."""
        mock_engine = MagicMock()
        mock_engine.generate_audio = AsyncMock(return_value=b"fake_mp3_data")

        with patch("backend.src.api.routes.alerts.get_tts_engine", return_value=mock_engine):
            response = client.post(
                "/api/tts",
                json={"message": "Attention, Entry Gate. Hard hat is required."},
            )
        assert response.status_code == 200
        assert response.headers["content-type"] == "audio/mpeg"
        assert response.content == b"fake_mp3_data"

    def test_tts_empty_message(self) -> None:
        """Empty message should return 422 (validation error)."""
        response = client.post("/api/tts", json={"message": ""})
        assert response.status_code == 422

    def test_tts_engine_failure(self) -> None:
        """If TTS engine returns None, should return 503."""
        mock_engine = MagicMock()
        mock_engine.generate_audio = AsyncMock(return_value=None)

        with patch("backend.src.api.routes.alerts.get_tts_engine", return_value=mock_engine):
            response = client.post("/api/tts", json={"message": "Test message"})
        assert response.status_code == 503


class TestReport:
    """Tests for GET /api/report."""

    def test_get_report(self) -> None:
        """Report endpoint should return a PDF."""
        response = client.get("/api/report")
        assert response.status_code == 200
        assert "application/pdf" in response.headers.get("content-type", "")
        assert len(response.content) > 0

    def test_get_report_with_site_name(self) -> None:
        """Report should accept a site_name query param."""
        response = client.get("/api/report?site_name=Test%20Site")
        assert response.status_code == 200
