from __future__ import annotations

import time
from datetime import UTC, datetime

import httpx

from app.services.market.exceptions import ProviderPayloadError
from app.services.market.providers.base import BaseMarketProvider
from app.services.market.schemas import ProviderPrice


class KrakenProvider(BaseMarketProvider):
    def provider_name(self) -> str:
        return "kraken"

    def fetch_btc_price(self) -> ProviderPrice:
        start = time.perf_counter()
        response = httpx.get("https://api.kraken.com/0/public/Ticker?pair=XBTUSD", timeout=10)
        response.raise_for_status()
        data = response.json()
        key = next(iter(data.get("result", {}).keys()), None)
        if key is None:
            raise ProviderPayloadError("missing kraken result")
        price = float(data["result"][key]["c"][0])
        if price <= 0:
            raise ProviderPayloadError("negative price")
        return ProviderPrice("kraken", "XBTUSD", price, datetime.now(UTC), int((time.perf_counter() - start) * 1000), data)

    def healthcheck(self) -> bool:
        try:
            self.fetch_btc_price()
            return True
        except Exception:
            return False
