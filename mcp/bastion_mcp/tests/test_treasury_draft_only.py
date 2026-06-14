from __future__ import annotations

import pytest

from bastion_mcp.server import run_tool


class TreasuryClient:
    def __init__(self) -> None:
        self.called_payload: dict[str, object] | None = None
        self.approve_called = False
        self.broadcast_called = False
        self.sign_called = False

    async def create_treasury_draft(self, payload: dict[str, object]) -> dict[str, object]:
        self.called_payload = payload
        return {"draft_id": "local", "approval_required": True, "no_custody": True}

    async def approve_request(self) -> None:
        self.approve_called = True

    async def broadcast_transaction(self) -> None:
        self.broadcast_called = True

    async def sign_transaction(self) -> None:
        self.sign_called = True


@pytest.mark.asyncio
async def test_create_treasury_draft_does_not_call_execution_methods() -> None:
    client = TreasuryClient()
    result = await run_tool(
        "create_treasury_draft",
        {"destination": "bc1qexamplepublicaddress000000000000000000000", "amount_sats": 10000},
        client=client,  # type: ignore[arg-type]
    )
    assert client.called_payload is not None
    assert client.approve_called is False
    assert client.broadcast_called is False
    assert client.sign_called is False
    assert result["safety_flags"]["draft_only"] is True
    assert result["data"]["approval_required"] is True


@pytest.mark.asyncio
async def test_treasury_sensitive_material_rejected() -> None:
    client = TreasuryClient()
    result = await run_tool(
        "create_treasury_draft",
        {"destination": "xprv private key", "amount_sats": 10000},
        client=client,  # type: ignore[arg-type]
    )
    assert result["error_code"] == "safety_violation"
    assert client.called_payload is None
