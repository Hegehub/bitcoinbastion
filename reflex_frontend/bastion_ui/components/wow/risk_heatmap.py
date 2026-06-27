from __future__ import annotations

import reflex as rx

from bastion_ui.components.charts.heatmap import heatmap_chart
from bastion_ui.components.ui.badge import badge
from bastion_ui.components.ui.card import card

SAFETY_COPY = "Risk heatmap is advisory and does not calculate final verdicts in the frontend."
UNAVAILABLE_COPY = (
    "Live operational data is unavailable. This panel is displaying safe unavailable states only."
)
STATE_COPY = (
    "Loading, empty, error, degraded, unavailable, and unknown states are "
    "represented without backend-owned verdict logic."
)
BODY_COPY = (
    "Risk bands use low, medium, elevated, high, and unknown for Trace, "
    "Market, Provider Health, Treasury, Policy, Evidence, and Runtime."
)


def risk_heatmap() -> rx.Component:
    return card(
        rx.text(SAFETY_COPY),
        rx.text(UNAVAILABLE_COPY),
        heatmap_chart("Risk Heatmap visual"),
        rx.text(BODY_COPY),
        rx.text(STATE_COPY),
        title="Risk Heatmap",
        badge=badge("unavailable", "warning"),
        variant="console",
    )
