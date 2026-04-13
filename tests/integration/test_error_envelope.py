from fastapi.testclient import TestClient

from app.main import app


def test_unauthorized_errors_use_standard_envelope() -> None:
    client = TestClient(app)
    response = client.get("/api/v1/users")
    assert response.status_code == 401
    body = response.json()
    assert body["success"] is False
    assert body["error"]["code"] == "unauthorized"
    assert "request_id" in body["error"]
