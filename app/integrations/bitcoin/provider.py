from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Protocol


@dataclass
class ChainEvent:
    event_type: str
    txid: str
    address: str
    value_sats: int
    block_height: int
    observed_at: datetime
    payload: dict[str, str | int | float]


class BitcoinProvider(Protocol):
    def recent_events(self) -> list[ChainEvent]:
        ...


class MockBitcoinProvider:
    def recent_events(self) -> list[ChainEvent]:
        return [
            ChainEvent(
                event_type="large_transfer",
                txid="deadbeef1234",
                address="bc1qexample",
                value_sats=1_500_000_000,
                block_height=900_000,
                observed_at=datetime.now(UTC),
                payload={"note": "mock event"},
            )
        ]
