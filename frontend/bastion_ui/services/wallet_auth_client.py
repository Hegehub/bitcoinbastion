from __future__ import annotations

from typing import Any, cast
from urllib.parse import quote

from bastion_ui.services.api_client import BastionApiClient


class WalletAuthService:
    """Async Wallet Auth adapter for Reflex state; backend policy remains authoritative."""

    def __init__(self, client: BastionApiClient | None = None) -> None:
        self.client = client or BastionApiClient()

    async def create_challenge(self, payload: dict[str, Any]) -> dict[str, Any]:
        return cast(
            dict[str, Any], await self.client.post("/api/v1/wallet-auth/challenges", json=payload)
        )

    async def register(self, payload: dict[str, Any]) -> dict[str, Any]:
        return cast(
            dict[str, Any], await self.client.post("/api/v1/wallet-auth/register", json=payload)
        )

    async def login(self, payload: dict[str, Any]) -> dict[str, Any]:
        return cast(
            dict[str, Any], await self.client.post("/api/v1/wallet-auth/login", json=payload)
        )

    async def create_session(self, payload: dict[str, Any]) -> dict[str, Any]:
        return cast(
            dict[str, Any], await self.client.post("/api/v1/wallet-auth/sessions", json=payload)
        )

    async def get_me(self, headers: dict[str, str]) -> dict[str, Any]:
        return cast(
            dict[str, Any], await self.client.get("/api/v1/wallet-auth/me", headers=headers)
        )

    async def get_entitlements(self, headers: dict[str, str]) -> dict[str, Any]:
        return cast(
            dict[str, Any],
            await self.client.get("/api/v1/wallet-auth/entitlements", headers=headers),
        )

    async def get_devices(self, headers: dict[str, str]) -> dict[str, Any]:
        return cast(
            dict[str, Any], await self.client.get("/api/v1/wallet-auth/devices", headers=headers)
        )

    async def revoke_device(self, device_id: str, headers: dict[str, str]) -> dict[str, Any]:
        return cast(
            dict[str, Any],
            await self.client.delete(
                f"/api/v1/wallet-auth/devices/{quote(device_id, safe='')}", headers=headers
            ),
        )

    async def step_up(self, payload: dict[str, Any], headers: dict[str, str]) -> dict[str, Any]:
        return cast(
            dict[str, Any],
            await self.client.post("/api/v1/wallet-auth/step-up", json=payload, headers=headers),
        )

    async def start_recovery(self, payload: dict[str, Any]) -> dict[str, Any]:
        return cast(
            dict[str, Any],
            await self.client.post("/api/v1/wallet-auth/recovery/start", json=payload),
        )

    async def complete_recovery(self, recovery_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        return cast(
            dict[str, Any],
            await self.client.post(
                f"/api/v1/wallet-auth/recovery/{quote(recovery_id, safe='')}/complete", json=payload
            ),
        )

    async def lockdown(self, payload: dict[str, Any], headers: dict[str, str]) -> dict[str, Any]:
        return cast(
            dict[str, Any],
            await self.client.post("/api/v1/wallet-auth/lockdown", json=payload, headers=headers),
        )
