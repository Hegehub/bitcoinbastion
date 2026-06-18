from __future__ import annotations

import reflex as rx

from bastion_ui.components.layout.section import section
from bastion_ui.components.public.feature_grid import feature_grid
from bastion_ui.components.public.hero import public_hero
from bastion_ui.routes._public import public_page

MANIFESTO_POINTS = (
    (
        "Bitcoin-first",
        "Design starts with Bitcoin public data and operator sovereignty.",
        "baseline",
    ),
    ("No custody", "The frontend must not custody funds or sign transactions.", "baseline"),
    ("Evidence over claims", "Interfaces should show sources and uncertainty.", "baseline"),
    ("Operator control", "Risky actions require human approval.", "baseline"),
    ("Self-hostability", "Rollback and self-hosting remain first-class disciplines.", "baseline"),
    (
        "No black-box trust",
        "Provider disagreement and limitations should remain visible.",
        "baseline",
    ),
    ("Auditability", "State changes and evidence should be reviewable.", "planned"),
    ("Rollback discipline", "Next.js remains available until parity gates pass.", "baseline"),
)


def manifesto_page() -> rx.Component:
    return public_page(
        public_hero(
            "A manifesto for sovereign Bitcoin operations",
            "Bitcoin Bastion should be inspectable, self-hostable, no-custody, and honest "
            "about limitations.",
        ),
        section(feature_grid(MANIFESTO_POINTS), title="Principles"),
        rx.text("Explicit limitation: this Reflex frontend is not production cutover yet."),
    )
