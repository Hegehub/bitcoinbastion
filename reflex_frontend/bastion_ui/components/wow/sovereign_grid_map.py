from __future__ import annotations

import reflex as rx

from bastion_ui.components.charts.matrix import matrix_chart
from bastion_ui.components.ui.badge import badge
from bastion_ui.components.ui.card import card

SAFETY_COPY = (
    "Conceptual topology only; this does not introduce distributed backend "
    "mesh, P2P mesh, or Stratum/mining support."
)
UNAVAILABLE_COPY = (
    "Live operational data is unavailable. This panel is displaying safe unavailable states only."
)
STATE_COPY = (
    "Loading, empty, error, degraded, unavailable, and unknown states are "
    "represented without backend-owned verdict logic."
)
BODY_COPY = (
    "Conceptual topology: API, Worker, Beat, provider adapters, evidence "
    "pipeline, webhook dispatcher, Reflex frontend, and runtime profile."
)


def sovereign_grid_map() -> rx.Component:
    return card(
        rx.text(SAFETY_COPY),
        rx.text(UNAVAILABLE_COPY),
        matrix_chart("Sovereign Grid Map visual"),
        rx.text(BODY_COPY),
        rx.text(STATE_COPY),
        title="Sovereign Grid Map",
        badge=badge("unavailable", "warning"),
        variant="console",
    )
