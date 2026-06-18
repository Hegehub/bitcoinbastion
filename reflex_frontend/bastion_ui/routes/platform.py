from __future__ import annotations

import reflex as rx

from bastion_ui.components.layout.section import section
from bastion_ui.components.public.feature_grid import feature_grid
from bastion_ui.components.public.hero import public_hero
from bastion_ui.components.public.safety_section import safety_section
from bastion_ui.routes._public import public_page

PLATFORM_AREAS = (
    ("FastAPI backend", "Backend APIs remain the source of data and decisions.", "implemented"),
    ("Trace layer", "Trace workflows are migrated later and remain advisory-only.", "planned"),
    (
        "Evidence layer",
        "Source material, reasoning, and packets are surfaced for review.",
        "baseline",
    ),
    ("Market Intelligence", "Market dashboard remains delegated during parity work.", "planned"),
    ("Policy control", "Operator policy views must be review-first.", "baseline"),
    ("Runtime deployment", "Docker and local-first profiles are the baseline path.", "baseline"),
    (
        "Developer API",
        "Reflex clients call public backend endpoints without duplicating logic.",
        "baseline",
    ),
)


def platform_page() -> rx.Component:
    return public_page(
        public_hero(
            "Bitcoin-first sovereign intelligence and operations infrastructure.",
            "The platform combines backend APIs, evidence surfaces, operator controls, and "
            "deployment profiles without custody or signing behavior.",
            primary_label="Review Evidence",
            primary_href="/evidence",
            secondary_label="Read Docs",
            secondary_href="/docs",
        ),
        section(feature_grid(PLATFORM_AREAS), title="Platform layers"),
        safety_section(),
        rx.text("Readiness remains gated by documented route, API, and safety parity."),
    )
