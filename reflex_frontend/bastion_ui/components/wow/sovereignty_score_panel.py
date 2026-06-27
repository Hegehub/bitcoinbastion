from __future__ import annotations

import reflex as rx

from bastion_ui.components.ui.badge import badge
from bastion_ui.components.ui.card import card

SAFETY_COPY = "Sovereignty Score is an operational posture indicator, not a guarantee."
UNAVAILABLE_COPY = (
    "Live operational data is unavailable. This panel is displaying safe unavailable states only."
)
STATE_COPY = (
    "Loading, empty, error, degraded, unavailable, and unknown states are "
    "represented without backend-owned verdict logic."
)
BODY_COPY = (
    "Inputs may include self-hosted runtime, provider redundancy, evidence "
    "availability, no-custody status, degraded-state visibility, audit "
    "availability, and webhook/event backbone status."
)


def sovereignty_score_panel() -> rx.Component:
    return card(
        rx.text(SAFETY_COPY),
        rx.text(UNAVAILABLE_COPY),
        rx.text(BODY_COPY),
        rx.text(STATE_COPY),
        title="Sovereignty Score Panel",
        badge=badge("unavailable", "warning"),
        variant="console",
    )
