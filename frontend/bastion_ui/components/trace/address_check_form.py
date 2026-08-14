from __future__ import annotations

from typing import cast

import reflex as rx

from bastion_ui.components.trace.address_input import address_input
from bastion_ui.state.trace_state import TraceState


def address_check_form() -> rx.Component:
    return cast(
        rx.Component,
        rx.vstack(
            address_input(),
            rx.button(
                rx.cond(TraceState.loading, "Submitting…", "Submit Trace"),
                on_click=TraceState.submit_address_check,
                disabled=TraceState.loading,
                aria_label="Submit public Bitcoin address for advisory Trace analysis",
            ),
            rx.button("Reset", on_click=TraceState.reset_result, variant="soft"),
            align="start",
            spacing="3",
            width="100%",
        ),
    )
