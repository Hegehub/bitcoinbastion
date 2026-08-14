from __future__ import annotations

import reflex as rx

from bastion_ui.components.prompt9_screens import jobs_screen
from bastion_ui.routes._shared import public_page


def operations_jobs_page() -> rx.Component:
    return public_page(
        "Operations Jobs",
        jobs_screen(),
        subtitle="Authoritative job state, timing, scheduling, and bounded failure summaries.",
    )
