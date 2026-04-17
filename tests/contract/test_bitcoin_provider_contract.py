from datetime import UTC

from app.core.config import Settings
from app.integrations.bitcoin.provider import (
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
