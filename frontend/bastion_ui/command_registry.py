"""Typed, deterministic shell commands derived from canonical route metadata."""

from __future__ import annotations

import os
from dataclasses import dataclass
from enum import StrEnum

from bastion_ui.feature_flags import FeatureFlagId, RolloutState, resolve_flags
from bastion_ui.topology import ROUTES, RouteClass, RouteRecord, path_for


class CommandType(StrEnum):
    NAVIGATION = "NAVIGATION"
    CONTEXT_ACTION = "CONTEXT_ACTION"
    GLOBAL_ACTION = "GLOBAL_ACTION"
    HELP = "HELP"


class ContextActionType(StrEnum):
    REFRESH = "REFRESH"
    COPY_SAFE_IDENTIFIER = "COPY_SAFE_IDENTIFIER"
    NAVIGATE = "NAVIGATE"


@dataclass(frozen=True)
class CommandEntry:
    id: str
    type: CommandType
    label: str
    route_id: str | None
    domain: str
    aliases: tuple[str, ...] = ()
    keywords: tuple[str, ...] = ()
    shortcut: str | None = None
    order: int = 0


@dataclass(frozen=True)
class ContextAction:
    """A bounded shell slot; mutation payloads are deliberately unsupported."""

    id: str
    type: ContextActionType
    label: str
    route_id: str | None = None


def _route_command(route: RouteRecord) -> CommandEntry:
    return CommandEntry(
        id=f"navigate.{route.id}",
        type=CommandType.NAVIGATION,
        label=f"Open {route.title}",
        route_id=route.id,
        domain=route.domain,
        aliases=(route.title, route.domain),
        keywords=(route.product.value, route.nav_group or ""),
        order=route.nav_order,
    )


# Commands are generated once from the route owner; they do not fetch or clone paths.
COMMANDS: tuple[CommandEntry, ...] = tuple(
    _route_command(route)
    for route in ROUTES
    if route.nav_visible and route.route_class is not RouteClass.DEVELOPMENT_ONLY
)


def available_commands(
    *,
    flags: dict[FeatureFlagId, RolloutState] | None = None,
    allowed_security_requirements: frozenset[str] = frozenset(),
    include_protected: bool = False,
) -> tuple[CommandEntry, ...]:
    """Resolve discovery without turning display into authorization."""
    resolved = flags or resolve_flags(environment=os.getenv("BB_ENVIRONMENT", "production"))
    routes = {route.id: route for route in ROUTES}
    result: list[CommandEntry] = []
    for command in COMMANDS:
        route = routes[command.route_id or ""]
        if resolved[route.feature_flag_id] is RolloutState.OFF:
            continue
        if route.route_class in {RouteClass.PROTECTED, RouteClass.OPERATOR_ONLY}:
            if (
                not include_protected
                or route.security_requirement_id not in allowed_security_requirements
            ):
                continue
        result.append(command)
    return tuple(result)


def search_commands(
    query: str,
    *,
    current_domain: str | None = None,
    commands: tuple[CommandEntry, ...] | None = None,
) -> tuple[CommandEntry, ...]:
    """Rank exact/prefix/alias/keyword matches deterministically and locally."""
    candidates = commands if commands is not None else available_commands()
    needle = query.strip().casefold()

    def rank(command: CommandEntry) -> tuple[int, int, int, str]:
        label = command.label.casefold()
        aliases = tuple(value.casefold() for value in command.aliases)
        keywords = tuple(value.casefold() for value in command.keywords)
        if not needle:
            match = 4
        elif label == needle:
            match = 0
        elif label.startswith(needle):
            match = 1
        elif any(value.startswith(needle) for value in aliases):
            match = 2
        elif needle in label or any(needle in value for value in aliases + keywords):
            match = 3
        else:
            match = 99
        domain_penalty = 0 if current_domain and command.domain == current_domain else 1
        return (match, domain_penalty, command.order, command.id)

    return tuple(command for command in sorted(candidates, key=rank) if rank(command)[0] < 99)


def command_destination(command: CommandEntry) -> str:
    if command.type is not CommandType.NAVIGATION or command.route_id is None:
        raise ValueError(f"command has no route destination: {command.id}")
    return path_for(command.route_id)


def validate_commands() -> None:
    route_ids = {route.id for route in ROUTES}
    ids = [command.id for command in COMMANDS]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate command id")
    shortcuts = [command.shortcut for command in COMMANDS if command.shortcut]
    if len(shortcuts) != len(set(shortcuts)):
        raise ValueError("conflicting command shortcut")
    for command in COMMANDS:
        if command.type is CommandType.NAVIGATION and command.route_id not in route_ids:
            raise ValueError(f"unknown command route: {command.id}")
        if command.route_id:
            route = next(route for route in ROUTES if route.id == command.route_id)
            if route.route_class is RouteClass.DEVELOPMENT_ONLY:
                raise ValueError(f"development command exposed: {command.id}")


validate_commands()
