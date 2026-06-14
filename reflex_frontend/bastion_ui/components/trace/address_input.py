from __future__ import annotations

from typing import cast

import reflex as rx

from bastion_ui.state.trace_state import TraceState


def address_input() -> rx.Component:
    return cast(rx.Component, rx.input(placeholder="Public Bitcoin address only", value=TraceState.address, on_change=TraceState.set_address, width="100%"))
