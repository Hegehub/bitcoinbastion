from __future__ import annotations

import re
from typing import Any

from bastion_mcp.client import BastionAPIClient
from bastion_mcp.safety import TRACE_SAFETY_TEXT, BastionMCPSafetyError, assert_no_sensitive_material
from bastion_mcp.schemas import TraceAddressRequest, TraceReportRequest
from bastion_mcp.tools.common import ensure_limitations, structured_response

_ADDRESS_RE = re.compile(r"^(bc1|tb1|bcrt1|[13])[a-zA-HJ-NP-Z0-9]{20,90}$", re.IGNORECASE)


def _validate_address(address: str) -> None:
    assert_no_sensitive_material(address)
    if not _ADDRESS_RE.match(address):
        raise BastionMCPSafetyError(f"Public Bitcoin address required. {TRACE_SAFETY_TEXT}")


async def analyze_address(client: BastionAPIClient, arguments: dict[str, Any]) -> dict[str, Any]:
    req = TraceAddressRequest.model_validate(arguments)
    _validate_address(req.address)
    data = await client.get_trace_lite(req.address)
    return structured_response(
        data={"trace": data, "safety": TRACE_SAFETY_TEXT},
        limitations=ensure_limitations(data, TRACE_SAFETY_TEXT),
        trace=True,
        degraded=_degraded(data),
    )


async def get_trace_report(client: BastionAPIClient, arguments: dict[str, Any]) -> dict[str, Any]:
    req = TraceReportRequest.model_validate(arguments)
    data = await client.get_trace_report(req.report_id)
    return structured_response(
        data={"report": data, "safety": TRACE_SAFETY_TEXT},
        limitations=ensure_limitations(data, TRACE_SAFETY_TEXT),
        trace=True,
        degraded=_degraded(data),
    )


async def get_public_trace_summary(client: BastionAPIClient, arguments: dict[str, Any]) -> dict[str, Any]:
    req = TraceReportRequest.model_validate(arguments)
    data = await client.get_public_trace_summary(req.report_id)
    return structured_response(
        data={"summary": data, "safety": TRACE_SAFETY_TEXT},
        limitations=ensure_limitations(data, "Public summary only; internal evidence may be omitted."),
        trace=True,
        degraded=_degraded(data),
    )


def _degraded(data: Any) -> bool | None:
    return data.get("degraded") if isinstance(data, dict) and isinstance(data.get("degraded"), bool) else None
