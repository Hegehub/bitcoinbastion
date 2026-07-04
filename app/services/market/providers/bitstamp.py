from __future__ import annotations

import time
from datetime import UTC, datetime

import httpx

from app.services.market.exceptions import ProviderPayloadError
from app.services.market.providers.base import BaseMarketProvider
from app.services.market.schemas import ProviderPrice


class BitstampProvider(BaseMarketProvider):
    def provider_name(self) -> str:
        return "bitstamp"

    def fetch_btc_price(self) -> ProviderPrice:
        start = time.perf_counter()
        response = httpx.get("https://www.bitstamp.net/api/v2/ticker/btcusd/", timeout=10)
        response.raise_for_status()
        data = response.json()
        price = float(data["last"])
        if price <= 0:
            raise ProviderPayloadError("negative price")
        return ProviderPrice(
            "bitstamp",
            "BTCUSD",
            price,
            datetime.now(UTC),
            int((time.perf_counter() - start) * 1000),
            data,
        )

    def healthcheck(self) -> bool:
        try:
            self.fetch_btc_price()
            return True
        except Exception:
            return False
