from __future__ import annotations

import reflex as rx

from bastion_ui.components.charts.matrix import matrix_chart
from bastion_ui.components.ui.badge import badge
from bastion_ui.components.ui.card import card

SAFETY_COPY = "Provider trust is source-dependent and disagreement must remain visible."
UNAVAILABLE_COPY = (
    "Live operational data is unavailable. This panel is displaying safe unavailable states only."
)
STATE_COPY = (
    "Loading, empty, error, degraded, unavailable, and unknown states are "
    "represented without backend-owned verdict logic."
)
BODY_COPY = (
    "Provider states include healthy, degraded, stale, offline, fallback, "
    "and unknown; degraded providers remain visible."
)


def provider_trust_matrix() -> rx.Component:
    return card(
        rx.text(SAFETY_COPY),
        rx.text(UNAVAILABLE_COPY),
        matrix_chart("Provider Trust Matrix visual"),
        rx.text(BODY_COPY),
        rx.text(STATE_COPY),
        title="Provider Trust Matrix",
        badge=badge("unavailable", "warning"),
        variant="console",
    )
