from __future__ import annotations

import reflex as rx

from bastion_ui.components.operations.screens import storage_section
from bastion_ui.routes._shared import public_page


def operations_storage_page() -> rx.Component:
    return public_page(
        "Operations Storage",
        storage_section(),
        subtitle="Sanitized storage posture without credentials or connection metadata.",
    )
