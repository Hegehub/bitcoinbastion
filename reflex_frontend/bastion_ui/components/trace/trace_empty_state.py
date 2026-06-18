from __future__ import annotations

import reflex as rx

from bastion_ui.components.ui.empty_state import empty_state


def trace_empty_state() -> rx.Component:
    return empty_state(
        "No Trace result yet",
        "Enter a public Bitcoin address to request advisory source-based context.",
    )
