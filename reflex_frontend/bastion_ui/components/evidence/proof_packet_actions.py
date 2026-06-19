from __future__ import annotations

import reflex as rx

from bastion_ui.components.ui.card import card


def proof_packet_actions(report_id: str = "Route report id") -> rx.Component:
    return card(
        rx.link("Back to Trace Report", href=f"/trace/{report_id}"),
        rx.link("Open Evidence Overview", href="/evidence"),
        rx.text("Refresh uses route-driven loading when backend DTOs are available."),
        title="Proof Packet actions",
    )
