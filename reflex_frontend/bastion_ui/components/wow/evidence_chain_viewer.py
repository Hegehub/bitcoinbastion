from __future__ import annotations

import reflex as rx

from bastion_ui.components.charts.timeline import timeline_chart
from bastion_ui.components.ui.badge import badge
from bastion_ui.components.ui.card import card

SAFETY_COPY = "Evidence is advisory and source-dependent. This is not Bitcoin consensus proof."
UNAVAILABLE_COPY = (
    "Live operational data is unavailable. This panel is displaying safe unavailable states only."
)
STATE_COPY = (
    "Loading, empty, error, degraded, unavailable, and unknown states are "
    "represented without backend-owned verdict logic."
)
BODY_COPY = (
    "Evidence chain fields include packet id, source name, source status, "
    "timestamp, quality indicator, replay availability, and degraded "
    "indicator."
)


def evidence_chain_viewer() -> rx.Component:
    return card(
        rx.text(SAFETY_COPY),
        rx.text(UNAVAILABLE_COPY),
        timeline_chart("Evidence Chain Viewer visual"),
        rx.text(BODY_COPY),
        rx.text(STATE_COPY),
        title="Evidence Chain Viewer",
        badge=badge("unavailable", "warning"),
        variant="console",
    )
