from __future__ import annotations

from typing import Any

from bastion_mcp.client import BastionAPIClient
from bastion_mcp.schemas import ProviderHealthRequest
from bastion_mcp.tools.common import ensure_limitations, structured_response


async def get_provider_health(client: BastionAPIClient, arguments: dict[str, Any]) -> dict[str, Any]:
    req = ProviderHealthRequest.model_validate(arguments)
    data = await client.get_provider_health(req.provider_type)
    return structured_response(
        data={"provider_health": data},
        limitations=ensure_limitations(data, "Provider health may be degraded, stale, or incomplete."),
        degraded=_degraded(data),
    )


def _degraded(data: Any) -> bool | None:
    return data.get("degraded") if isinstance(data, dict) and isinstance(data.get("degraded"), bool) else None
