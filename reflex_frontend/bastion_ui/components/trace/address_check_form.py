from __future__ import annotations

import reflex as rx

from bastion_ui.components.trace.address_input import address_input
from bastion_ui.components.trace.trace_empty_state import trace_empty_state
from bastion_ui.components.trace.trace_error_state import trace_error_state
from bastion_ui.components.trace.trace_lite_result_card import trace_lite_result_card
from bastion_ui.components.trace.trace_loading_state import trace_loading_state
from bastion_ui.components.ui.card import card
from bastion_ui.state.trace_state import TraceState


def address_check_form() -> rx.Component:
    return card(
        address_input(),
        rx.button(
            "Check public address",
            on_click=TraceState.submit_address_check,
            disabled=TraceState.loading,
        ),
        rx.cond(TraceState.loading, trace_loading_state(), rx.fragment()),
        rx.cond(TraceState.error != "", trace_error_state(), rx.fragment()),
        rx.cond(
            (TraceState.result != {}) & (~TraceState.loading),
            trace_lite_result_card(),
            trace_empty_state(),
        ),
        title="Public address check",
    )
