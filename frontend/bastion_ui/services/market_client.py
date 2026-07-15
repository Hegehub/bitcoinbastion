from __future__ import annotations

from bastion_ui.services.api_client import BastionApiClient
from bastion_ui.services.errors import BastionApiError
from bastion_ui.services.models import ApiResult


class MarketApiClient:
    def __init__(self, api_client: BastionApiClient | None = None) -> None:
        self.api_client = api_client or BastionApiClient()

    async def _safe_get(self, endpoint: str, *, missing_reason: str | None = None) -> ApiResult:
        try:
            data = await self.api_client.get(endpoint)
            degraded = isinstance(data, dict) and bool(
                data.get("degraded") or data.get("stale") or data.get("fallback")
            )
            return ApiResult(ok=True, data=data, degraded=degraded)
        except BastionApiError as exc:
            return ApiResult(
                ok=False,
                data={
                    "available": False,
                    "reason": missing_reason or exc.public_message,
                    "endpoint": endpoint,
                },
                error=missing_reason or exc.public_message,
                status_code=exc.status_code,
                degraded=True,
            )

    async def get_market_dashboard(self) -> ApiResult:
        return await self._safe_get("/web/market-time-machine")

    async def get_market_status(self) -> ApiResult:
        return await self._safe_get("/api/v1/market/health")

    async def get_market_regime(self) -> ApiResult:
        return await self._safe_get(
            "/web/market-time-machine",
            missing_reason="Market regime is unavailable until dashboard DTO data is returned.",
        )

    async def get_latest_intelligence_signals(self) -> ApiResult:
        return await self._safe_get("/api/v1/signals/latest")

    async def get_provider_health(self) -> ApiResult:
        return await self._safe_get("/api/v1/market/providers/health")

    async def get_evidence_summary(self) -> ApiResult:
        return await self._safe_get(
            "/api/v1/evidence/packets",
            missing_reason="Evidence summary endpoint is not connected to this dashboard yet.",
        )

    async def get_market_time_machine(self) -> ApiResult:
        return await self._safe_get("/web/market-time-machine")

    async def get_time_machine(self) -> ApiResult:
        return await self._safe_get("/web/market-time-machine")

    async def get_market_signals(self) -> ApiResult:
        return await self._safe_get("/api/v1/signals/latest")

    async def get_market_evidence(self) -> ApiResult:
        return await self._safe_get(
            "/api/v1/evidence/packets",
            missing_reason="Market evidence endpoint is unavailable or not connected yet.",
        )

    async def get_market_narratives(self) -> ApiResult:
        return await self._safe_get("/api/v1/intelligence/narratives")

    async def get_market_sources(self) -> ApiResult:
        return await self._safe_get("/api/v1/news/sources")

    async def get_candle_detail(self, candle_id: str) -> ApiResult:
        return await self._safe_get(f"/web/candle/{candle_id}")

    async def get_evidence_packet(self, packet_id: str) -> ApiResult:
        return await self._safe_get(f"/web/evidence/{packet_id}")

    async def get_timeline(self) -> ApiResult:
        return await self._safe_get("/web/timeline")

    async def get_candle(self, candle_id: str) -> ApiResult:
        return await self._safe_get(f"/web/candle/{candle_id}")

    async def get_evidence(self, packet_id: str) -> ApiResult:
        return await self._safe_get(f"/web/evidence/{packet_id}")
