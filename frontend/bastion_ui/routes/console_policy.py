from __future__ import annotations

import reflex as rx

from bastion_ui.components.console.dashboard_shell import dashboard_shell
from bastion_ui.components.console.policy_console_panel import policy_console_panel
from bastion_ui.components.wow.policy_simulator_preview import policy_simulator_preview


def console_policy_page() -> rx.Component:
    return dashboard_shell(policy_console_panel(), policy_simulator_preview())
