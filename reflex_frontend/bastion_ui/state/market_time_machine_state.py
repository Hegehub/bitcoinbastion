from __future__ import annotations

from typing import Any

import reflex as rx

from bastion_ui.services.market_client import MarketApiClient
from bastion_ui.services.models import ApiResult


def _items_from_result(result: ApiResult, *keys: str) -> list[dict[str, Any]]:
    if not result.ok or not isinstance(result.data, dict):
        return []
    for key in keys:
        value = result.data.get(key)
        if isinstance(value, list):
            return [item for item in value if isinstance(item, dict)]
    return []


class MarketTimeMachineState(rx.State):
    loading: bool = False
    error: str = ""
    degraded: bool = True
    last_updated: str = "Not available"
    selected_asset: str = "BTC"
    selected_time_range: str = "24h"
    selected_section: str = "time-machine"
    market_regime: dict[str, Any] = {}
    timeline_events: list[dict[str, Any]] = []
    signals: list[dict[str, Any]] = []
    evidence_packets: list[dict[str, Any]] = []
    narratives: list[dict[str, Any]] = []
    sources: list[dict[str, Any]] = []
    selected_candle_id: str = ""
    selected_evidence_packet_id: str = ""

    async def load_time_machine(self) -> None:
        self.loading = True
        self.error = ""
        result = await MarketApiClient().get_time_machine()
        self.degraded = result.degraded or not result.ok
        if result.ok and isinstance(result.data, dict):
            self.timeline_events = _items_from_result(result, "timeline_items", "timeline")
            self.signals = _items_from_result(result, "signals", "signal_summary")
            self.evidence_packets = _items_from_result(result, "evidence", "evidence_packets")
            self.narratives = _items_from_result(result, "narratives", "narrative_panel")
            self.sources = _items_from_result(result, "sources", "source_summary")
            self.market_regime = result.data.get("market_regime", {}) if isinstance(
                result.data.get("market_regime"), dict
            ) else {}
            self.last_updated = str(
                result.data.get("generated_at")
                or result.data.get("last_updated")
                or "Not available"
            )
        else:
            self.error = result.error or "Market Time Machine data unavailable."
        self.loading = False

    async def load_timeline(self) -> None:
        result = await MarketApiClient().get_timeline()
        self.timeline_events = _items_from_result(result, "timeline_items", "items", "events")
        self.degraded = result.degraded or not result.ok
        self.error = "" if result.ok else result.error or "Market timeline unavailable."

    async def load_signals(self) -> None:
        result = await MarketApiClient().get_market_signals()
        self.signals = _items_from_result(result, "signals", "items", "data")
        self.degraded = result.degraded or not result.ok
        self.error = "" if result.ok else result.error or "Market signals unavailable."

    async def load_evidence(self) -> None:
        result = await MarketApiClient().get_market_evidence()
        self.evidence_packets = _items_from_result(result, "items", "packets", "data")
        self.degraded = result.degraded or not result.ok
        self.error = "" if result.ok else result.error or "Market evidence unavailable."

    async def load_narratives(self) -> None:
        result = await MarketApiClient().get_market_narratives()
        self.narratives = _items_from_result(result, "narratives", "items", "data")
        self.degraded = result.degraded or not result.ok
        self.error = "" if result.ok else result.error or "Market narratives unavailable."

    async def load_sources(self) -> None:
        result = await MarketApiClient().get_market_sources()
        self.sources = _items_from_result(result, "sources", "items", "data")
        self.degraded = result.degraded or not result.ok
        self.error = "" if result.ok else result.error or "Market sources unavailable."

    def set_selected_asset(self, value: str) -> None:
        self.selected_asset = value or "BTC"

    def set_selected_time_range(self, value: str) -> None:
        self.selected_time_range = value or "24h"

    def set_selected_candle(self, value: str) -> None:
        self.selected_candle_id = value

    def set_selected_evidence_packet(self, value: str) -> None:
        self.selected_evidence_packet_id = value

    def clear_error(self) -> None:
        self.error = ""

    async def refresh(self) -> None:
        if self.selected_section == "timeline":
            await self.load_timeline()
        elif self.selected_section == "signals":
            await self.load_signals()
        elif self.selected_section == "evidence":
            await self.load_evidence()
        elif self.selected_section == "narratives":
            await self.load_narratives()
        elif self.selected_section == "sources":
            await self.load_sources()
        else:
            await self.load_time_machine()
