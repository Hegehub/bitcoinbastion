from __future__ import annotations

from typing import Any

from bastion_ui.services.api_client import BastionApiClient
from bastion_ui.services.errors import UNAVAILABLE_PUBLIC_MESSAGE, BastionApiUnavailableError


class ConsoleApiClient:
    def __init__(self, api_client: BastionApiClient | None = None) -> None:
        self.api_client = api_client or BastionApiClient()

    async def get_console_overview(self) -> Any:
        return await self.api_client.get("/api/v1/operations/status")

    async def get_provider_health_matrix(self) -> Any:
        return await self.api_client.get("/api/v1/health/providers")

    async def get_audit_summary(self) -> Any:
        raise BastionApiUnavailableError(
            "No stable Reflex audit summary endpoint is documented yet.",
            public_message=UNAVAILABLE_PUBLIC_MESSAGE,
        )

    async def get_policy_summary(self) -> Any:
        raise BastionApiUnavailableError(
            "No stable Reflex policy summary endpoint is documented yet.",
            public_message=UNAVAILABLE_PUBLIC_MESSAGE,
        )
