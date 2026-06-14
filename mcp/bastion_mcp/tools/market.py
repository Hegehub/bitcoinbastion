from __future__ import annotations

from typing import Any

from bastion_mcp.client import BastionAPIClient
from bastion_mcp.safety import MARKET_SAFETY_TEXT, assert_no_sensitive_material
from bastion_mcp.schemas import MarketDashboardRequest
from bastion_mcp.tools.common import ensure_limitations, structured_response


async def get_market_dashboard(client: BastionAPIClient, arguments: dict[str, Any]) -> dict[str, Any]:
    req = MarketDashboardRequest.model_validate(arguments)
    assert_no_sensitive_material(arguments)
    data = await client.get_market_dashboard(req.timeframe)
    return structured_response(
        data={"dashboard": data, "safety": MARKET_SAFETY_TEXT},
        limitations=ensure_limitations(data, MARKET_SAFETY_TEXT),
        market=True,
        degraded=_degraded(data),
    )


def _degraded(data: Any) -> bool | None:
    return data.get("degraded") if isinstance(data, dict) and isinstance(data.get("degraded"), bool) else None
