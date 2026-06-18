from __future__ import annotations

import reflex as rx

from bastion_ui.components.feedback.loading_state import loading_state
from bastion_ui.components.ui.card import card


def trace_loading_state() -> rx.Component:
    return card(loading_state("Checking public address with Trace API."), title="Checking address")
