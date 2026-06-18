from __future__ import annotations

import reflex as rx

from bastion_ui.components.layout.section import section
from bastion_ui.components.public.hero import public_hero
from bastion_ui.components.public.roadmap_preview import (
    CONSERVATIVE_ROADMAP_STATUSES,
    roadmap_preview,
)
from bastion_ui.components.ui.card import card
from bastion_ui.routes._public import public_page

ROADMAP_API_ENDPOINT = "/api/v1/public/roadmap"


def roadmap_page() -> rx.Component:
    return public_page(
        public_hero(
            "Roadmap with conservative readiness labels",
            "The Reflex migration proceeds by documented route, API, and safety parity gates.",
            primary_label="Review blockers",
            primary_href="/status",
            secondary_label="Read docs",
            secondary_href="/docs",
        ),
        roadmap_preview(),
        section(
            card(
                rx.text("Allowed statuses: " + ", ".join(CONSERVATIVE_ROADMAP_STATUSES)),
                rx.text(f"API dependency: {ROADMAP_API_ENDPOINT}"),
                rx.text("No cutover occurs until all required gates pass."),
                title="Migration labels",
            ),
            title="Frontend migration steps",
        ),
    )
