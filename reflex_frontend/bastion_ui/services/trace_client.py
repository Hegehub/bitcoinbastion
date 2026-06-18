from __future__ import annotations

from typing import Any
from urllib.parse import quote

from bastion_ui.services.api_client import BastionApiClient
from bastion_ui.services.errors import BastionApiError
from bastion_ui.services.models import ApiResult, TraceLiteResult

TRACE_LITE_ENDPOINT_TEMPLATE = "/api/v1/trace/lite/{address}"


def _q(value: str) -> str:
    return quote(value, safe="")


def _as_float(value: Any) -> float | None:
    if isinstance(value, int | float):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value)
        except ValueError:
            return None
    return None


def normalize_trace_lite_payload(payload: Any, *, address: str) -> TraceLiteResult:
    if not isinstance(payload, dict):
        return TraceLiteResult(
            address=address,
            degraded=True,
            summary="Trace returned an unexpected response shape.",
            limitations=["Manual review recommended."],
            warnings=["Response shape mismatch."],
        )
    report_id = payload.get("report_id") or payload.get("id")
    risk_band = payload.get("risk_band") or payload.get("trace_band") or payload.get("band")
    confidence = _as_float(payload.get("confidence"))
    summary = payload.get("summary") or payload.get("advisory") or payload.get("operator_guidance")
    if isinstance(summary, list):
        summary = " ".join(str(item) for item in summary[:2])
    raw_limitations = payload.get("limitations")
    raw_warnings = payload.get("warnings")
    limitations: list[Any] = raw_limitations if isinstance(raw_limitations, list) else []
    warnings: list[Any] = raw_warnings if isinstance(raw_warnings, list) else []
    provider_count = payload.get("provider_count") or payload.get("providers_count")
    source_count = payload.get("source_count") or payload.get("sources_count")
    return TraceLiteResult(
        address=str(payload.get("address") or address),
        report_id=str(report_id) if report_id is not None else None,
        risk_band=str(risk_band) if risk_band is not None else None,
        confidence=confidence,
        summary=str(summary) if summary is not None else "Advisory result available.",
        provider_count=provider_count if isinstance(provider_count, int) else None,
        source_count=source_count if isinstance(source_count, int) else None,
        degraded=bool(payload.get("degraded") or payload.get("stale") or False),
        limitations=[str(item) for item in limitations],
        warnings=[str(item) for item in warnings],
        generated_at=str(payload.get("generated_at") or payload.get("created_at") or "") or None,
    )


async def get_trace_lite(address: str, client: BastionApiClient | None = None) -> TraceLiteResult:
    payload = await (client or BastionApiClient()).get(
        TRACE_LITE_ENDPOINT_TEMPLATE.format(address=_q(address))
    )
    return normalize_trace_lite_payload(payload, address=address)


async def get_trace_address(address: str, client: BastionApiClient | None = None) -> Any:
    return await (client or BastionApiClient()).get(f"/api/v1/trace/address/{_q(address)}")


async def get_trace_report(report_id: str, client: BastionApiClient | None = None) -> Any:
    return await (client or BastionApiClient()).get(f"/api/v1/trace/report/{_q(report_id)}")


async def get_trace_evidence(report_id: str, client: BastionApiClient | None = None) -> Any:
    return await (client or BastionApiClient()).get(
        f"/api/v1/trace/report/{_q(report_id)}/evidence"
    )


async def get_origin_passport(report_id: str, client: BastionApiClient | None = None) -> Any:
    return await (client or BastionApiClient()).get(
        f"/api/v1/trace/report/{_q(report_id)}/origin-passport"
    )


async def get_privacy_shield(report_id: str, client: BastionApiClient | None = None) -> Any:
    return await (client or BastionApiClient()).get(
        f"/api/v1/trace/report/{_q(report_id)}/privacy-shield"
    )


async def get_source_summary(report_id: str, client: BastionApiClient | None = None) -> Any:
    return await (client or BastionApiClient()).get(
        f"/api/v1/trace/report/{_q(report_id)}/source-summary"
    )


