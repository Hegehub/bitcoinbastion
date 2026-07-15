from __future__ import annotations

import reflex as rx

from bastion_ui.components.public.docs_grid import docs_grid
from bastion_ui.routes._shared import public_page


def docs_page() -> rx.Component:
    return public_page(
        "Docs",
        docs_grid(),
        subtitle=(
            "Documentation landing page with pending/planned labels where docs are not complete."
        ),
    )
