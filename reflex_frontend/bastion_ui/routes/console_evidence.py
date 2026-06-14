from __future__ import annotations

import reflex as rx

from bastion_ui.components.console.dashboard_shell import dashboard_shell
from bastion_ui.components.ui.card import card


def console_evidence_page() -> rx.Component:
    return dashboard_shell("Console Evidence", rx.vstack(
        card(rx.text("Evidence chain placeholder. No fake data is generated."), title="Evidence Chain"),
        card(rx.text("Proof Packet placeholder. Unavailable evidence is not hidden."), title="Proof Packet"),
        card(rx.text("Replay and audit placeholder. Backend evidence is required for live data."), title="Replay and Audit"),
        spacing="4",
        width="100%",
    ))
