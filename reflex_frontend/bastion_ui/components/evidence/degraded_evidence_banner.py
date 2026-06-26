from __future__ import annotations

import reflex as rx

from bastion_ui.components.ui.safety_banner import safety_banner


def degraded_evidence_banner() -> rx.Component:
    return safety_banner("degraded")
