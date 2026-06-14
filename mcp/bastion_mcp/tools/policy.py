from __future__ import annotations

from typing import Any

from bastion_mcp.client import BastionAPIClient
from bastion_mcp.safety import assert_no_sensitive_material
from bastion_mcp.schemas import PolicyEvaluationRequest
from bastion_mcp.tools.common import ensure_limitations, structured_response


async def evaluate_policy(client: BastionAPIClient, arguments: dict[str, Any]) -> dict[str, Any]:
    req = PolicyEvaluationRequest.model_validate(arguments)
    assert_no_sensitive_material(req.model_dump())
    data = await client.evaluate_policy(req.policy_profile, req.action_type, req.context)
    return structured_response(
        data={"policy_result": data, "execution": "not_executed"},
        limitations=ensure_limitations(data, "Policy MCP tools evaluate only and do not execute actions."),
        degraded=_degraded(data),
    )


def _degraded(data: Any) -> bool | None:
    return data.get("degraded") if isinstance(data, dict) and isinstance(data.get("degraded"), bool) else None
