from __future__ import annotations

import reflex as rx

from bastion_ui.components.layout.grid import responsive_grid
from bastion_ui.components.layout.section import section
from bastion_ui.components.public.evidence_overview import evidence_overview
from bastion_ui.components.public.hero import public_hero
from bastion_ui.components.ui.card import card
from bastion_ui.routes._public import public_page


def evidence_page() -> rx.Component:
    return public_page(
        public_hero(
            "Evidence over claims",
            "Evidence in Bitcoin Bastion means source-dependent context, audit trails, "
            "provider disagreement, and replayable reasoning surfaces.",
            primary_label="Open Trace preview",
            primary_href="/trace",
            secondary_label="View Status",
            secondary_href="/status",
        ),
        evidence_overview(),
        section(
            responsive_grid(
                card(
                    rx.text("Proof Packet viewer migration is intentionally deferred."),
                    title="Proof packets",
                ),
                card(
                    rx.text("Audit trails should make source material reviewable."),
                    title="Audit trail",
                ),
                card(rx.text("Replay concepts must not fabricate evidence."), title="Replay"),
            ),
            title="Evidence concepts",
        ),
    )
