import reflex as rx

from bastion_ui.components.operations.screens import slo_section
from bastion_ui.routes._shared import public_page


def operations_slo_page() -> rx.Component:
    return public_page(
        "Operations SLO",
        slo_section(),
        subtitle="Backend-evaluated objectives; missing data never silently passes.",
    )
