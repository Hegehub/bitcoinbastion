from __future__ import annotations

from typing import Any

from bastion_mcp.client import BastionAPIClient
from bastion_mcp.safety import NO_CUSTODY_TEXT, assert_no_sensitive_material
from bastion_mcp.schemas import WalletHealthRequest
from bastion_mcp.tools.common import ensure_limitations, structured_response


async def get_wallet_health(client: BastionAPIClient, arguments: dict[str, Any]) -> dict[str, Any]:
    req = WalletHealthRequest.model_validate(arguments)
    assert_no_sensitive_material(arguments)
    data = await client.get_wallet_health(req.wallet_id)
    return structured_response(
        data={"wallet_health": data, "safety": NO_CUSTODY_TEXT},
        limitations=ensure_limitations(data, "Wallet health is no-custody status context only."),
        degraded=True if isinstance(data, dict) and data.get("status") == "unavailable" else None,
    )
