from __future__ import annotations

import reflex as rx

from bastion_ui.components.ui.badge import badge
from bastion_ui.components.ui.card import card

SAFETY_COPY = "Market intelligence is informational only and is not financial advice."
UNAVAILABLE_COPY = (
    "Live operational data is unavailable. This panel is displaying safe unavailable states only."
)
STATE_COPY = (
    "Loading, empty, error, degraded, unavailable, and unknown states are "
    "represented without backend-owned verdict logic."
)
BODY_COPY = (
    "Displays market regime, signal state, provider health, "
    "evidence-backed narratives, Time Machine links, and stale/degraded "
    "warnings when backend data exists."
)


def market_intelligence_wall() -> rx.Component:
    return card(
        rx.text(SAFETY_COPY),
        rx.text(UNAVAILABLE_COPY),
        rx.text(BODY_COPY),
        rx.text(STATE_COPY),
        title="Market Intelligence Wall",
        badge=badge("unavailable", "warning"),
        variant="console",
    )
