from __future__ import annotations

from typing import cast

import reflex as rx

from bastion_ui.security.address_validation import INVALID_ADDRESS_MESSAGE
from bastion_ui.state.trace_state import TraceState
from bastion_ui.theme.styles import INPUT

ADDRESS_INPUT_LABEL = "Public Bitcoin address"
ADDRESS_INPUT_DESCRIPTION = (
    "Use a public Bitcoin address beginning with bc1, 1, or 3. Do not enter wallet secrets."
)


def address_input() -> rx.Component:
    return cast(
        rx.Component,
        rx.vstack(
            rx.text(ADDRESS_INPUT_LABEL, weight="bold"),
            rx.input(
                placeholder="bc1q...",
                value=TraceState.address,
                on_change=TraceState.set_address,
                style=INPUT,
                aria_label=ADDRESS_INPUT_LABEL,
            ),
            rx.text(ADDRESS_INPUT_DESCRIPTION, size="2"),
            rx.cond(
                TraceState.validation_error != "",
                rx.text(TraceState.validation_error, color="red", role="alert"),
                rx.text(INVALID_ADDRESS_MESSAGE, size="1", color="gray"),
            ),
            align="start",
            spacing="2",
            width="100%",
        ),
    )
