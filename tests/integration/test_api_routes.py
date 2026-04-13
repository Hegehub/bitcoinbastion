from fastapi.testclient import TestClient

from app.main import app


def test_new_api_groups_exist() -> None:
    client = TestClient(app)
    assert client.get("/api/v1/admin/status").status_code == 200
    assert client.get("/api/v1/onchain/events").status_code == 200
    assert client.get("/api/v1/entities").status_code == 200
    assert client.get("/api/v1/fees/snapshot").status_code == 200
