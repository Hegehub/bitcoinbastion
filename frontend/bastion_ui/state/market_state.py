from __future__ import annotations

from typing import Any

import reflex as rx

from bastion_ui.services.market_client import MarketApiClient
from bastion_ui.services.models import ApiResult


def _as_dict(result: ApiResult) -> dict[str, Any]:
    return result.data if result.ok and isinstance(result.data, dict) else {}


class MarketState(rx.State):
    loading: bool = False
    error: str = ""
    market_status: dict[str, Any] = {}
    market_regime: dict[str, Any] = {}
    latest_signals: list[dict[str, Any]] = []
    provider_health: dict[str, Any] = {}
    evidence_summary: dict[str, Any] = {}
    freshness: dict[str, Any] = {}
    degraded_reasons: list[str] = ["Market dashboard has not loaded live backend data yet."]
    last_updated_at: str = "Not available"

    market_status_label: str = "Unavailable until backend dashboard data is loaded."
    market_regime_label: str = "Not available"
    market_regime_confidence: str = "Not available"
    market_regime_evidence_count: str = "Not available"
    latest_signals_label: str = "Latest signals are not connected yet."
    latest_signals_status: str = "Unavailable"
    provider_health_label: str = "Provider health is not connected yet."
    provider_health_status: str = "Unavailable"
    evidence_summary_label: str = "Evidence summary is not connected yet."
    evidence_summary_status: str = "Unavailable"
    freshness_label: str = "Freshness cannot be verified from Reflex until backend data loads."
    freshness_status: str = "Stale or unavailable"

    async def load_market_dashboard(self) -> None:
        self.loading = True
        self.error = ""
        client = MarketApiClient()
        dashboard = await client.get_market_dashboard()
        status = await client.get_market_status()
        self.market_status = _as_dict(dashboard)
        status_data = _as_dict(status)
        if dashboard.ok or status.ok:
            self.market_status_label = str(
                self.market_status.get("status") or status_data.get("status") or "Available"
            )
            self.last_updated_at = str(
                self.market_status.get("generated_at")
                or self.market_status.get("last_updated")
                or status_data.get("last_updated")
                or "Not available"
            )
            self.degraded_reasons = [] if not dashboard.degraded and not status.degraded else [
                "Backend reported degraded market data."
            ]
        else:
            self.error = dashboard.error or status.error or "Market dashboard data unavailable."
            self.degraded_reasons = [self.error]
        self.loading = False

    async def load_latest_signals(self) -> None:
        result = await MarketApiClient().get_latest_intelligence_signals()
        data = result.data
        if result.ok and isinstance(data, dict):
            raw = data.get("signals") or data.get("items") or data.get("data") or []
            self.latest_signals = raw if isinstance(raw, list) else []
            self.latest_signals_label = f"{len(self.latest_signals)} signal records returned."
            self.latest_signals_status = "Available" if self.latest_signals else "Empty"
        else:
            self.latest_signals = []
            self.latest_signals_label = result.error or "Latest signals endpoint unavailable."
            self.latest_signals_status = "Unavailable"

    async def load_provider_health(self) -> None:
        result = await MarketApiClient().get_provider_health()
        self.provider_health = _as_dict(result)
        if result.ok:
            self.provider_health_label = str(
                self.provider_health.get("status") or "Provider health returned by backend."
            )
            self.provider_health_status = "Available"
        else:
            self.provider_health_label = result.error or "Provider health endpoint unavailable."
            self.provider_health_status = "Unavailable"

    async def load_evidence_summary(self) -> None:
        result = await MarketApiClient().get_evidence_summary()
        self.evidence_summary = _as_dict(result)
        if result.ok:
            self.evidence_summary_label = "Evidence summary data returned by backend."
            self.evidence_summary_status = "Available"
        else:
            self.evidence_summary_label = result.error or "Evidence summary endpoint unavailable."
            self.evidence_summary_status = "Unavailable"

    async def refresh(self) -> None:
        await self.load_market_dashboard()
        await self.load_latest_signals()
        await self.load_provider_health()
        await self.load_evidence_summary()

    def clear_error(self) -> None:
        self.error = ""
