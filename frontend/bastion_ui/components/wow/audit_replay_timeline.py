from __future__ import annotations

import reflex as rx

from bastion_ui.components.charts.timeline import timeline_chart
from bastion_ui.components.ui.badge import badge
from bastion_ui.components.ui.card import card

SAFETY_COPY = "Audit replay is operator context only; no audit entries are fabricated."
UNAVAILABLE_COPY = (
    "Live operational data is unavailable. This panel is displaying safe unavailable states only."
)
STATE_COPY = (
    "Loading, empty, error, degraded, unavailable, and unknown states are "
    "represented without backend-owned verdict logic."
)
BODY_COPY = (
    "Displays event type, timestamp, source, status, confidence or "
    "quality, and related evidence packet only when backend data exists."
)


def audit_replay_timeline() -> rx.Component:
    return card(
        rx.text(SAFETY_COPY),
        rx.text(UNAVAILABLE_COPY),
        timeline_chart("Audit Replay Timeline visual"),
        rx.text(BODY_COPY),
        rx.text(STATE_COPY),
        title="Audit Replay Timeline",
        badge=badge("unavailable", "warning"),
        variant="console",
    )
