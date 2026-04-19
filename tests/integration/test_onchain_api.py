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


def test_onchain_state_can_probe_provider_for_tip_height(monkeypatch) -> None:
    from app.api.v1 import onchain as onchain_api
    from app.db.repositories.onchain_repository import OnchainRepository
    from app.integrations.bitcoin.provider import ChainEvent
    from datetime import UTC, datetime

    class FakeProvider:
        def recent_events(self) -> list[ChainEvent]:
            return [
                ChainEvent(
                    event_type="mempool_recent_tx",
                    txid="probe123",
                    address="bc1qprobe",
                    value_sats=10_000,
                    block_height=555_000,
                    observed_at=datetime.now(UTC),
                    payload={"provider": "fake"},
                )
            ]

    monkeypatch.setattr(OnchainRepository, "latest_block_height", lambda self: 123_456)
    monkeypatch.setattr(onchain_api, "build_bitcoin_provider", lambda settings: FakeProvider())

    client = TestClient(app)
    response = client.get("/api/v1/onchain/state", params={"provider_probe": True})

    assert response.status_code == 200
    payload = response.json()
    assert payload["data"]["tip_height"] == 555_000
    assert payload["data"]["explainability"]["data_source"] == "provider_probe"


def test_onchain_state_provider_probe_falls_back_when_provider_fails(monkeypatch) -> None:
    from app.api.v1 import onchain as onchain_api
    from app.db.repositories.onchain_repository import OnchainRepository
    from app.integrations.bitcoin.provider import BitcoinProviderError

    class BrokenProvider:
        def recent_events(self) -> list[object]:
            raise BitcoinProviderError("provider down")

    monkeypatch.setattr(OnchainRepository, "latest_block_height", lambda self: 333_000)
    monkeypatch.setattr(onchain_api, "build_bitcoin_provider", lambda settings: BrokenProvider())

    client = TestClient(app)
    response = client.get("/api/v1/onchain/state", params={"provider_probe": True})

    assert response.status_code == 200
    payload = response.json()
    assert payload["data"]["tip_height"] == 333_001
    assert payload["data"]["explainability"]["data_source"] == "repository_fallback"


def test_onchain_state_provider_probe_emits_metrics(monkeypatch) -> None:
    from app.api.v1 import onchain as onchain_api
    from app.db.repositories.onchain_repository import OnchainRepository
    from app.integrations.bitcoin.provider import ChainEvent
    from datetime import UTC, datetime

    class FakeProvider:
        def recent_events(self) -> list[ChainEvent]:
            return [
                ChainEvent(
                    event_type="mempool_recent_tx",
                    txid="metrics123",
                    address="bc1qmetrics",
                    value_sats=11_000,
                    block_height=444_444,
                    observed_at=datetime.now(UTC),
                    payload={"provider": "fake"},
                )
            ]

    monkeypatch.setattr(OnchainRepository, "latest_block_height", lambda self: 111_000)
    monkeypatch.setattr(onchain_api, "build_bitcoin_provider", lambda settings: FakeProvider())

    client = TestClient(app)
    assert client.get("/api/v1/onchain/state", params={"provider_probe": True}).status_code == 200

    metrics = client.get("/metrics")
    assert metrics.status_code == 200
    assert "onchain_provider_probe_events_total" in metrics.text
