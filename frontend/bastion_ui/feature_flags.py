"""Typed, fail-closed frontend rollout controls (Feature 58)."""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum


class RolloutState(StrEnum):
    OFF = "OFF"
    INTERNAL = "INTERNAL"
    LIMITED = "LIMITED"
    ON = "ON"


class FeatureFlagId(StrEnum):
    CORE = "frontend.core"
    CONSOLE = "frontend.console"
    PAYREGISTER = "frontend.payregister"
    WEBSOCKET_LAB = "frontend.websocket_lab"
    DESIGN_SYSTEM = "frontend.design_system"


@dataclass(frozen=True)
class FeatureFlag:
    id: FeatureFlagId
    owner: str
    default: RolloutState
    production_allowed: bool
    rollback: str
    removal_condition: str


FLAGS: Mapping[FeatureFlagId, FeatureFlag] = {
    FeatureFlagId.CORE: FeatureFlag(
        FeatureFlagId.CORE,
        "Frontend/Core",
        RolloutState.ON,
        True,
        "Keep public recovery routes available; stop route-owned lifecycle.",
        "Permanent control.",
    ),
    FeatureFlagId.CONSOLE: FeatureFlag(
        FeatureFlagId.CONSOLE,
        "Frontend/Console",
        RolloutState.LIMITED,
        True,
        "Remove console navigation and release route-owned HTTP/WS work.",
        "Remove after operator-console acceptance.",
    ),
    FeatureFlagId.PAYREGISTER: FeatureFlag(
        FeatureFlagId.PAYREGISTER,
        "PayRegister",
        RolloutState.OFF,
        True,
        "Remove PayRegister navigation without changing Core or merchant data.",
        "Remove after separate-product launch decision.",
    ),
    FeatureFlagId.WEBSOCKET_LAB: FeatureFlag(
        FeatureFlagId.WEBSOCKET_LAB,
        "Feature 59",
        RolloutState.INTERNAL,
        False,
        "Close the canonical subscription and suppress reconnect.",
        "Remove with the degraded laboratory.",
    ),
    FeatureFlagId.DESIGN_SYSTEM: FeatureFlag(
        FeatureFlagId.DESIGN_SYSTEM,
        "Frontend development",
        RolloutState.INTERNAL,
        False,
        "Hide the development route.",
        "Remove when the preview is retired.",
    ),
}


def resolve_flags(
    *, environment: str, values: Mapping[str, str] | None = None
) -> dict[FeatureFlagId, RolloutState]:
    """Resolve defaults then trusted process environment; never browser-controlled state."""
    source = os.environ if values is None else values
    production = environment.lower() == "production"
    resolved: dict[FeatureFlagId, RolloutState] = {}
    known_keys = {f"BASTION_FLAG_{flag_id.name}" for flag_id in FLAGS}
    unknown = sorted(
        key for key in source if key.startswith("BASTION_FLAG_") and key not in known_keys
    )
    if unknown:
        raise ValueError(f"unknown frontend feature flag(s): {', '.join(unknown)}")
    for flag_id, definition in FLAGS.items():
        raw = source.get(f"BASTION_FLAG_{flag_id.name}")
        try:
            state = definition.default if raw is None else RolloutState(raw.upper())
        except ValueError as exc:
            raise ValueError(f"invalid value for feature flag {flag_id.value}") from exc
        if production and not definition.production_allowed and state is not RolloutState.OFF:
            state = RolloutState.OFF
        resolved[flag_id] = state
    return resolved


def validate_flags(*, consumed: set[FeatureFlagId]) -> None:
    if set(FLAGS) != consumed:
        orphaned = sorted(flag.value for flag in set(FLAGS) - consumed)
        unknown = sorted(flag.value for flag in consumed - set(FLAGS))
        raise ValueError(f"flag consumer mismatch; orphaned={orphaned}; unknown={unknown}")
    for flag_id, definition in FLAGS.items():
        if not definition.owner.strip() or not definition.rollback.strip():
            raise ValueError(f"incomplete feature flag metadata: {flag_id.value}")
