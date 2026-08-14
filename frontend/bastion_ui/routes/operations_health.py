from __future__ import annotations

import reflex as rx

from bastion_ui.components.operations.screens import health_section
from bastion_ui.routes._shared import public_page


def operations_health_page() -> rx.Component:
    return public_page(
        "Operations Health",
        health_section(),
        subtitle="Authoritative API and dependency status; no frontend health score.",
    )
