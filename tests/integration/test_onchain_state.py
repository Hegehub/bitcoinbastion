from datetime import UTC, datetime

from fastapi.testclient import TestClient

from app.integrations.bitcoin.provider import BitcoinProviderError, ChainEvent
from app.main import app


def test_onchain_state_provider_probe_adds_confidence_and_freshness(monkeypatch) -> None:
    from app.api.v1 import onchain as onchain_api
    from app.db.repositories.onchain_repository import OnchainRepository

    class FakeProvider:
        def recent_events(self) -> list[ChainEvent]:
            return [
                ChainEvent(
                    event_type="mempool_recent_tx",
                    txid="probe-1",
                    address="bc1qprobe",
                    value_sats=1000,
                    block_height=777_000,
                    observed_at=datetime.now(UTC),
                    payload={"provider": "fake"},
                )
            ]

    monkeypatch.setattr(OnchainRepository, "latest_block_height", lambda self: 776_990)
    monkeypatch.setattr(onchain_api, "build_bitcoin_provider", lambda settings: FakeProvider())

    response = TestClient(app).get("/api/v1/onchain/state", params={"provider_probe": True})
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["explainability"]["data_source"] == "provider_probe"
    assert data["confidence_score"] <= 0.95
    assert data["freshness"]["provider_freshness_band"] in {"fresh", "aging", "stale", "very_stale", "unknown"}


def test_onchain_state_provider_failure_degrades_confidence(monkeypatch) -> None:
    from app.api.v1 import onchain as onchain_api
    from app.db.repositories.onchain_repository import OnchainRepository

    class BrokenProvider:
        def recent_events(self) -> list[object]:
            raise BitcoinProviderError("down")

    monkeypatch.setattr(OnchainRepository, "latest_block_height", lambda self: 333_000)
    monkeypatch.setattr(onchain_api, "build_bitcoin_provider", lambda settings: BrokenProvider())

    response = TestClient(app).get("/api/v1/onchain/state", params={"provider_probe": True})
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["explainability"]["data_source"] == "repository_fallback"
    assert data["freshness"]["source"] == "repository_fallback"
    assert data["confidence_score"] < 0.7
