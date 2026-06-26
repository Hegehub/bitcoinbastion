from __future__ import annotations

import reflex as rx

from bastion_ui.components.console.dashboard_shell import dashboard_shell
from bastion_ui.components.console.trace_console_panel import trace_console_panel


def console_trace_page() -> rx.Component:
    return dashboard_shell(trace_console_panel())
