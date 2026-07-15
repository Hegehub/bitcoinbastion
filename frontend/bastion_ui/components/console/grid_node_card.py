from __future__ import annotations

import reflex as rx

from bastion_ui.components.ui.badge import badge
from bastion_ui.components.ui.card import card


def grid_node_card(title: str, description: str, status: str = "unknown") -> rx.Component:
    return card(
        rx.text(description),
        title=title,
        subtitle="Frontend visualization only; backend capability is not implied.",
        badge=badge(status, "warning" if status == "unknown" else "info"),
        variant="console",
    )
