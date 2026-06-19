from __future__ import annotations

import reflex as rx

from bastion_ui.components.feedback.loading_state import loading_state as feedback_loading_state


def loading_state(message: str = "Loading evidence…") -> rx.Component:
    return feedback_loading_state(message)
