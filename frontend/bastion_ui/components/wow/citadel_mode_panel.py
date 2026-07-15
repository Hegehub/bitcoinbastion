from __future__ import annotations

import reflex as rx

from bastion_ui.components.ui.badge import badge
from bastion_ui.components.ui.card import card

SAFETY_COPY = (
    "Citadel Mode is high-caution operator posture only; no auto-blocking "
    "claims and no legal verdicts."
)
UNAVAILABLE_COPY = (
    "Live operational data is unavailable. This panel is displaying safe unavailable states only."
)
STATE_COPY = (
    "Loading, empty, error, degraded, unavailable, and unknown states are "
    "represented without backend-owned verdict logic."
)
BODY_COPY = (
    "Shows safety invariants, no-custody status, degraded-state "
    "visibility, provider disagreement, manual review requirements, and "
    "policy warnings."
)


def citadel_mode_panel() -> rx.Component:
    return card(
        rx.text(SAFETY_COPY),
        rx.text(UNAVAILABLE_COPY),
        rx.text(BODY_COPY),
        rx.text(STATE_COPY),
        title="Citadel Mode Panel",
        badge=badge("unavailable", "warning"),
        variant="console",
    )
