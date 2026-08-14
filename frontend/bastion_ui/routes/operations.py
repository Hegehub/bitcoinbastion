from __future__ import annotations

import reflex as rx

from bastion_ui.components.layout.grid import responsive_grid
from bastion_ui.components.operations.screens import (
    health_section,
    providers_section,
    storage_section,
)
from bastion_ui.routes._shared import public_page


def operations_page() -> rx.Component:
    return public_page(
        "Operations",
        health_section(compact=True),
        responsive_grid(providers_section(compact=True), storage_section(compact=True)),
        subtitle="Health, providers and storage. Incidents, SLOs and jobs remain Prompt 9.",
    )
