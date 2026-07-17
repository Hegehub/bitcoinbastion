from __future__ import annotations

from typing import Any

import reflex as rx

from bastion_ui.services.wow_client import UNAVAILABLE_REASON, WowApiClient

SAFE_UNAVAILABLE = {"available": False, "reason": UNAVAILABLE_REASON}


class WowState(rx.State):
    loading: bool = False
    error: str | None = None
    selected_module: str = "overview"
    degraded_states: list[str] = ["unavailable"]
    trace_radar_data: dict[str, Any] = SAFE_UNAVAILABLE
    evidence_chain_data: dict[str, Any] = SAFE_UNAVAILABLE
    provider_matrix_data: dict[str, Any] = SAFE_UNAVAILABLE
    node_pulse_data: dict[str, Any] = SAFE_UNAVAILABLE
    sovereignty_score_data: dict[str, Any] = SAFE_UNAVAILABLE
    market_wall_data: dict[str, Any] = SAFE_UNAVAILABLE

    async def load_wow_dashboard(self) -> None:
        self.loading = True
        await self.load_provider_matrix()
        await self.load_node_pulse()
        await self.load_market_wall()
        self.loading = False

    async def load_trace_radar(self, report_id: str) -> None:
        result = await WowApiClient().get_trace_radar(report_id)
        self.trace_radar_data = (
            result.data if result.ok and isinstance(result.data, dict) else SAFE_UNAVAILABLE
        )
        self.error = result.error

    async def load_evidence_chain(self, packet_id: str) -> None:
        result = await WowApiClient().get_evidence_chain(packet_id)
        self.evidence_chain_data = (
            result.data if result.ok and isinstance(result.data, dict) else SAFE_UNAVAILABLE
        )
        self.error = result.error

    async def load_provider_matrix(self) -> None:
        result = await WowApiClient().get_provider_matrix()
        self.provider_matrix_data = (
            result.data if result.ok and isinstance(result.data, dict) else SAFE_UNAVAILABLE
        )
        self.error = result.error

    async def load_node_pulse(self) -> None:
        result = await WowApiClient().get_node_pulse()
        self.node_pulse_data = (
            result.data if result.ok and isinstance(result.data, dict) else SAFE_UNAVAILABLE
        )
        self.error = result.error

    async def load_market_wall(self) -> None:
        result = await WowApiClient().get_market_wall()
        self.market_wall_data = (
            result.data if result.ok and isinstance(result.data, dict) else SAFE_UNAVAILABLE
        )
        self.error = result.error

    def set_selected_module(self, module: str) -> None:
        self.selected_module = module

    def clear_error(self) -> None:
        self.error = None
