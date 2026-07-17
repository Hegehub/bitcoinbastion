from __future__ import annotations

import reflex as rx

from bastion_ui.components.console.console_sidebar import console_sidebar
from bastion_ui.components.console.console_status_strip import console_status_strip
from bastion_ui.components.console.console_topbar import console_topbar
from bastion_ui.components.console.degraded_mode_banner import degraded_mode_banner
from bastion_ui.components.console.operator_safety_panel import operator_safety_panel
from bastion_ui.components.layout.console_layout import console_layout


def dashboard_shell(*children: rx.Component) -> rx.Component:
    return console_layout(
        *children,
        sidebar=console_sidebar(),
        topbar=console_topbar(),
        degraded_banner=rx.vstack(console_status_strip(), degraded_mode_banner(), width="100%"),
        audit_footer=operator_safety_panel(),
    )
