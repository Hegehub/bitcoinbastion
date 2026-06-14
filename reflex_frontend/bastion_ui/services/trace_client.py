from __future__ import annotations

from typing import Any, cast

from bastion_ui.services.api_client import api_get


async def get_trace_lite(address: str) -> dict[str, Any]:
    return cast(dict[str, Any], await api_get(f"/api/v1/trace/lite/{address}"))


async def get_public_trace_summary(report_id: str | int) -> dict[str, Any]:
    return cast(dict[str, Any], await api_get(f"/api/v1/public/trace/{report_id}/summary"))


async def get_trace_report(report_id: str | int) -> dict[str, Any]:
    return cast(dict[str, Any], await api_get(f"/api/v1/trace/report/{report_id}"))


async def get_trace_evidence(report_id: str | int) -> list[dict[str, Any]]:
    return cast(list[dict[str, Any]], await api_get(f"/api/v1/trace/report/{report_id}/evidence"))


async def get_privacy_shield(report_id: str | int) -> dict[str, Any]:
    return cast(dict[str, Any], await api_get(f"/api/v1/trace/report/{report_id}/privacy-shield"))


async def get_origin_passport(report_id: str | int) -> dict[str, Any]:
    return cast(dict[str, Any], await api_get(f"/api/v1/trace/report/{report_id}/origin-passport"))


async def get_provider_disagreement(report_id: str | int) -> dict[str, Any]:
    return cast(dict[str, Any], await api_get(f"/api/v1/trace/report/{report_id}/provider-disagreement"))


async def get_counterparty_lens(report_id: str | int) -> dict[str, Any]:
    return cast(dict[str, Any], await api_get(f"/api/v1/trace/report/{report_id}/counterparty-lens"))


async def get_policy_facts(report_id: str | int) -> dict[str, Any]:
    return cast(dict[str, Any], await api_get(f"/api/v1/trace/report/{report_id}/policy-facts"))
