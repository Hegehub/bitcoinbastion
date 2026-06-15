from __future__ import annotations

from typing import Literal, cast

import reflex as rx

from bastion_ui.components.ui.badge import badge

ReadonlyLabel = Literal["Read-only", "Advisory", "No custody", "Operator review", "Evidence-based", "Degraded visible"]


def readonly_badge(label: ReadonlyLabel = "Read-only") -> rx.Component:
    return badge(label, "bitcoin" if label == "Read-only" else "neutral")


def readonly_badge_group() -> rx.Component:
    return cast(rx.Component, rx.hstack(
        readonly_badge("Read-only"),
        readonly_badge("Advisory"),
        readonly_badge("No custody"),
        readonly_badge("Operator review"),
        readonly_badge("Evidence-based"),
        readonly_badge("Degraded visible"),
        wrap="wrap",
    ))
