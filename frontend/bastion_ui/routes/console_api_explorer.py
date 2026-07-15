from __future__ import annotations

import reflex as rx

from bastion_ui.components.console.api_explorer_panel import api_explorer_panel
from bastion_ui.components.console.dashboard_shell import dashboard_shell


def console_api_explorer_page() -> rx.Component:
    return dashboard_shell(api_explorer_panel())
