from __future__ import annotations

import reflex as rx

from bastion_ui.components.charts.radar import radar_chart
from bastion_ui.components.ui.badge import badge
from bastion_ui.components.ui.card import card

SAFETY_COPY = (
    "Advisory-only. Not legal verification. Not Bitcoin consensus proof. "
    "No custody. Public Bitcoin addresses only. Never enter seed phrases, "
    "private keys, wallet files or signing material."
)
UNAVAILABLE_COPY = (
    "Live operational data is unavailable. This panel is displaying safe unavailable states only."
)
STATE_COPY = (
    "Loading, empty, error, degraded, unavailable, and unknown states are "
    "represented without backend-owned verdict logic."
)
BODY_COPY = (
    "Radar dimensions: evidence coverage, provider disagreement, privacy "
    "exposure, origin clarity, counterparty context, payment context, and "
    "confidence level."
)


def trace_radar() -> rx.Component:
    return card(
        rx.text(SAFETY_COPY),
        rx.text(UNAVAILABLE_COPY),
        radar_chart("Trace Radar visual"),
        rx.text(BODY_COPY),
        rx.text(STATE_COPY),
        title="Trace Radar",
        badge=badge("unavailable", "warning"),
        variant="console",
    )
