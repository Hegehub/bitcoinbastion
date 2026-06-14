from __future__ import annotations

import logging

import pytest

from bastion_mcp.server import run_tool


class AnyClient:
    async def get_market_dashboard(self, timeframe: str = "1h") -> dict[str, object]:
        return {"timeframe": timeframe, "limitations": ["not financial advice"]}


@pytest.mark.asyncio
@pytest.mark.parametrize("value", ["seed phrase", "mnemonic", "private key", "xprv", "wallet.dat", "keystore"])
async def test_no_tool_accepts_sensitive_material(value: str) -> None:
    result = await run_tool("get_market_dashboard", {"timeframe": value}, client=AnyClient())  # type: ignore[arg-type]
    assert result["error_code"] == "safety_violation"
    assert "safety_flags" in result


@pytest.mark.asyncio
async def test_no_logs_or_response_echo_raw_sensitive_material(caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.INFO)
    result = await run_tool("get_market_dashboard", {"timeframe": "xprv actual-secret-value"}, client=AnyClient())  # type: ignore[arg-type]
    assert "actual-secret-value" not in caplog.text.casefold()
    assert "actual-secret-value" not in str(result).casefold()
