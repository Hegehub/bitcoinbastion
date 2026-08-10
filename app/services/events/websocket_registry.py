"""Authoritative route/family ownership and compatibility policy."""

from __future__ import annotations

from dataclasses import dataclass

from app.services.events.websocket_contracts import WIRE_PROTOCOL_VERSION
from app.services.events.websocket_filters import SPECIALIZED_STREAM_EVENT_TYPES, SUPPORTED_TOPICS


@dataclass(frozen=True)
class WebSocketContract:
    matrix_id: str
    blocker_id: str
    route: str
    family: str
    event_types: tuple[str, ...]
    wire_version: int
    accepted_versions: tuple[int, ...]
    direction: str
    ordering: str
    duplicate_policy: str
    gap_policy: str
    security_profile: str
    frontend_owner: str
    visibility_policy: str
    max_buffered_frames: int


def _contract(index: int, family: str) -> WebSocketContract:
    route = "/api/v1/ws/events" if family == "events" else f"/api/v1/ws/{family}"
    event_types = tuple(sorted(SPECIALIZED_STREAM_EVENT_TYPES.get(family, ())))
    return WebSocketContract(
        matrix_id=f"WS-{index:04d}",
        blocker_id=f"P1R2-B{index + 4:02d}",
        route=route,
        family=family,
        event_types=event_types,
        wire_version=WIRE_PROTOCOL_VERSION,
        accepted_versions=(WIRE_PROTOCOL_VERSION,),
        direction="server_to_client",
        ordering="event_id_identity; occurred_at is not total order",
        duplicate_policy="suppress identical event_id within bounded recent-id window",
        gap_policy="no replay authority; mark degraded and use authoritative HTTP refresh",
        security_profile="public-advisory-limited-payload",
        frontend_owner="bastion_ui.realtime.transport:WebSocketTransport",
        visibility_policy="disconnect_when_hidden_then_reconnect_and_refresh",
        max_buffered_frames=128,
    )


FAMILIES = (
    "events",
    "signals",
    "news",
    "onchain",
    "market",
    "trace",
    "treasury",
    "provider-health",
    "intelligence-timeline",
)
WEBSOCKET_CONTRACTS = tuple(_contract(index, family) for index, family in enumerate(FAMILIES, 1))

assert set(SUPPORTED_TOPICS) >= {
    contract.family for contract in WEBSOCKET_CONTRACTS if contract.family != "events"
}
