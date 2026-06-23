from __future__ import annotations

import reflex as rx

from bastion_ui.components.ui.card import card


def source_health_card() -> rx.Component:
    return card(
        rx.text("Provider/source status: unavailable until backend data is returned."),
        rx.text(
            "Last update, degraded/stale indicators, error counts, and notes are "
            "shown when present."
        ),
        title="Source health",
        variant="console",
    )
