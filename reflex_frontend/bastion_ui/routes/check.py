from __future__ import annotations

import reflex as rx

from bastion_ui.components.layout.section import section
from bastion_ui.components.public.hero import public_hero
from bastion_ui.components.trace.address_check_form import address_check_form
from bastion_ui.components.trace.trace_limitations_card import trace_limitations_card
from bastion_ui.components.trace.trace_safety_banner import trace_safety_banner
from bastion_ui.components.ui.card import card
from bastion_ui.routes._public import public_page


def check_page() -> rx.Component:
    return public_page(
        public_hero(
            "Check a public Bitcoin address",
            "Bitcoin Bastion Trace provides advisory intelligence based on available sources. "
            "It is not legal verification, not Bitcoin consensus proof, and "
            "not a guarantee of safety.",
            primary_label="Open Trace overview",
            primary_href="/trace",
            secondary_label="Evidence overview",
            secondary_href="/evidence",
        ),
        trace_safety_banner(),
        address_check_form(),
        trace_limitations_card(),
        section(
            card(
                rx.link("Open broader Trace overview", href="/trace"),
                title="Trace overview",
            ),
            title="Next step",
        ),
    )
