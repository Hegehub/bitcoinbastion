from __future__ import annotations

import reflex as rx

from bastion_ui.components.evidence.degraded_evidence_banner import degraded_evidence_banner
from bastion_ui.components.evidence.evidence_chain import evidence_chain
from bastion_ui.components.evidence.evidence_limitations_card import evidence_limitations_card
from bastion_ui.components.evidence.proof_packet_card import proof_packet_card
from bastion_ui.components.evidence.source_disagreement_panel import source_disagreement_panel
from bastion_ui.components.layout.grid import responsive_grid
from bastion_ui.components.layout.section import section
from bastion_ui.components.public.hero import public_hero
from bastion_ui.components.ui.card import card
from bastion_ui.components.ui.safety_banner import safety_banner
from bastion_ui.routes._public import public_page


def evidence_page() -> rx.Component:
    return public_page(
        public_hero(
            "Evidence over claims",
            "Bastion Evidence is source-dependent advisory context, audit trails, provider "
            "disagreement, and replayable reasoning for operator review.",
            primary_label="Open Trace",
            primary_href="/trace",
            secondary_label="View Status",
            secondary_href="/status",
        ),
        safety_banner("advisory"),
        degraded_evidence_banner(),
        section(
            responsive_grid(
                card(
                    rx.text("Evidence is advisory-only and source-dependent."),
                    rx.text("Evidence is not legal verification."),
                    rx.text("Evidence is not Bitcoin consensus proof."),
                    title="Evidence Layer Overview",
                ),
                proof_packet_card(),
                card(
                    rx.text("A Proof Packet does not prove legal status or approve payments."),
                    rx.text("It can be incomplete, stale, degraded, or provider-disputed."),
                    title="What a Proof Packet Does Not Prove",
                ),
            ),
            title="Evidence overview",
        ),
        section(
            responsive_grid(
                source_disagreement_panel(),
                card(
                    rx.text("Bitcoin Bastion does not custody funds."),
                    rx.text(
                        "Never enter seed phrases, private keys, wallet files, or signing material."
                    ),
                    title="No-custody safety rules",
                    variant="safety",
                ),
            ),
            title="Provider disagreement and safety",
        ),
        section(evidence_chain(), title="Evidence chain UI"),
        evidence_limitations_card(),
    )
