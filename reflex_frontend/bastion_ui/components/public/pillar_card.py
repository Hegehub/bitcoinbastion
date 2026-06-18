from __future__ import annotations

import reflex as rx

from bastion_ui.components.ui.badge import badge
from bastion_ui.components.ui.card import card


def pillar_card(title: str, description: str, *, status: str = "baseline") -> rx.Component:
    return card(
        rx.text(description),
        title=title,
        badge=badge(status.title(), "info" if status in {"baseline", "implemented"} else "warning"),
    )
