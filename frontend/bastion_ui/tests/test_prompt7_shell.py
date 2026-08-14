from __future__ import annotations

import json
from pathlib import Path

import pytest

from bastion_ui.command_registry import (
    COMMANDS,
    CommandType,
    available_commands,
    command_destination,
    search_commands,
    validate_commands,
)
from bastion_ui.feature_flags import FeatureFlagId, RolloutState, resolve_flags
from bastion_ui.navigation import MOBILE_NAVIGATION
from bastion_ui.realtime.transport import ConnectionStatus, WebSocketTransport
from bastion_ui.state.shell_state import shell_metadata
from bastion_ui.topology import ROUTE_BY_ID, redirect_for_alias
from bastion_ui.wow import SHELL_EFFECTS, validate_shell_effects

ROOT = Path(__file__).resolve().parents[3]


def test_command_registry_is_unique_typed_and_route_owned() -> None:
    validate_commands()
    assert len({command.id for command in COMMANDS}) == len(COMMANDS)
    assert all(command.type is CommandType.NAVIGATION for command in COMMANDS)
    assert all(command.route_id in ROUTE_BY_ID for command in COMMANDS)
    assert all(
        command_destination(command) == ROUTE_BY_ID[command.route_id or ""].path
        for command in COMMANDS
    )


def test_command_search_ranking_is_deterministic_and_local() -> None:
    first = search_commands("trace")
    assert first == search_commands("trace")
    assert first and "Trace" in first[0].label


def test_disabled_and_denied_commands_cannot_execute() -> None:
    flags = resolve_flags(environment="test", values={})
    flags[FeatureFlagId.CORE] = RolloutState.OFF
    assert available_commands(flags=flags) == ()
    production = available_commands()
    assert all(
        ROUTE_BY_ID[command.route_id or ""].security_requirement_id == "public"
        for command in production
    )


def test_explicit_security_requirement_is_needed_for_protected_discovery() -> None:
    denied = available_commands(include_protected=True)
    allowed = available_commands(
        include_protected=True, allowed_security_requirements=frozenset({"operator"})
    )
    assert not any(command.route_id == "console.home" for command in denied)
    assert any(command.route_id == "console.home" for command in allowed)


def test_shell_context_reconstructs_deep_links_and_unknown_routes() -> None:
    report = shell_metadata("/trace/report-123")
    assert report["route_id"] == "trace.report"
    assert report["context"] == "Bitcoin Bastion Core · Trace"
    assert tuple(report["breadcrumbs"])[-1][2] is True  # type: ignore[arg-type]
    assert shell_metadata("/not-a-route")["route_id"] == ""


def test_mobile_navigation_has_no_independent_paths() -> None:
    assert MOBILE_NAVIGATION
    assert all(route.id in ROUTE_BY_ID and route.mobile_eligible for route in MOBILE_NAVIGATION)


def test_feature_57_legacy_wow_route_is_a_safe_internal_alias() -> None:
    assert redirect_for_alias("/console/wow") == "/console/command-center"
    with pytest.raises(ValueError):
        redirect_for_alias("//attacker.example")


def test_wow_effects_are_bounded_and_reduced_motion_owned() -> None:
    validate_shell_effects()
    assert all(effect.reduced_motion and effect.performance_strategy for effect in SHELL_EFFECTS)
    assert all(
        "State traffic" in effect.performance_strategy
        or "requestAnimationFrame" in effect.performance_strategy
        or "Transform" in effect.performance_strategy
        for effect in SHELL_EFFECTS
    )


def test_shell_uses_one_overlay_owner_and_accessibility_landmarks() -> None:
    source = (ROOT / "frontend/bastion_ui/components/layout/app_shell.py").read_text()
    assert "rx.el.main(" in source
    assert "Skip to main content" in source
    assert source.count("command_palette()") == 1
    assert source.count("global_command_shortcut()") == 1
    shortcut = (ROOT / "frontend/bastion_ui/components/layout/command_palette.py").read_text()
    assert "window.addEventListener('keydown', window[owner])" in shortcut
    assert "window.removeEventListener('keydown', window[owner])" in shortcut
    assert "event.key !== '/'" in shortcut
    assert "event.key === 'Escape'" in shortcut
    css = (ROOT / "frontend/assets/visual-system.css").read_text()
    assert 'aria-current="page"' in css
    assert "prefers-reduced-motion:reduce" in css


def test_command_state_is_presentation_only() -> None:
    source = (ROOT / "frontend/bastion_ui/state/command_palette_state.py").read_text()
    forbidden = ("generated_http", "WebSocket", "SecurityShellState", "raw_payload")
    assert not any(value in source for value in forbidden)


def test_protected_and_operator_shells_reuse_feature67_fail_closed_state() -> None:
    source = (ROOT / "frontend/bastion_ui/app.py").read_text()
    assert "SecurityShellState.protected_visible" in source
    assert "SecurityShellState.operator_visible" in source
    assert "access_required_shell" in source
    lifecycle = (ROOT / "frontend/bastion_ui/route_lifecycle.py").read_text()
    assert '{"access.me", "operator"}' in lifecycle


@pytest.mark.asyncio
async def test_route_owned_websocket_remains_open_until_explicit_cleanup(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class Socket:
        closed = False

        async def recv(self) -> str:
            return json.dumps(
                {
                    "protocol": "bitcoin-bastion.events",
                    "wire_version": 1,
                    "type": "system",
                    "event_type": "connection.accepted",
                    "message": "Connected",
                    "stream": "provider-health",
                }
            )

        async def close(self) -> None:
            self.closed = True

    socket = Socket()

    async def connect(_uri: str) -> Socket:
        return socket

    monkeypatch.setattr("bastion_ui.realtime.transport.connect", connect)
    transport = WebSocketTransport()
    await transport.receive_first("ws://example.invalid/events")
    assert transport.status is ConnectionStatus.CONNECTED
    assert socket.closed is False
    await transport.close()
    assert socket.closed is True
    assert transport.status is ConnectionStatus.DISCONNECTED
