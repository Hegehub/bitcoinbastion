from __future__ import annotations

import reflex as rx

from bastion_ui.components.console.dashboard_shell import dashboard_shell
from bastion_ui.components.console.degraded_mode_banner import console_degraded_mode_banner
from bastion_ui.components.console.provider_health_matrix import provider_health_matrix


def console_provider_health_page() -> rx.Component:
    return dashboard_shell("Provider Health", rx.vstack(
        console_degraded_mode_banner(),
        rx.text("Provider failures, fallback, stale, degraded, and source-unavailable states must remain visible."),
        provider_health_matrix(),
        spacing="4",
        width="100%",
    ))
