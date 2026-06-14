from __future__ import annotations

from typing import Any

import httpx

from bastion_mcp.config import MCPConfig


class BastionMCPClientError(RuntimeError):
    pass


class BastionAPIClient:
    def __init__(self, config: MCPConfig, *, transport: httpx.AsyncBaseTransport | None = None) -> None:
        self.config = config
        headers: dict[str, str] = {"User-Agent": "bitcoin-bastion-mcp/0.1.0"}
        if config.api_token:
            headers["Authorization"] = f"Bearer {config.api_token}"
        self._client = httpx.AsyncClient(
            base_url=config.api_base_url,
            timeout=config.request_timeout_seconds,
            headers=headers,
            transport=transport,
        )

    async def close(self) -> None:
        await self._client.aclose()

    async def __aenter__(self) -> "BastionAPIClient":
        return self

    async def __aexit__(self, *args: object) -> None:
        await self.close()

    async def get_latest_signals(self, *, limit: int = 10, signal_type: str | None = None) -> Any:
        params: dict[str, Any] = {"limit": limit}
        if signal_type:
            params["signal_type"] = signal_type
        return await self._request("GET", "/api/v1/signals/latest", params=params)

    async def get_signal(self, signal_id: int | str) -> Any:
        return await self._request("GET", f"/api/v1/signals/{signal_id}")

    async def get_signal_evidence(self, signal_id: int | str) -> Any:
        return await self._request("GET", f"/api/v1/signals/{signal_id}/evidence")

    async def get_trace_lite(self, address: str) -> Any:
        return await self._request("GET", f"/api/v1/trace/lite/{address}")

    async def get_trace_report(self, report_id: int | str) -> Any:
        return await self._request("GET", f"/api/v1/trace/report/{report_id}")

    async def get_public_trace_summary(self, report_id: int | str) -> Any:
        return await self._request("GET", f"/api/v1/public/trace/{report_id}/summary")

    async def get_wallet_health(self, wallet_id: str | None = None) -> Any:
        if wallet_id is None:
            return {
                "status": "unavailable",
                "limitations": ["Wallet health endpoint requires a wallet reference in this deployment."],
                "no_custody": True,
            }
        return await self._request("GET", f"/api/v1/wallet/profiles/{wallet_id}/health/reports", params={"limit": 1})

    async def evaluate_policy(self, policy_profile: str, action_type: str, context: dict[str, Any]) -> Any:
        return await self._request(
            "POST",
            "/api/v1/policy/check",
            json={"policy_profile": policy_profile, "action_type": action_type, "context": context},
        )

    async def create_treasury_draft(self, payload: dict[str, Any]) -> Any:
        # Intentionally local/draft-only for Prompt 15; do not call execution endpoints.
        return {
            "draft_id": "local-draft",
            "destination": payload.get("destination"),
            "amount_sats": payload.get("amount_sats"),
            "purpose": payload.get("purpose"),
            "policy_profile": payload.get("policy_profile", "default"),
            "approval_required": True,
            "destination_review_status": "operator_review_required",
            "policy_warnings": ["Draft-only MCP preview; human approval required before any treasury action."],
            "no_custody": True,
        }

    async def get_provider_health(self, provider_type: str | None = None) -> Any:
        params = {"provider_type": provider_type} if provider_type else None
        return await self._request("GET", "/api/v1/health/providers", params=params)

    async def get_market_dashboard(self, timeframe: str = "1h") -> Any:
        return await self._request("GET", "/api/v1/market/btc/context", params={"timeframe": timeframe})

    async def get_evidence_packet(self, packet_id: int | str) -> Any:
        return await self._request("GET", f"/api/v1/evidence/packets/{packet_id}")

    async def _request(self, method: str, path: str, **kwargs: Any) -> Any:
        try:
            response = await self._client.request(method, path, **kwargs)
        except httpx.TimeoutException as exc:
            raise BastionMCPClientError("Bitcoin Bastion API request timed out.") from exc
        except httpx.HTTPError as exc:
            raise BastionMCPClientError("Bitcoin Bastion API unavailable.") from exc
        if response.status_code >= 400:
            raise BastionMCPClientError(f"Bitcoin Bastion API returned HTTP {response.status_code}.")
        payload = response.json()
        if isinstance(payload, dict) and "data" in payload and "error" in payload:
            if payload.get("error"):
                raise BastionMCPClientError("Bitcoin Bastion API returned an error envelope.")
            return payload.get("data")
        return payload
