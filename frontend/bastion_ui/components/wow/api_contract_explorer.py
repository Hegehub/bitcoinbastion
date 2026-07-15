from __future__ import annotations

import reflex as rx

from bastion_ui.components.ui.badge import badge
from bastion_ui.components.ui.card import card

SAFETY_COPY = (
    "API availability is displayed only when documented or returned by "
    "backend; unknown routes remain unknown."
)
UNAVAILABLE_COPY = (
    "Live operational data is unavailable. This panel is displaying safe unavailable states only."
)
STATE_COPY = (
    "Loading, empty, error, degraded, unavailable, and unknown states are "
    "represented without backend-owned verdict logic."
)
BODY_COPY = (
    "Shows Public, Trace, Evidence, Webhooks, WebSocket, Market, Treasury, "
    "and Provider Health groups as documented, unknown, or pending."
)


def api_contract_explorer() -> rx.Component:
    return card(
        rx.text(SAFETY_COPY),
        rx.text(UNAVAILABLE_COPY),
        rx.text(BODY_COPY),
        rx.text(STATE_COPY),
        title="API Contract Explorer",
        badge=badge("unavailable", "warning"),
        variant="console",
    )
