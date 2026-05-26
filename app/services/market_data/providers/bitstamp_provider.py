from __future__ import annotations

import time
from datetime import UTC, datetime

import httpx

from app.services.market_data.base import MarketDataProvider
from app.services.market_data.normalization import payload_hash
from app.services.market_data.provider_models import NormalizedBTCPricePoint


class BitstampProvider(MarketDataProvider):
    def get_provider_name(self) -> str:
        return "bitstamp"

    def get_provider_metadata(self) -> dict[str, object]:
        return {"endpoint": "https://www.bitstamp.net/api/v2/ticker/btcusd/"}

    def fetch_ticker(self) -> NormalizedBTCPricePoint:
        start = time.perf_counter()
        response = httpx.get(str(self.get_provider_metadata()["endpoint"]), timeout=10)
        response.raise_for_status()
        data = response.json()
        latency_ms = int((time.perf_counter() - start) * 1000)
        return NormalizedBTCPricePoint("bitstamp", "BTCUSD", float(data["last"]), datetime.now(UTC), latency_ms, 0.8, payload_hash(response.text), {})

    def fetch_recent_prices(self) -> list[NormalizedBTCPricePoint]:
        return [self.fetch_ticker()]
