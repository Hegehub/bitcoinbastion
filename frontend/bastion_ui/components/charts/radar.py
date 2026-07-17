from __future__ import annotations

from collections.abc import Sequence

import reflex as rx

from bastion_ui.components.ui.badge import badge
from bastion_ui.components.ui.card import card

DEFAULT_ITEMS = (
    "Evidence coverage",
    "Provider disagreement",
    "Privacy exposure",
    "Origin clarity",
    "Confidence",
)


def radar_chart(title: str = "Radar", items: Sequence[str] | None = None) -> rx.Component:
    values = items or DEFAULT_ITEMS
    rows = [
        rx.hstack(badge(str(index + 1), "info"), rx.text(item), spacing="2")
        for index, item in enumerate(values)
    ]
    return card(
        *rows,
        title=title,
        subtitle="Reflex-native radar visualization with safe unavailable defaults.",
        variant="console",
    )
