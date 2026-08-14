from __future__ import annotations

from typing import cast

import reflex as rx

from bastion_ui.components.console.degraded_state_banner import degraded_state_banner
from bastion_ui.components.console.historical_similarity_card import historical_similarity_card
from bastion_ui.components.console.provider_freshness_card import provider_freshness_card
from bastion_ui.components.console.time_machine_timeline import time_machine_timeline
from bastion_ui.components.layout.grid import responsive_grid
from bastion_ui.components.ui.badge import badge
from bastion_ui.components.ui.card import card
from bastion_ui.topology import path_for

TIME_MACHINE_SAFETY_COPY = (
    "Historical similarity is not prediction. This view explains context and evidence, "
    "not future certainty. This is not financial advice."
)


def time_machine_panel() -> rx.Component:
    return cast(
        rx.Component,
        rx.vstack(
            rx.heading("Market Time Machine", size="6"),
            rx.text(
                "Operator view for historical market context, evidence, "
                "candle attribution, and narrative context."
            ),
            card(rx.text(TIME_MACHINE_SAFETY_COPY), title="Time Machine safety", variant="safety"),
            degraded_state_banner(),
            responsive_grid(
                time_machine_timeline(), historical_similarity_card(), provider_freshness_card()
            ),
            card(
                rx.text(
                    "Selected candle or event detail is unavailable until backend "
                    "DTO data is selected."
                ),
                rx.text("No candle attribution is fabricated by the Reflex console."),
                title="Selected event detail",
                badge=badge("empty", "warning"),
                variant="console",
            ),
            card(
                rx.text(
                    "Evidence packet and narrative context links appear only when "
                    "backend DTOs provide ids."
                ),
                rx.link("Open public Time Machine route", href=path_for("market.time_machine")),
                title="Evidence and narrative context",
                variant="console",
            ),
            align="start",
            spacing="4",
            width="100%",
        ),
    )
