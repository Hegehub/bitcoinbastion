from __future__ import annotations

from typing import cast

import reflex as rx

from bastion_ui.components.console.console_nav import console_nav
from bastion_ui.components.console.degraded_mode_banner import console_degraded_mode_banner
from bastion_ui.components.console.module_tile import module_tile
from bastion_ui.components.layout.public_layout import public_layout



def dashboard_shell(title: str, content: rx.Component) -> rx.Component:
    sidebar = console_nav()
    modules = rx.grid(
        module_tile("Trace", "Trace module overview.", "/console/trace"),
        module_tile("Evidence", "Evidence chain and Proof Packet review.", "/console/evidence"),
        module_tile("Provider Health", "Provider status and degraded visibility.", "/console/provider-health"),
        module_tile("Market Intelligence", "Market intelligence preview.", "/console/market-intelligence"),
        module_tile("Time Machine", "Time Machine preview.", "/console/time-machine"),
        module_tile("Sovereign Grid", "Sovereign Grid preview.", "/console/sovereign-grid"),
        module_tile("Policy Engine", "Policy preview with human review.", "/console/policy"),
        module_tile("Audit Log", "Audit Log preview.", "/console/audit"),
        columns="2",
        spacing="4",
        width="100%",
    )
    return public_layout(cast(rx.Component, rx.vstack(
        rx.heading(title, size="7"),
        console_degraded_mode_banner(),
        rx.hstack(sidebar, rx.vstack(content, modules, width="100%"), align="start", width="100%"),
        spacing="5",
        width="100%",
    )))
