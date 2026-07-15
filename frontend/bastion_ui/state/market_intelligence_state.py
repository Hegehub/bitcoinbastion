from __future__ import annotations

from typing import Any

import reflex as rx

from bastion_ui.services.market_client import MarketApiClient

MARKET_INTELLIGENCE_MISSING = "Market intelligence endpoint unavailable."


class MarketIntelligenceState(rx.State):
    loading: bool = False
    error: str | None = None
    data: dict[str, Any] = {}
    degraded: bool = True
    last_updated: str = "Not available"

    async def refresh(self) -> None:
        self.loading = True
        result = await MarketApiClient().get_market_dashboard()
        if result.ok and isinstance(result.data, dict):
            self.data = result.data
            self.error = None
            self.degraded = result.degraded
        else:
            self.data = {"available": False, "reason": MARKET_INTELLIGENCE_MISSING}
            self.error = result.error
            self.degraded = True
        self.loading = False

    def clear_error(self) -> None:
        self.error = None
