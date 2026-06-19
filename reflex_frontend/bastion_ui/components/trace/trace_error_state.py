from __future__ import annotations

import reflex as rx

from bastion_ui.components.feedback.error_state import error_state
from bastion_ui.state.trace_state import TraceState


def trace_error_state() -> rx.Component:
    return error_state(TraceState.error)
