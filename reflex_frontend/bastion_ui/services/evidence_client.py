from __future__ import annotations

from typing import Any
from urllib.parse import quote

from bastion_ui.services.api_client import BastionApiClient
from bastion_ui.services.errors import NOT_FOUND_PUBLIC_MESSAGE, BastionApiNotFoundError


def _q(value: str) -> str:
    return quote(value, safe="")


async def get_evidence_packet(packet_id: str, client: BastionApiClient | None = None) -> Any:
    if not packet_id:
        raise BastionApiNotFoundError(
            "Evidence packet endpoint requires a packet identifier.",
            status_code=404,
            public_message=NOT_FOUND_PUBLIC_MESSAGE,
        )
    return await (client or BastionApiClient()).get(f"/web/evidence/{_q(packet_id)}")


async def get_trace_report_evidence(report_id: str, client: BastionApiClient | None = None) -> Any:
    return await (client or BastionApiClient()).get(
        f"/api/v1/trace/report/{_q(report_id)}/evidence"
    )
