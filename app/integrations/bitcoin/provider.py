from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Protocol

import httpx

from app.core.config import Settings

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


class BitcoinProviderError(RuntimeError):
    pass


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


class EsploraProvider:
    def __init__(self, *, base_url: str, timeout_seconds: float = 6.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds

    def recent_events(self) -> list[ChainEvent]:
        try:
            with httpx.Client(timeout=self.timeout_seconds) as client:
                tip_resp = client.get(f"{self.base_url}/blocks/tip/height")
                tip_resp.raise_for_status()
                tip_height = int(tip_resp.text.strip())

                mempool_resp = client.get(f"{self.base_url}/mempool/recent")
                mempool_resp.raise_for_status()
                rows = mempool_resp.json()
        except Exception as exc:  # noqa: BLE001
            raise BitcoinProviderError("esplora provider unavailable") from exc

        events: list[ChainEvent] = []
        for row in rows[:10]:
            txid = str(row.get("txid", ""))
            if not txid:
                continue
            fee_sats = int(row.get("fee", 0) or 0)
            events.append(
                ChainEvent(
                    event_type="mempool_recent_tx",
                    txid=txid,
                    address="bc1qesplora",
                    value_sats=max(fee_sats * 100, 1),
                    block_height=tip_height,
                    observed_at=datetime.now(UTC),
                    payload={"provider": "esplora", "fee_sats": fee_sats},
                )
            )
        if events:
            return events
        raise BitcoinProviderError("esplora returned no parseable events")


class FallbackBitcoinProvider:
    def __init__(self, providers: list[BitcoinProvider]) -> None:
        self.providers = providers

    def recent_events(self) -> list[ChainEvent]:
        last_error: Exception | None = None
        for provider in self.providers:
            try:
                events = provider.recent_events()
                if events:
                    return events
            except Exception as exc:  # noqa: BLE001
                last_error = exc
        if last_error is not None:
            raise BitcoinProviderError("all bitcoin providers failed") from last_error
        return []


def build_bitcoin_provider(settings: Settings) -> BitcoinProvider:
    if settings.bitcoin_esplora_url:
        return FallbackBitcoinProvider(
            [
                EsploraProvider(
                    base_url=settings.bitcoin_esplora_url,
                    timeout_seconds=settings.bitcoin_provider_timeout_seconds,
                ),
                MockBitcoinProvider(),
            ]
        )
    return MockBitcoinProvider()
