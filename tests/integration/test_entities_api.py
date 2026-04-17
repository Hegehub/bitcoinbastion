from fastapi.testclient import TestClient

from app.main import app


def test_entities_endpoint_returns_paginated_envelope() -> None:
    client = TestClient(app)

    response = client.get("/api/v1/entities")

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert set(payload["data"].keys()) == {"items", "total", "limit", "offset"}


def test_entities_watchlist_requires_authentication() -> None:
    client = TestClient(app)

    response = client.get("/api/v1/entities/watchlist")

    assert response.status_code in {401, 403}
