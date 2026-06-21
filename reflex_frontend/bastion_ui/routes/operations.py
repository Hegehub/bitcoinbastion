from __future__ import annotations

import reflex as rx

from bastion_ui.components.public.runtime_profile_preview import runtime_profile_preview
from bastion_ui.components.ui.card import card
from bastion_ui.routes._shared import public_page


def operations_page() -> rx.Component:
    return public_page(
        "Operations",
        card(
            rx.text(
                "Deployment posture is self-hostable, evidence-driven, and operator-controlled."
            ),
            rx.text("No cloud lock-in is required by the public Reflex route plan."),
            rx.text("Runtime profiles are not claimed production-equivalent without validation."),
            title="Deployment philosophy",
        ),
        runtime_profile_preview(),
        card(
            rx.text(
                "Operators keep rollback control while Next.js and FastAPI/Jinja remain available."
            ),
            title="Rollback discipline",
        ),
        subtitle="Self-hosting and runtime profile overview.",
    )
