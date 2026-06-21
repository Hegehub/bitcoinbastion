from __future__ import annotations

from typing import Any

from bastion_ui.services.api_client import BastionApiClient


class TraceApiClient:
    def __init__(self, api_client: BastionApiClient | None = None) -> None:
        self.api_client = api_client or BastionApiClient()

    async def get_trace_lite(self, address: str) -> Any:
        return await self.api_client.get(f"/api/v1/trace/lite/{address}")

    async def get_trace_address(self, address: str) -> Any:
        return await self.api_client.get(f"/api/v1/trace/address/{address}")

    async def get_trace_report(self, report_id: str) -> Any:
        return await self.api_client.get(f"/api/v1/trace/report/{report_id}")

    async def get_trace_evidence(self, report_id: str) -> Any:
        return await self.api_client.get(f"/api/v1/trace/report/{report_id}/evidence")

    async def get_origin_passport(self, report_id: str) -> Any:
        return await self.api_client.get(f"/api/v1/trace/report/{report_id}/origin-passport")

    async def get_privacy_shield(self, report_id: str) -> Any:
        return await self.api_client.get(f"/api/v1/trace/report/{report_id}/privacy-shield")

    async def get_source_summary(self, report_id: str) -> Any:
        return await self.api_client.get(f"/api/v1/trace/report/{report_id}/source-summary")

    async def get_provider_disagreement(self, report_id: str) -> Any:
        return await self.api_client.get(f"/api/v1/trace/report/{report_id}/provider-disagreement")

    async def get_utxo_hygiene(self, report_id: str) -> Any:
        return await self.api_client.get(f"/api/v1/trace/report/{report_id}/utxo-hygiene")

    async def get_dust_radar(self, report_id: str) -> Any:
        return await self.api_client.get(f"/api/v1/trace/report/{report_id}/dust-radar")

    async def get_counterparty_lens(self, report_id: str) -> Any:
        return await self.api_client.get(f"/api/v1/trace/report/{report_id}/counterparty-lens")

    async def get_policy_facts(self, report_id: str) -> Any:
        return await self.api_client.get(f"/api/v1/trace/report/{report_id}/policy-facts")
