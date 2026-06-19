from __future__ import annotations

import reflex as rx

from bastion_ui.components.layout.grid import responsive_grid
from bastion_ui.components.layout.section import section
from bastion_ui.components.public.hero import public_hero
from bastion_ui.components.trace.address_check_form import address_check_form
from bastion_ui.components.trace.trace_limitations_card import trace_limitations_card
from bastion_ui.components.trace.trace_safety_banner import trace_safety_banner
from bastion_ui.components.ui.card import card
from bastion_ui.routes._public import public_page


def trace_page() -> rx.Component:
    return public_page(
        public_hero(
            "Bastion Trace",
            "A public-address intelligence layer for Bitcoin risk context, source disagreement, "
            "privacy exposure, and evidence-based review.",
            primary_label="Check an address",
            primary_href="/check",
            secondary_label="Trace status",
            secondary_href="/status",
        ),
        trace_safety_banner(),
        address_check_form(),
        section(
            responsive_grid(
                card(
                    rx.text("Source-based context and manual review hints."),
                    title="What Trace can show",
                ),
                card(
                    rx.text("Provider disagreement, degraded data, and confidence gaps."),
                    title="Uncertainty stays visible",
                ),
                card(
                    rx.text(
                        "Trace does not custody funds, sign transactions, or prove legal status."
                    ),
                    title="What Trace cannot prove",
                ),
            ),
            title="Trace overview",
        ),
        trace_limitations_card(),
        section(
            responsive_grid(
                card(rx.link("Evidence overview", href="/evidence"), title="Evidence"),
                card(rx.link("Public status", href="/status"), title="Status"),
                card(rx.link("Documentation", href="/docs"), title="Docs"),
            ),
            title="Related public routes",
        ),
    )
