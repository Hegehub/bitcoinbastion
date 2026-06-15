from __future__ import annotations

from typing import Any

import reflex as rx

from bastion_ui.services.api_client import normalize_api_error
from bastion_ui.services.wow_client import (
    get_api_contract_preview,
    get_audit_replay_preview,
    get_command_center_summary,
    get_market_intelligence_preview,
    get_provider_trust_matrix,
    get_sovereign_grid_preview,
    get_trace_wow_summary,
)


class WowState(rx.State):
    loading: bool = False
    error: str = ""
    degraded: bool = True
    preview_mode: bool = True
    command_center: dict[str, Any] = {}
    provider_matrix: dict[str, Any] = {}
    trace_wow_summary: dict[str, Any] = {}
    market_preview: dict[str, Any] = {}
    sovereign_grid: dict[str, Any] = {}
    audit_preview: dict[str, Any] = {}
    api_contracts: dict[str, Any] = {}

    async def _load(self, field: str, loader: Any) -> None:
        self.loading = True
        self.error = ""
        try:
            setattr(self, field, await loader())
            self.degraded = True
            self.preview_mode = True
        except Exception as exc:
            self.error = normalize_api_error(exc)
        finally:
            self.loading = False

    async def load_command_center(self) -> None:
        await self._load("command_center", get_command_center_summary)

    async def load_trace_wow_summary(self, report_id: str) -> None:
        await self._load("trace_wow_summary", lambda: get_trace_wow_summary(report_id))

    async def load_provider_matrix(self) -> None:
        await self._load("provider_matrix", get_provider_trust_matrix)

    async def load_market_preview(self) -> None:
        await self._load("market_preview", get_market_intelligence_preview)

    async def load_sovereign_grid(self) -> None:
        await self._load("sovereign_grid", get_sovereign_grid_preview)

    async def load_audit_preview(self) -> None:
        await self._load("audit_preview", get_audit_replay_preview)

    async def load_api_contracts(self) -> None:
        await self._load("api_contracts", get_api_contract_preview)
