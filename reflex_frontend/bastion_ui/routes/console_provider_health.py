from __future__ import annotations

import reflex as rx

from bastion_ui.components.console.dashboard_shell import dashboard_shell
from bastion_ui.components.console.provider_health_panel import provider_health_panel
from bastion_ui.components.wow.degraded_mode_banner import wow_degraded_mode_banner
from bastion_ui.components.wow.provider_trust_matrix import provider_trust_matrix


def console_provider_health_page() -> rx.Component:
    return dashboard_shell(
        provider_health_panel(), wow_degraded_mode_banner(), provider_trust_matrix()
    )
