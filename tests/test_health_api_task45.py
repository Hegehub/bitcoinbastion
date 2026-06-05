from fastapi.testclient import TestClient

from app.main import app


def test_health_api_contracts_task45() -> None:
    client = TestClient(app)
    for path in [
        "/api/v1/health",
        "/api/v1/health/providers",
        "/api/v1/health/jobs",
        "/api/v1/health/runtime",
        "/api/v1/health/degraded",
        "/api/v1/metrics/status",
    ]:
        response = client.get(path)
        assert response.status_code == 200


def test_readiness_and_liveness_contracts_task45() -> None:
    client = TestClient(app)
    assert client.get("/api/v1/health/live").status_code == 200
    ready = client.get("/api/v1/health/ready")
    assert ready.status_code == 200
    assert "provider_layer" in ready.json()["details"]
