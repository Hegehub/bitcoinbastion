from __future__ import annotations

import reflex as rx

from bastion_ui.components.ui.empty_state import empty_state


def trace_empty_state() -> rx.Component:
    return empty_state(
        "No address checked yet",
        "Enter a public Bitcoin address to request an advisory Trace Lite result.",
    )
