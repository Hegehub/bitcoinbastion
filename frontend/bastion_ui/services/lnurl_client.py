from __future__ import annotations

from typing import Any, cast
from urllib.parse import quote

from bastion_ui.services.api_client import BastionApiClient


class LnurlService:
    def __init__(self, client: BastionApiClient | None = None) -> None:
        self.client = client or BastionApiClient()

    async def create_auth_challenge(self, payload: dict[str, Any]) -> dict[str, Any]:
        return cast(
            dict[str, Any], await self.client.post("/v1/lnurl/auth/challenges", json=payload)
        )

    async def create_auth_session(self, payload: dict[str, Any]) -> dict[str, Any]:
        return cast(dict[str, Any], await self.client.post("/v1/lnurl/auth/sessions", json=payload))

    async def create_subscription_payment(self, payload: dict[str, Any]) -> dict[str, Any]:
        return cast(
            dict[str, Any], await self.client.post("/v1/lnurl/pay/subscriptions", json=payload)
        )

    async def verify_payment(self, payment_id: str) -> dict[str, Any]:
        return cast(
            dict[str, Any],
            await self.client.get(f"/v1/lnurl/pay/verify/{quote(payment_id, safe='')}"),
        )

    async def create_withdraw(
        self, payload: dict[str, Any], headers: dict[str, str]
    ) -> dict[str, Any]:
        return cast(
            dict[str, Any],
            await self.client.post("/v1/lnurl/withdraw/requests", json=payload, headers=headers),
        )

    @staticmethod
    def missing_status_contracts() -> tuple[str, ...]:
        return ("lnurl_auth_attempt_status", "lnurl_withdraw_status")
