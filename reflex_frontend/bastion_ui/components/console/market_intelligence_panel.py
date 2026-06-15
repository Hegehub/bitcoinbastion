from __future__ import annotations

from typing import cast

import reflex as rx

from bastion_ui.components.console._panel_helpers import preview_card


def market_intelligence_panel() -> rx.Component:
    return cast(rx.Component, rx.grid(
        preview_card("BTC market context", "Evidence-based and informational only."),
        preview_card("News/event timeline preview", "Endpoint data may be degraded, fallback, stale, or unavailable."),
        preview_card("Signal governance preview", "Operator review queue preview; no financial advice."),
        preview_card("Provider health summary", "Provider disagreement and unavailable states remain visible."),
        preview_card("Narrative heatmap preview", "Historical similarity is contextual evidence, not prediction."),
        preview_card("Evidence/replay availability", "Replay availability is shown only when backend evidence exists."),
        preview_card("Operator review queue preview", "No automatic actions are exposed."),
        columns="2",
        spacing="4",
        width="100%",
    ))
