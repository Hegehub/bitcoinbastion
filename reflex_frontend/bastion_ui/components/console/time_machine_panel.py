from __future__ import annotations

from typing import cast

import reflex as rx

from bastion_ui.components.console._panel_helpers import preview_card


def time_machine_panel() -> rx.Component:
    return cast(rx.Component, rx.grid(
        preview_card("Timeline preview", "Links may reference /market without replacing it."),
        preview_card("Historical similarity preview", "Historical similarity does not guarantee future market behavior."),
        preview_card("Evidence packet preview", "Past market reactions are contextual evidence only."),
        preview_card("Replay status preview", "Correlation is not causation."),
        preview_card("Narrative context preview", "No heavy charting is implemented in this prompt."),
        preview_card("Provider confidence preview", "Degraded states are intentionally visible."),
        columns="2",
        spacing="4",
        width="100%",
    ))
