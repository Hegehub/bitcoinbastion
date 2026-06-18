from __future__ import annotations

import reflex as rx

from bastion_ui.components.layout.section import section
from bastion_ui.components.public.docs_grid import docs_grid
from bastion_ui.components.public.hero import public_hero
from bastion_ui.routes._public import public_page


def docs_page() -> rx.Component:
    return public_page(
        public_hero(
            "Documentation landing",
            "Docs are labeled conservatively so planned or pending areas do not appear complete.",
            primary_label="Platform overview",
            primary_href="/platform",
            secondary_label="Security",
            secondary_href="/security",
        ),
        section(docs_grid(), title="Documentation index"),
    )
