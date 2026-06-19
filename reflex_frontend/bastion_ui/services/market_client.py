from __future__ import annotations

from typing import Any
from urllib.parse import quote

from bastion_ui.services.api_client import BastionApiClient


def _q(value: str) -> str:
    return quote(value, safe="")


async def get_market_dashboard(client: BastionApiClient | None = None) -> Any:
    return await (client or BastionApiClient()).get("/web/market-time-machine")


async def get_market_time_machine(client: BastionApiClient | None = None) -> Any:
    return await (client or BastionApiClient()).get("/web/market-time-machine")


async def get_timeline(client: BastionApiClient | None = None) -> Any:
    return await (client or BastionApiClient()).get("/web/timeline")


async def get_candle(candle_id: str, client: BastionApiClient | None = None) -> Any:
    return await (client or BastionApiClient()).get(f"/web/candle/{_q(candle_id)}")


async def get_evidence(packet_id: str, client: BastionApiClient | None = None) -> Any:
    return await (client or BastionApiClient()).get(f"/web/evidence/{_q(packet_id)}")
