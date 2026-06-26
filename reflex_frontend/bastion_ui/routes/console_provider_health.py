from __future__ import annotations

import reflex as rx

from bastion_ui.components.console.dashboard_shell import dashboard_shell
from bastion_ui.components.console.provider_health_panel import provider_health_panel


def console_provider_health_page() -> rx.Component:
    return dashboard_shell(provider_health_panel())
