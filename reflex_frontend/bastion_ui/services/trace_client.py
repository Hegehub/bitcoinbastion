from __future__ import annotations

from typing import Any

from bastion_ui.services.api_client import BastionApiClient
from bastion_ui.services.models import TraceLiteResult

TRACE_LITE_ENDPOINT = "/api/v1/trace/lite/{address}"


def normalize_trace_lite_payload(address: str, payload: Any) -> TraceLiteResult:
    data = payload if isinstance(payload, dict) else {}
    report_id = data.get("report_id") or data.get("id")
    risk_band = data.get("risk_band") or data.get("status") or data.get("risk_level")
    confidence = data.get("confidence")
    summary = data.get("summary") or data.get("message") or data.get("description")
    raw_providers = data.get("providers")
    providers: list[Any] = raw_providers if isinstance(raw_providers, list) else []
    raw_sources = data.get("sources")
    sources: list[Any] = raw_sources if isinstance(raw_sources, list) else []
    raw_limitations = data.get("limitations")
    limitations: list[Any] = raw_limitations if isinstance(raw_limitations, list) else []
    raw_warnings = data.get("warnings")
    warnings: list[Any] = raw_warnings if isinstance(raw_warnings, list) else []
    return TraceLiteResult(
        address=str(data.get("address") or address),
        report_id=report_id,
        risk_band=str(risk_band) if risk_band is not None else None,
        confidence=float(confidence) if isinstance(confidence, int | float) else None,
        summary=str(summary) if summary is not None else None,
        provider_count=data.get("provider_count")
        if isinstance(data.get("provider_count"), int)
        else len(providers) or None,
        source_count=data.get("source_count")
        if isinstance(data.get("source_count"), int)
        else len(sources) or None,
        degraded=bool(data.get("degraded") or data.get("is_degraded") or False),
        limitations=[str(item) for item in limitations],
        warnings=[str(item) for item in warnings],
        generated_at=str(data.get("generated_at"))
        if data.get("generated_at") is not None
        else None,
    )


class TraceApiClient:
    def __init__(self, api_client: BastionApiClient | None = None) -> None:
        self.api_client = api_client or BastionApiClient()

    async def get_trace_lite(self, address: str) -> TraceLiteResult:
        payload = await self.api_client.get(TRACE_LITE_ENDPOINT.format(address=address))
        return normalize_trace_lite_payload(address, payload)

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
