from __future__ import annotations

import reflex as rx

from bastion_ui.components.ui.alert import alert


def degraded_state(
    message: str = "Data source degraded. This view may be incomplete.",
) -> rx.Component:
    return alert(message, "degraded")


def provider_unavailable_state() -> rx.Component:
    return degraded_state("Some providers are unavailable. Manual review recommended.")
