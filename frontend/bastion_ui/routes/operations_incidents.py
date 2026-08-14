import reflex as rx

from bastion_ui.components.operations.screens import incidents_section
from bastion_ui.routes._shared import public_page


def operations_incidents_page() -> rx.Component:
    return public_page(
        "Operations Incidents",
        incidents_section(),
        subtitle="Durable detector-owned incident lifecycle and history.",
    )
