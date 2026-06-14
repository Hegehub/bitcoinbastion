from __future__ import annotations

from typing import Any

from bastion_mcp.client import BastionAPIClient
from bastion_mcp.safety import NO_CUSTODY_TEXT, assert_no_sensitive_material, enforce_treasury_draft_only
from bastion_mcp.schemas import TreasuryDraftRequest
from bastion_mcp.tools.common import structured_response


async def create_treasury_draft(client: BastionAPIClient, arguments: dict[str, Any]) -> dict[str, Any]:
    req = TreasuryDraftRequest.model_validate(arguments)
    payload = req.model_dump()
    assert_no_sensitive_material(payload)
    enforce_treasury_draft_only(payload)
    data = await client.create_treasury_draft(payload)
    return structured_response(
        data={"draft": data, "safety": NO_CUSTODY_TEXT, "approval_required": True},
        limitations=[
            "Draft-only MCP preview; it does not sign, broadcast, approve, or move funds.",
            "Human/operator approval is required for risky treasury workflows.",
        ],
        draft_only=True,
        degraded=None,
    )
