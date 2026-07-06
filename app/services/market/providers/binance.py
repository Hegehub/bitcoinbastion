from __future__ import annotations

import time
from datetime import UTC, datetime

import httpx

from app.services.market.exceptions import ProviderPayloadError
from app.services.market.providers.base import BaseMarketProvider
from app.services.market.schemas import ProviderPrice


class BinanceProvider(BaseMarketProvider):
    def provider_name(self) -> str:
        return "binance"

    def fetch_btc_price(self) -> ProviderPrice:
        start = time.perf_counter()
        r = httpx.get("https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT", timeout=10)
        r.raise_for_status()
        d = r.json()
        try:
            price = float(d["price"])
        except Exception as exc:
            raise ProviderPayloadError("invalid binance payload") from exc
        if price <= 0:
            raise ProviderPayloadError("negative price")
        return ProviderPrice(
            "binance",
            "BTCUSDT",
            price,
            datetime.now(UTC),
            int((time.perf_counter() - start) * 1000),
            d,
        )

    def healthcheck(self) -> bool:
        try:
            self.fetch_btc_price()
            return True
        except Exception:
            return False
