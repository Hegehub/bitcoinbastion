from __future__ import annotations

import reflex as rx

from bastion_ui.components.ui.safety_banner import degraded_state_banner


def console_degraded_mode_banner() -> rx.Component:
    return degraded_state_banner("Console modules may show delayed, degraded, stale, fallback, or unavailable state.")
