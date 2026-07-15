from __future__ import annotations

import reflex as rx

from bastion_ui.components.public.roadmap_preview import CONSERVATIVE_STATUS_LABELS, roadmap_preview
from bastion_ui.components.ui.card import card
from bastion_ui.routes._shared import public_page


def roadmap_page() -> rx.Component:
    return public_page(
        "Roadmap",
        roadmap_preview(),
        card(
            rx.text("Conservative status labels: " + ", ".join(CONSERVATIVE_STATUS_LABELS) + "."),
            rx.text(
                "Next major steps: Trace Lite, /check, /trace public flow, then "
                "report and Proof Packet parity."
            ),
            rx.text(
                "Blockers include Trace route parity, Market DTO verification, "
                "Console endpoint contracts, and rollback evidence."
            ),
            title="Migration sequence",
        ),
        subtitle="Implemented, baseline, experimental, planned, blocked, and future work.",
    )
