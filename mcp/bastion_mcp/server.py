from __future__ import annotations

import asyncio
import json
import sys
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any

from bastion_mcp.client import BastionAPIClient
from bastion_mcp.config import MCPConfig
from bastion_mcp.safety import BastionMCPSafetyError, assert_no_forbidden_wording, assert_no_sensitive_material
from bastion_mcp.schemas import ToolError
from bastion_mcp.tools.evidence import get_evidence_packet
from bastion_mcp.tools.market import get_market_dashboard
from bastion_mcp.tools.policy import evaluate_policy
from bastion_mcp.tools.provider_health import get_provider_health
from bastion_mcp.tools.signals import explain_signal, get_latest_signals
from bastion_mcp.tools.trace import analyze_address, get_public_trace_summary, get_trace_report
from bastion_mcp.tools.treasury import create_treasury_draft
from bastion_mcp.tools.wallet import get_wallet_health

ToolHandler = Callable[[BastionAPIClient, dict[str, Any]], Awaitable[dict[str, Any]]]


@dataclass(frozen=True)
class MCPTool:
    name: str
    description: str
    handler: ToolHandler
    read_only: bool = True
    draft_only: bool = False


TOOL_REGISTRY: dict[str, MCPTool] = {
    "get_latest_signals": MCPTool(
        "get_latest_signals",
        "Return latest operator-safe Bitcoin Bastion signals with limitations.",
        get_latest_signals,
    ),
    "explain_signal": MCPTool(
        "explain_signal",
        "Explain a single signal with supporting evidence and limitations.",
        explain_signal,
    ),
    "analyze_address": MCPTool(
        "analyze_address",
        "Run advisory-only public Bitcoin address analysis through Bastion Trace.",
        analyze_address,
    ),
    "get_trace_report": MCPTool(
        "get_trace_report",
        "Fetch an existing advisory-only Trace report.",
        get_trace_report,
    ),
    "get_public_trace_summary": MCPTool(
        "get_public_trace_summary",
        "Fetch a public-safe Trace summary.",
        get_public_trace_summary,
    ),
    "get_wallet_health": MCPTool(
        "get_wallet_health",
        "Return no-custody wallet-health context or explicit unavailable status.",
        get_wallet_health,
    ),
    "evaluate_policy": MCPTool(
        "evaluate_policy",
        "Evaluate policy without executing the action.",
        evaluate_policy,
    ),
    "create_treasury_draft": MCPTool(
        "create_treasury_draft",
        "Create a local draft-only treasury review object requiring human approval.",
        create_treasury_draft,
        read_only=False,
        draft_only=True,
    ),
    "get_provider_health": MCPTool(
        "get_provider_health",
        "Return provider health and degraded/fallback/stale context.",
        get_provider_health,
    ),
    "get_market_dashboard": MCPTool(
        "get_market_dashboard",
        "Return market context without financial advice or prediction claims.",
        get_market_dashboard,
    ),
    "get_evidence_packet": MCPTool(
        "get_evidence_packet",
        "Fetch an evidence packet or explicit unavailable/partial evidence context.",
        get_evidence_packet,
    ),
}


async def run_tool(
    tool_name: str,
    arguments: dict[str, Any] | None = None,
    *,
    config: MCPConfig | None = None,
    client: BastionAPIClient | None = None,
) -> dict[str, Any]:
    arguments = arguments or {}
    if tool_name not in TOOL_REGISTRY:
        return _tool_error(f"Unknown MCP tool: {tool_name}", code="unknown_tool")
    try:
        assert_no_sensitive_material(arguments)
        tool = TOOL_REGISTRY[tool_name]
        if client is not None:
            result = await tool.handler(client, arguments)
        else:
            async with BastionAPIClient(config or MCPConfig.from_env()) as managed_client:
                result = await tool.handler(managed_client, arguments)
        _validate_response_shape(result)
        assert_no_forbidden_wording(result)
        return result
    except BastionMCPSafetyError as exc:
        return _tool_error(str(exc), code="safety_violation")
    except Exception as exc:  # noqa: BLE001 - MCP boundary returns structured errors
        return _tool_error(str(exc), code="tool_failed")


def list_tools() -> list[dict[str, Any]]:
    return [
        {
            "name": tool.name,
            "description": tool.description,
            "read_only": tool.read_only,
            "draft_only": tool.draft_only,
        }
        for tool in TOOL_REGISTRY.values()
    ]


def _validate_response_shape(result: dict[str, Any]) -> None:
    result.setdefault("limitations", ["No limitations returned by tool handler."])
    result.setdefault("safety_flags", {"no_custody": True})
    result.setdefault("source", "bitcoin_bastion_mcp")


def _tool_error(message: str, *, code: str) -> dict[str, Any]:
    safe_message = "Never enter seed phrases, private keys, wallet files or signing material." if "seed" in message.casefold() else message
    return ToolError(
        message=safe_message,
        error_code=code,
        limitations=["Tool did not complete successfully."],
        safety_flags={"no_custody": True},
    ).model_dump()


async def _json_lines_loop() -> None:
    print(json.dumps({"server": "bitcoin-bastion-mcp", "tools": list_tools()}), flush=True)
    async with BastionAPIClient(MCPConfig.from_env()) as client:
        for line in sys.stdin:
            request = json.loads(line)
            result = await run_tool(request["tool"], request.get("arguments", {}), client=client)
            print(json.dumps(result, default=str), flush=True)


def main() -> None:
    asyncio.run(_json_lines_loop())


if __name__ == "__main__":
    main()
