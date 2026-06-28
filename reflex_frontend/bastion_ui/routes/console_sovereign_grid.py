from __future__ import annotations

import reflex as rx

from bastion_ui.components.console.dashboard_shell import dashboard_shell
from bastion_ui.components.console.sovereign_grid_panel import sovereign_grid_panel
from bastion_ui.components.wow.node_pulse import node_pulse
from bastion_ui.components.wow.sovereign_grid_map import sovereign_grid_map


def console_sovereign_grid_page() -> rx.Component:
    return dashboard_shell(sovereign_grid_panel(), sovereign_grid_map(), node_pulse())
