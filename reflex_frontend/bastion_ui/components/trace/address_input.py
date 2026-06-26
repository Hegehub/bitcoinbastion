from __future__ import annotations

from typing import cast

import reflex as rx

from bastion_ui.state.trace_state import TraceState
from bastion_ui.theme.styles import INPUT


def address_input() -> rx.Component:
    return cast(
        rx.Component,
        rx.vstack(
            rx.text("Public Bitcoin address", weight="bold"),
            rx.input(
                placeholder="bc1..., 1..., or 3...",
                value=TraceState.address,
                on_change=TraceState.set_address,
                style=INPUT,
            ),
            rx.cond(
                TraceState.validation_error != "",
                rx.text(TraceState.validation_error, color="#EF4444"),
            ),
            rx.text("Only public Bitcoin addresses are accepted."),
            align="start",
            width="100%",
        ),
    )
