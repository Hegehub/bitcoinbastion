from __future__ import annotations

from typing import Any

from bastion_mcp.safety import assert_no_forbidden_wording, safety_flags
from bastion_mcp.schemas import ToolResponse


def ensure_limitations(data: Any, fallback: str) -> list[str]:
    if isinstance(data, dict):
        limitations = data.get("limitations")
        if isinstance(limitations, list):
            return [str(item) for item in limitations]
    if isinstance(data, list):
        collected: list[str] = []
        for item in data:
            if isinstance(item, dict) and isinstance(item.get("limitations"), list):
                collected.extend(str(limit) for limit in item["limitations"])
        if collected:
            return collected
    return [fallback]


def structured_response(
    *,
    data: dict[str, Any],
    limitations: list[str],
    trace: bool = False,
    market: bool = False,
    draft_only: bool = False,
    degraded: bool | None = None,
) -> dict[str, Any]:
    flags = safety_flags(trace=trace, market=market)
    flags["draft_only"] = draft_only
    response = ToolResponse(
        data=data,
        limitations=limitations,
        safety_flags=flags,
        degraded=degraded,
    ).model_dump()
    assert_no_forbidden_wording(response)
    return response
