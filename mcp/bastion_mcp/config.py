from __future__ import annotations

from dataclasses import dataclass
import os


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class MCPConfig:
    api_base_url: str = "http://localhost:8000"
    api_token: str | None = None
    request_timeout_seconds: float = 5.0
    default_limit: int = 10
    enable_treasury_drafts: bool = True
    enable_market_tools: bool = True
    enable_trace_tools: bool = True
    enable_wallet_tools: bool = True

    @classmethod
    def from_env(cls) -> "MCPConfig":
        token = os.getenv("BB_API_TOKEN") or None
        return cls(
            api_base_url=(os.getenv("BB_API_BASE_URL") or "http://localhost:8000").rstrip("/"),
            api_token=token,
            request_timeout_seconds=float(os.getenv("BB_MCP_REQUEST_TIMEOUT_SECONDS", "5")),
            default_limit=int(os.getenv("BB_MCP_DEFAULT_LIMIT", "10")),
            enable_treasury_drafts=_env_bool("BB_MCP_ENABLE_TREASURY_DRAFTS", True),
            enable_market_tools=_env_bool("BB_MCP_ENABLE_MARKET_TOOLS", True),
            enable_trace_tools=_env_bool("BB_MCP_ENABLE_TRACE_TOOLS", True),
            enable_wallet_tools=_env_bool("BB_MCP_ENABLE_WALLET_TOOLS", True),
        )