async def get_provider_disagreement(report_id: str, client: BastionApiClient | None = None) -> Any:
    return await (client or BastionApiClient()).get(
        f"/api/v1/trace/report/{_q(report_id)}/provider-disagreement"
    )


async def get_utxo_hygiene(report_id: str, client: BastionApiClient | None = None) -> Any:
    return await (client or BastionApiClient()).get(
        f"/api/v1/trace/report/{_q(report_id)}/utxo-hygiene"
    )


async def get_dust_radar(report_id: str, client: BastionApiClient | None = None) -> Any:
    return await (client or BastionApiClient()).get(
        f"/api/v1/trace/report/{_q(report_id)}/dust-radar"
    )


async def get_counterparty_lens(report_id: str, client: BastionApiClient | None = None) -> Any:
    return await (client or BastionApiClient()).get(
        f"/api/v1/trace/report/{_q(report_id)}/counterparty-lens"
    )


async def get_policy_facts(report_id: str, client: BastionApiClient | None = None) -> Any:
    return await (client or BastionApiClient()).get(
        f"/api/v1/trace/report/{_q(report_id)}/policy-facts"
    )


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
        return ApiResult(ok=True, data=None)
    return ApiResult(
        ok=False,
        error="Trace returned an unexpected response shape.",
        degraded=True,
    )


async def get_public_trace_summary(
    report_id: str, client: BastionApiClient | None = None
) -> ApiResult:
    return await _safe_get_result(f"/api/v1/public/trace/{_q(report_id)}/summary", client)


async def get_trace_report_result(
    report_id: str, client: BastionApiClient | None = None
) -> ApiResult:
    return await _safe_get_result(f"/api/v1/trace/report/{_q(report_id)}", client)


async def get_trace_evidence_result(
    report_id: str, client: BastionApiClient | None = None
) -> ApiResult:
    return await _safe_get_result(f"/api/v1/trace/report/{_q(report_id)}/evidence", client)


async def get_privacy_shield_result(
    report_id: str, client: BastionApiClient | None = None
) -> ApiResult:
    return await _safe_get_result(f"/api/v1/trace/report/{_q(report_id)}/privacy-shield", client)


async def get_origin_passport_result(
    report_id: str, client: BastionApiClient | None = None
) -> ApiResult:
    return await _safe_get_result(f"/api/v1/trace/report/{_q(report_id)}/origin-passport", client)


async def get_source_summary_result(
    report_id: str, client: BastionApiClient | None = None
) -> ApiResult:
    return await _safe_get_result(f"/api/v1/trace/report/{_q(report_id)}/source-summary", client)


async def get_provider_disagreement_result(
    report_id: str, client: BastionApiClient | None = None
) -> ApiResult:
    return await _safe_get_result(
        f"/api/v1/trace/report/{_q(report_id)}/provider-disagreement", client
    )


async def get_utxo_hygiene_result(
    report_id: str, client: BastionApiClient | None = None
) -> ApiResult:
    return await _safe_get_result(f"/api/v1/trace/report/{_q(report_id)}/utxo-hygiene", client)


async def get_dust_radar_result(
    report_id: str, client: BastionApiClient | None = None
) -> ApiResult:
    return await _safe_get_result(f"/api/v1/trace/report/{_q(report_id)}/dust-radar", client)


async def get_counterparty_lens_result(
    report_id: str, client: BastionApiClient | None = None
) -> ApiResult:
    return await _safe_get_result(f"/api/v1/trace/report/{_q(report_id)}/counterparty-lens", client)


async def get_policy_facts_result(
    report_id: str, client: BastionApiClient | None = None
) -> ApiResult:
    return await _safe_get_result(f"/api/v1/trace/report/{_q(report_id)}/policy-facts", client)


async def get_proof_packet(report_id: str, client: BastionApiClient | None = None) -> ApiResult:
    return await _safe_get_result(f"/api/v1/trace/report/{_q(report_id)}/proof-packet", client)
