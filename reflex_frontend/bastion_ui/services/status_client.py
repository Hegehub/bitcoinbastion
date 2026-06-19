from __future__ import annotations

from typing import Any

from bastion_ui.services.api_client import BastionApiClient
from bastion_ui.services.errors import NOT_FOUND_PUBLIC_MESSAGE, BastionApiNotFoundError


async def get_public_status(client: BastionApiClient | None = None) -> Any:
    return await (client or BastionApiClient()).get("/api/v1/public/status")


async def get_provider_health(client: BastionApiClient | None = None) -> Any:
    raise BastionApiNotFoundError(
        "Stable provider health endpoint is not documented for Reflex yet.",
        status_code=404,
        public_message=NOT_FOUND_PUBLIC_MESSAGE,
    )


async def get_health(client: BastionApiClient | None = None) -> Any:
    return await (client or BastionApiClient()).get("/health")
