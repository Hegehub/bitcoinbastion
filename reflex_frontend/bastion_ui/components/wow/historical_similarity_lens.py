from __future__ import annotations

import reflex as rx

from bastion_ui.components.ui.badge import badge
from bastion_ui.components.ui.card import card

SAFETY_COPY = "Historical similarity is contextual, not predictive certainty."
UNAVAILABLE_COPY = (
    "Live operational data is unavailable. This panel is displaying safe unavailable states only."
)
STATE_COPY = (
    "Loading, empty, error, degraded, unavailable, and unknown states are "
    "represented without backend-owned verdict logic."
)
BODY_COPY = (
    "Historical matches are not invented; unavailable state is shown when backend data is absent."
)


def historical_similarity_lens() -> rx.Component:
    return card(
        rx.text(SAFETY_COPY),
        rx.text(UNAVAILABLE_COPY),
        rx.text(BODY_COPY),
        rx.text(STATE_COPY),
        title="Historical Similarity Lens",
        badge=badge("unavailable", "warning"),
        variant="console",
    )
