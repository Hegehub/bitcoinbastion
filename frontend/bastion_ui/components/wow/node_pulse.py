from __future__ import annotations

import reflex as rx

from bastion_ui.components.charts.pulse import pulse_chart
from bastion_ui.components.ui.badge import badge
from bastion_ui.components.ui.card import card

SAFETY_COPY = "Node Pulse is operational status context only and not a production guarantee."
UNAVAILABLE_COPY = (
    "Live operational data is unavailable. This panel is displaying safe unavailable states only."
)
STATE_COPY = (
    "Loading, empty, error, degraded, unavailable, and unknown states are "
    "represented without backend-owned verdict logic."
)
BODY_COPY = "Operational pulse unavailable. No production evidence was found for this metric."


def node_pulse() -> rx.Component:
    return card(
        rx.text(SAFETY_COPY),
        rx.text(UNAVAILABLE_COPY),
        pulse_chart("Node Pulse visual"),
        rx.text(BODY_COPY),
        rx.text(STATE_COPY),
        title="Node Pulse",
        badge=badge("unavailable", "warning"),
        variant="console",
    )
