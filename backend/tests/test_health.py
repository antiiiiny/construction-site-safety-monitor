"""Stage 0 smoke test — verifies the FastAPI app boots and /health works.

Run with: pytest backend/tests/test_health.py
"""

from fastapi.testclient import TestClient

from backend.src.api.main import app


def test_health_endpoint() -> None:
    """The /health endpoint should return 200 and {"status": "ok"}."""
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_app_metadata() -> None:
    """The FastAPI app should have a title and version set."""
    assert app.title == "Construction Site Safety Monitor API"
    assert app.version == "0.1.0"
