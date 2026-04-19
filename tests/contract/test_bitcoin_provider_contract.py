from datetime import UTC

from app.core.config import Settings
from app.integrations.bitcoin.provider import (
    BitcoinProviderError,
    EsploraProvider,
    FallbackBitcoinProvider,
    MockBitcoinProvider,
    build_bitcoin_provider,
)


def test_mock_provider_returns_contract_compatible_events() -> None:
    provider = MockBitcoinProvider()

    events = provider.recent_events()

    assert events, "provider should return at least one event"
    event = events[0]
    assert event.event_type
    assert event.txid
    assert event.address.startswith("bc1")
    assert event.value_sats > 0
    assert event.block_height > 0
    assert event.observed_at.tzinfo == UTC
    assert isinstance(event.payload, dict)
    assert "note" in event.payload


def test_fallback_provider_uses_secondary_when_primary_fails() -> None:
    class BrokenProvider:
        def recent_events(self) -> list:  # type: ignore[override]
            raise RuntimeError("down")

    provider = FallbackBitcoinProvider([BrokenProvider(), MockBitcoinProvider()])

    events = provider.recent_events()

    assert events
    assert events[0].txid


def test_build_bitcoin_provider_returns_fallback_for_esplora_config() -> None:
    settings = Settings(BITCOIN_ESPLORA_URL="https://example.org", BITCOIN_PROVIDER_TIMEOUT_SECONDS=2)

    provider = build_bitcoin_provider(settings)

    assert isinstance(provider, FallbackBitcoinProvider)


def test_esplora_provider_contract_parses_recent_mempool_rows(monkeypatch) -> None:
    class FakeResponse:
        def __init__(self, *, text: str = "", json_data: list[dict[str, object]] | None = None) -> None:
            self.text = text
            self._json_data = json_data or []

        def raise_for_status(self) -> None:
            return

        def json(self) -> list[dict[str, object]]:
            return self._json_data

    class FakeClient:
        def __init__(self, *args, **kwargs) -> None:  # noqa: ANN002, ANN003
            pass

        def __enter__(self) -> "FakeClient":
            return self

        def __exit__(self, exc_type, exc, tb) -> None:  # noqa: ANN001, ANN002, ANN003
            return

        def get(self, url: str) -> FakeResponse:
            if url.endswith("/blocks/tip/height"):
                return FakeResponse(text="910001")
            if url.endswith("/mempool/recent"):
                return FakeResponse(json_data=[{"txid": "abc123", "fee": 4200}])
            raise AssertionError(f"Unexpected URL {url}")

    monkeypatch.setattr("app.integrations.bitcoin.provider.httpx.Client", FakeClient)

    events = EsploraProvider(base_url="https://esplora.example").recent_events()

    assert len(events) == 1
    assert events[0].txid == "abc123"
    assert events[0].block_height == 910001
    assert events[0].payload["provider"] == "esplora"
    assert events[0].payload["fee_sats"] == 4200


def test_esplora_provider_raises_error_on_unavailable_backend(monkeypatch) -> None:
    class BrokenClient:
        def __init__(self, *args, **kwargs) -> None:  # noqa: ANN002, ANN003
            pass

        def __enter__(self) -> "BrokenClient":
            return self

        def __exit__(self, exc_type, exc, tb) -> None:  # noqa: ANN001, ANN002, ANN003
            return

        def get(self, url: str) -> object:
            raise RuntimeError("network down")

    monkeypatch.setattr("app.integrations.bitcoin.provider.httpx.Client", BrokenClient)

    provider = EsploraProvider(base_url="https://esplora.example")
    try:
        provider.recent_events()
        assert False, "Expected BitcoinProviderError"
    except BitcoinProviderError:
        assert True
