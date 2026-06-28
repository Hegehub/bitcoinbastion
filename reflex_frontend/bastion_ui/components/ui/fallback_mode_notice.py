from __future__ import annotations

import reflex as rx

from bastion_ui.components.ui.alert import alert

FALLBACK_MODE_COPY = "Fallback mode active. Results may be partial and provider-dependent."


def fallback_mode_notice(message: str = FALLBACK_MODE_COPY) -> rx.Component:
    return alert(message, "advisory")
