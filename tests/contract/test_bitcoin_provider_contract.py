from datetime import UTC

from app.integrations.bitcoin.provider import MockBitcoinProvider


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
