from __future__ import annotations

import reflex as rx

from bastion_ui.components.console.dashboard_shell import dashboard_shell
from bastion_ui.components.console.policy_console_panel import policy_console_panel


def console_policy_page() -> rx.Component:
    return dashboard_shell(policy_console_panel())
