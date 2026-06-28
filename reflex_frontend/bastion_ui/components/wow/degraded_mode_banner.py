from __future__ import annotations

import reflex as rx

from bastion_ui.components.ui.badge import badge
from bastion_ui.components.ui.card import card

SAFETY_COPY = (
    "Some Bastion data may be delayed, stale, degraded, fallback-only, "
    "partial, unavailable, or unknown."
)
UNAVAILABLE_COPY = (
    "Live operational data is unavailable. This panel is displaying safe unavailable states only."
)
STATE_COPY = (
    "Loading, empty, error, degraded, unavailable, and unknown states are "
    "represented without backend-owned verdict logic."
)
BODY_COPY = "Supports degraded, stale, fallback, partial, unavailable, and unknown states."


def wow_degraded_mode_banner() -> rx.Component:
    return card(
        rx.text(SAFETY_COPY),
        rx.text(UNAVAILABLE_COPY),
        rx.text(BODY_COPY),
        rx.text(STATE_COPY),
        title="Wow degraded mode banner",
        badge=badge("unavailable", "warning"),
        variant="console",
    )
