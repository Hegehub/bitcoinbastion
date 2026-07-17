from __future__ import annotations

from collections.abc import Sequence

import reflex as rx

from bastion_ui.components.ui.badge import badge
from bastion_ui.components.ui.card import card

DEFAULT_ITEMS = (
    "API unknown",
    "Workers unknown",
    "Evidence pipeline unknown",
    "Runtime unknown",
)


def pulse_chart(title: str = "Pulse", items: Sequence[str] | None = None) -> rx.Component:
    values = items or DEFAULT_ITEMS
    rows = [
        rx.hstack(badge(str(index + 1), "info"), rx.text(item), spacing="2")
        for index, item in enumerate(values)
    ]
    return card(
        *rows,
        title=title,
        subtitle="Reflex-native pulse visualization with safe unavailable defaults.",
        variant="console",
    )
