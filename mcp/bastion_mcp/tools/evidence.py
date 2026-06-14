from __future__ import annotations

from typing import Any

from bastion_mcp.client import BastionAPIClient
from bastion_mcp.schemas import EvidencePacketRequest
from bastion_mcp.tools.common import ensure_limitations, structured_response


async def get_evidence_packet(client: BastionAPIClient, arguments: dict[str, Any]) -> dict[str, Any]:
    req = EvidencePacketRequest.model_validate(arguments)
    data = await client.get_evidence_packet(req.packet_id)
    return structured_response(
        data={"evidence_packet": data},
        limitations=ensure_limitations(data, "Evidence may be unavailable, partial, or operator-review pending."),
        degraded=_degraded(data),
    )


def _degraded(data: Any) -> bool | None:
    return data.get("degraded") if isinstance(data, dict) and isinstance(data.get("degraded"), bool) else None
