from __future__ import annotations

from pathlib import Path

import pytest

from bastion_ui.feature_flags import (
    FLAGS,
    FeatureFlagId,
    RolloutState,
    resolve_flags,
    validate_flags,
)
from bastion_ui.navigation import navigation_for
from bastion_ui.realtime.transport import ConnectionStatus, WebSocketTransport
from bastion_ui.route_lifecycle import transition_actions
from bastion_ui.topology import (
    ALIASES,
    ROUTES,
    RouteOutcome,
    hardcoded_href_consumers,
    redirect_for_alias,
    resolve_path,
    validate_dependencies,
    validate_routes,
)


def test_all_route_flag_dependencies_are_consumed_and_valid() -> None:
    validate_routes()
    validate_dependencies()
    consumed = {route.feature_flag_id for route in ROUTES}
    validate_flags(consumed=consumed)
    assert consumed == set(FLAGS)


def test_internal_literal_href_validator_is_clean() -> None:
    root = Path(__file__).resolve().parents[1]
    assert hardcoded_href_consumers(root) == ()


def test_disabled_direct_url_and_navigation_are_enforced() -> None:
    flags = resolve_flags(environment="production", values={})
    outcome, route_id = resolve_path("/websocket-lab", flags)
    assert (outcome, route_id) == (RouteOutcome.DISABLED, "websocket_lab")
    assert "websocket_lab" not in {route.id for route in navigation_for(flags)}


def test_flag_transitions_are_reversible_without_security_mutation() -> None:
    flags = resolve_flags(environment="test", values={})
    route = next(route for route in ROUTES if route.id == "access.security_posture")
    security = route.security_requirement_id
    flags[FeatureFlagId.CORE] = RolloutState.OFF
    assert resolve_path(route.path, flags)[0] is RouteOutcome.DISABLED
    flags[FeatureFlagId.CORE] = RolloutState.ON
    assert resolve_path(route.path, flags)[0] is RouteOutcome.ENABLED
    assert route.security_requirement_id == security == "access.me"


def test_aliases_are_internal_registered_and_security_preserving() -> None:
    flags = resolve_flags(environment="production", values={})
    for alias in ALIASES:
        assert redirect_for_alias(alias.path).startswith("/")
        assert resolve_path(alias.path, flags) == (RouteOutcome.REDIRECT, alias.canonical_route_id)
    for malicious in ("https://evil.example", "//evil.example", "/unknown", "javascript:alert(1)"):
        with pytest.raises(ValueError, match="unknown or unsafe"):
            redirect_for_alias(malicious)


def test_unknown_and_malformed_paths_select_not_found() -> None:
    flags = resolve_flags(environment="production", values={})
    assert resolve_path("/missing", flags) == (RouteOutcome.NOT_FOUND, None)
    assert resolve_path("/trace/../private-proof", flags) == (RouteOutcome.NOT_FOUND, None)
    assert resolve_path("/trace/not allowed", flags) == (RouteOutcome.NOT_FOUND, None)


def test_route_transition_reuses_cleanup_owners() -> None:
    enter_ws = transition_actions(None, "websocket_lab")
    assert enter_ws.connect_websocket and enter_ws.disconnect_websocket
    leave_ws = transition_actions("websocket_lab", "status")
    assert leave_ws.disconnect_websocket and leave_ws.invalidate_http
    reenter_ws = transition_actions("status", "websocket_lab")
    assert reenter_ws.connect_websocket and reenter_ws.disconnect_websocket
    protected = transition_actions("status", "access.security_posture")
    assert protected.invalidate_security and protected.refresh_security


@pytest.mark.asyncio
async def test_ws_owner_closes_socket_and_prevents_zombie_reconnect() -> None:
    class Socket:
        closed = False

        async def close(self) -> None:
            self.closed = True

    socket = Socket()
    transport = WebSocketTransport()
    transport.begin_connect()
    transport.connected()
    transport._socket = socket
    await transport.close()
    assert socket.closed
    assert transport.status is ConnectionStatus.DISCONNECTED
