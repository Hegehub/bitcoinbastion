from __future__ import annotations

import reflex as rx

from bastion_ui.components.ui.badge import badge
from bastion_ui.components.ui.card import card


def time_machine_teaser() -> rx.Component:
    return card(
        rx.text("Market Time Machine migration is intentionally deferred to Prompt 12/22."),
        rx.text(
            "Timeline, candle drilldowns, replay, narratives, and historical "
            "similarity are pending."
        ),
        rx.link("Legacy Market Time Machine remains available", href="/market/time-machine"),
        title="Time Machine",
        subtitle="Pending migration; no completed-state claim is made here.",
        badge=badge("Pending Prompt 12/22", "warning"),
        variant="console",
    )
