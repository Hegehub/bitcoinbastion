from __future__ import annotations

from typing import Any

import reflex as rx

from bastion_ui.components.trace.trace_overview_card import panel_card


def trace_policy_panel(data: dict[str, Any] | None = None) -> rx.Component:
    return panel_card("Policy Facts", data)
