from __future__ import annotations

from typing import cast

import reflex as rx

from bastion_ui.components.trace.address_input import address_input
from bastion_ui.components.trace.trace_lite_result_card import trace_lite_result_card
from bastion_ui.state.trace_state import TraceState


def address_check_form() -> rx.Component:
    return cast(rx.Component, rx.vstack(
        address_input(),
        rx.button("Check address", on_click=TraceState.submit_address_check, disabled=TraceState.loading),
        rx.cond(TraceState.loading, rx.text("Loading Trace summary...")),
        rx.cond(TraceState.error != "", rx.callout(TraceState.error, color_scheme="red")),
        rx.cond(TraceState.summary != {}, trace_lite_result_card(TraceState.summary)),
        spacing="3",
        width="100%",
    ))
