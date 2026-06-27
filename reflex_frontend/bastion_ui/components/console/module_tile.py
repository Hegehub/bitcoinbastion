from __future__ import annotations

import reflex as rx

from bastion_ui.components.ui.badge import badge
from bastion_ui.components.ui.card import card


def module_tile(
    title: str,
    description: str,
    route: str,
    status: str = "unknown",
    implemented: bool = False,
) -> rx.Component:
    return card(
        rx.text(description),
        rx.text("Route: " + route),
        rx.link("Open module", href=route),
        title=title,
        subtitle="Implemented now" if implemented else "Coming in later migration prompt",
        badge=badge(status, "info" if implemented else "warning"),
        variant="console",
    )
