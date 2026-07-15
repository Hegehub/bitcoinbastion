from __future__ import annotations

import reflex as rx

from bastion_ui.components.evidence.degraded_evidence_banner import degraded_evidence_banner
from bastion_ui.components.evidence.evidence_chain import evidence_chain
from bastion_ui.components.evidence.evidence_limitations_card import evidence_limitations_card
from bastion_ui.components.evidence.source_disagreement_panel import source_disagreement_panel
from bastion_ui.components.layout.grid import responsive_grid
from bastion_ui.components.public.evidence_overview import evidence_overview
from bastion_ui.components.ui.safety_banner import safety_banner
from bastion_ui.routes._shared import link_card, public_page


def evidence_page() -> rx.Component:
    return public_page(
        "Evidence",
        safety_banner("advisory"),
        evidence_overview(),
        responsive_grid(
            link_card("Trace", "/trace", "Trace links evidence to advisory reports."),
            link_card("Status", "/status", "Provider and backend status affects evidence quality."),
        ),
        responsive_grid(
            link_card(
                "What a Proof Packet contains",
                "/docs",
                "Source material, evidence items, timestamps, provider context, and limitations.",
            ),
            link_card(
                "What it does not prove",
                "/security",
                "No legal verification, payment approval, custody, or Bitcoin consensus proof.",
            ),
        ),
        source_disagreement_panel(),
        degraded_evidence_banner(),
        evidence_chain(),
        evidence_limitations_card(),
        subtitle=(
            "Evidence packets, audit trails, replay concepts, provider disagreement, "
            "and limitations."
        ),
    )
