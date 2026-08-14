from __future__ import annotations

import reflex as rx

from bastion_ui.components.operations.screens import providers_section
from bastion_ui.routes._shared import public_page


def operations_providers_page() -> rx.Component:
    return public_page(
        "Operations Providers",
        providers_section(),
        subtitle="Authoritative provider availability, freshness and latency.",
    )
