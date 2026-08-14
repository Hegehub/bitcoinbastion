"""Bounded presentation-only shell effects (Feature 10/57)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ShellEffect:
    id: str
    owner: str
    purpose: str
    reduced_motion: str
    performance_strategy: str
    production: bool


SHELL_EFFECTS: tuple[ShellEffect, ...] = (
    ShellEffect(
        "shell.ambient_geometry",
        "Prompt 6 ambient primitive",
        "Preserve spatial continuity behind application chrome.",
        "Static geometric field.",
        "One CSS transform animation; one shell owner; no State traffic.",
        True,
    ),
    ShellEffect(
        "shell.active_route_indicator",
        "Feature 10",
        "Keep current route visible with text, border, and material cues.",
        "Static border and aria-current remain.",
        "Transform/opacity transition only.",
        True,
    ),
    ShellEffect(
        "shell.overlay_reveal",
        "Feature 37/48",
        "Make command and mobile overlays spatially understandable.",
        "Overlay appears without transition.",
        "Bounded opacity/transform; no requestAnimationFrame.",
        True,
    ),
)


def validate_shell_effects() -> None:
    ids = [effect.id for effect in SHELL_EFFECTS]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate shell effect")
    for effect in SHELL_EFFECTS:
        if not all(
            (effect.owner, effect.purpose, effect.reduced_motion, effect.performance_strategy)
        ):
            raise ValueError(f"incomplete shell effect: {effect.id}")


validate_shell_effects()
