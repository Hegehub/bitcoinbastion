from __future__ import annotations

import reflex as rx

from bastion_ui.components.wow._shared import wow_card


def time_machine_timeline() -> rx.Component:
    return wow_card("Time Machine Timeline", "Selected timeframe: preview", "Event markers and candle attribution preview: unavailable until backend data is returned.", "Historical similarity does not guarantee future market behavior.", "Correlation is not proof of causation.")
