from __future__ import annotations

from typing import Any

import reflex as rx

from bastion_ui.components.ui.card import card


def provider_health_matrix(rows: list[dict[str, Any]] | None = None) -> rx.Component:
    if not rows:
        return card(rx.text("Provider health is unavailable. No provider failures are hidden; backend data is required for live status."), title="Provider Health Matrix")
    return card(rx.text(str(rows)), rx.text("Statuses include degraded, stale, fallback, and source-unavailable states when reported."), title="Provider Health Matrix")
