from fastapi.testclient import TestClient

from app.main import app


def test_onchain_events_returns_paginated_envelope() -> None:
    client = TestClient(app)

    response = client.get("/api/v1/onchain/events")

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert set(payload["data"].keys()) == {"items", "total", "limit", "offset"}
    assert isinstance(payload["data"]["items"], list)
