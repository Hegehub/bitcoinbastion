from __future__ import annotations

import reflex as rx

from bastion_ui.components.ui.badge import badge
from bastion_ui.components.ui.card import card


def provider_freshness_card() -> rx.Component:
    return card(
        rx.text(
            "Provider freshness is unknown until provider health or observability data is returned."
        ),
        rx.text("Unknown provider state is never treated as healthy."),
        title="Provider freshness",
        badge=badge("unknown", "warning"),
        variant="console",
    )
