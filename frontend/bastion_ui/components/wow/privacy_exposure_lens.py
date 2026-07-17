from __future__ import annotations

import reflex as rx

from bastion_ui.components.ui.badge import badge
from bastion_ui.components.ui.card import card

SAFETY_COPY = "Privacy exposure is advisory and depends on available evidence."
UNAVAILABLE_COPY = (
    "Live operational data is unavailable. This panel is displaying safe unavailable states only."
)
STATE_COPY = (
    "Loading, empty, error, degraded, unavailable, and unknown states are "
    "represented without backend-owned verdict logic."
)
BODY_COPY = (
    "Displays address reuse context, UTXO hygiene context, dust exposure "
    "context, counterparty context, and payment intent context when "
    "available."
)


def privacy_exposure_lens() -> rx.Component:
    return card(
        rx.text(SAFETY_COPY),
        rx.text(UNAVAILABLE_COPY),
        rx.text(BODY_COPY),
        rx.text(STATE_COPY),
        title="Privacy Exposure Lens",
        badge=badge("unavailable", "warning"),
        variant="console",
    )
