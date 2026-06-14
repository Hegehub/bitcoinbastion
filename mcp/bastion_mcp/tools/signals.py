from __future__ import annotations

from typing import Any

from bastion_mcp.client import BastionAPIClient
from bastion_mcp.safety import assert_no_sensitive_material
from bastion_mcp.schemas import SignalToolRequest, TraceReportRequest
from bastion_mcp.tools.common import ensure_limitations, structured_response


async def get_latest_signals(client: BastionAPIClient, arguments: dict[str, Any]) -> dict[str, Any]:
    req = SignalToolRequest.model_validate(arguments)
    assert_no_sensitive_material(arguments)
    data = await client.get_latest_signals(limit=req.limit, signal_type=req.signal_type)
    return structured_response(
        data={"signals": data},
        limitations=ensure_limitations(data, "Signals are informational only and not financial advice."),
        market=True,
        degraded=_degraded(data),
    )


async def explain_signal(client: BastionAPIClient, arguments: dict[str, Any]) -> dict[str, Any]:
    req = TraceReportRequest.model_validate({"report_id": arguments.get("signal_id")})
    signal = await client.get_signal(req.report_id)
    evidence = await client.get_signal_evidence(req.report_id)
    data = {
        "signal": signal,
        "supporting_evidence": evidence,
        "warning": "Correlation is not proof of causation. This is not financial advice.",
    }
    return structured_response(
        data=data,
        limitations=ensure_limitations(signal, "Operator review and evidence limitations apply."),
        market=True,
        degraded=_degraded(signal),
    )


def _degraded(data: Any) -> bool | None:
    return data.get("degraded") if isinstance(data, dict) and isinstance(data.get("degraded"), bool) else None
