from __future__ import annotations

import reflex as rx

from bastion_ui.components.ui.card import card
from bastion_ui.security.market_safety_copy import MARKET_TIME_MACHINE_NO_CUSTODY_COPY

MARKET_LIMITATIONS = (
    "Provider coverage may be incomplete.",
    "Market movement can have multiple causes.",
    "Historical similarity does not guarantee repetition.",
    "Signals require operator review.",
    "Degraded or stale providers reduce confidence.",
)


def market_limitations_card() -> rx.Component:
    return card(
        rx.unordered_list(*[rx.list_item(item) for item in MARKET_LIMITATIONS]),
        rx.text(MARKET_TIME_MACHINE_NO_CUSTODY_COPY),
        title="Market limitations and no-custody rules",
        subtitle="Operator review material only.",
        variant="safety",
    )
