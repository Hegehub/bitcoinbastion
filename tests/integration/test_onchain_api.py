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


def test_onchain_state_uses_repository_height_when_query_missing(monkeypatch) -> None:
    from app.db.repositories.onchain_repository import OnchainRepository

    monkeypatch.setattr(OnchainRepository, "latest_block_height", lambda self: 123_456)

    client = TestClient(app)
    response = client.get("/api/v1/onchain/state")

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["observed_block_height"] == 123_456
    assert payload["data"]["tip_height"] == 123_457
    assert payload["data"]["explainability"]["data_source"] == "repository_fallback"
