from __future__ import annotations

from typing import cast

import reflex as rx

from bastion_ui.components.trace.address_check_form import address_check_form
from bastion_ui.components.trace.trace_empty_state import trace_empty_state
from bastion_ui.components.trace.trace_error_state import trace_error_state
from bastion_ui.components.trace.trace_limitations_card import trace_limitations_card
from bastion_ui.components.trace.trace_lite_result_card import trace_lite_result_card
from bastion_ui.components.trace.trace_loading_state import trace_loading_state
from bastion_ui.components.trace.trace_safety_banner import trace_safety_banner
from bastion_ui.components.ui.card import card
from bastion_ui.state.trace_state import TraceState


def trace_public_flow() -> rx.Component:
    return cast(
        rx.Component,
        rx.vstack(
            trace_safety_banner(),
            card(address_check_form(), title="Check a public Bitcoin address"),
            rx.cond(TraceState.loading, trace_loading_state()),
            rx.cond(TraceState.error != "", trace_error_state(TraceState.error)),
            rx.cond(
                TraceState.result != {},
                trace_lite_result_card(),
                trace_empty_state(),
            ),
            trace_limitations_card(),
            align="start",
            spacing="4",
            width="100%",
        ),
    )
