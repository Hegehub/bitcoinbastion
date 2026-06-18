from __future__ import annotations

from typing import Any
from urllib.parse import quote

from bastion_ui.services.api_client import BastionApiClient


async def get_landing(client: BastionApiClient | None = None) -> Any:
    return await (client or BastionApiClient()).get("/api/v1/public/landing")


async def get_status(client: BastionApiClient | None = None) -> Any:
    return await (client or BastionApiClient()).get("/api/v1/public/status")


async def get_roadmap(client: BastionApiClient | None = None) -> Any:
    return await (client or BastionApiClient()).get("/api/v1/public/roadmap")


async def get_stats(client: BastionApiClient | None = None) -> Any:
    return await (client or BastionApiClient()).get("/api/v1/public/stats")


async def get_features(client: BastionApiClient | None = None) -> Any:
    return await (client or BastionApiClient()).get("/api/v1/public/features")


async def get_public_trace_summary(report_id: str, client: BastionApiClient | None = None) -> Any:
    safe_report_id = quote(report_id, safe="")
    return await (client or BastionApiClient()).get(
        f"/api/v1/public/trace/{safe_report_id}/summary"
    )
