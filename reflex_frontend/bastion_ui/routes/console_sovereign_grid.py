from __future__ import annotations

import reflex as rx

from bastion_ui.components.console.dashboard_shell import dashboard_shell
from bastion_ui.components.console.sovereign_grid_panel import sovereign_grid_panel


def console_sovereign_grid_page() -> rx.Component:
    return dashboard_shell(sovereign_grid_panel())
