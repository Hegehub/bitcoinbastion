from __future__ import annotations

from typing import Any
from urllib.parse import quote

from bastion_ui.services.api_client import BastionApiClient
from bastion_ui.services.errors import (
    NOT_FOUND_PUBLIC_MESSAGE,
    BastionApiError,
    BastionApiNotFoundError,
)
from bastion_ui.services.models import ApiResult


def _q(value: str) -> str:
    return quote(value, safe="")


def _api_error_result(error: BastionApiError) -> ApiResult:
    return ApiResult(
        ok=False,
        data=None,
        error=error.public_message,
        status_code=error.status_code,
        degraded=True,
    )


async def _safe_get_result(path: str, client: BastionApiClient | None = None) -> ApiResult:
    try:
        data = await (client or BastionApiClient()).get(path)
    except BastionApiError as error:
        return _api_error_result(error)
    if isinstance(data, dict):
        degraded = bool(data.get("degraded") or data.get("stale") or data.get("partial"))
        return ApiResult(ok=True, data=data, degraded=degraded)
    if isinstance(data, list):
        return ApiResult(ok=True, data=data)
    if data is None:
        return ApiResult(ok=True, data=None, degraded=True)
    return ApiResult(
        ok=False, error="Evidence returned an unexpected response shape.", degraded=True
    )


async def get_evidence_packet(packet_id: str, client: BastionApiClient | None = None) -> Any:
    if not packet_id:
        raise BastionApiNotFoundError(
            "Evidence packet endpoint requires a packet identifier.",
            status_code=404,
            public_message=NOT_FOUND_PUBLIC_MESSAGE,
        )
    return await (client or BastionApiClient()).get(f"/web/evidence/{_q(packet_id)}")


async def get_trace_report_evidence(report_id: str, client: BastionApiClient | None = None) -> Any:
    return await (client or BastionApiClient()).get(
        f"/api/v1/trace/report/{_q(report_id)}/evidence"
    )


async def get_trace_evidence(report_id: str, client: BastionApiClient | None = None) -> ApiResult:
    return await _safe_get_result(f"/api/v1/trace/report/{_q(report_id)}/evidence", client)


async def get_proof_packet(report_id: str, client: BastionApiClient | None = None) -> ApiResult:
    return await _safe_get_result(f"/api/v1/trace/report/{_q(report_id)}/proof-packet", client)


async def get_provider_disagreement(
    report_id: str, client: BastionApiClient | None = None
) -> ApiResult:
    return await _safe_get_result(
        f"/api/v1/trace/report/{_q(report_id)}/provider-disagreement", client
    )


async def get_public_trace_summary(
    report_id: str, client: BastionApiClient | None = None
) -> ApiResult:
    return await _safe_get_result(f"/api/v1/public/trace/{_q(report_id)}/summary", client)
