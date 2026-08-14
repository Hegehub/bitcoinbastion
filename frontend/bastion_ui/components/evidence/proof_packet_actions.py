from __future__ import annotations

import reflex as rx

from bastion_ui.components.ui.card import card
from bastion_ui.state.evidence_state import EvidenceState
from bastion_ui.topology import dynamic_route_parts, path_for


def proof_packet_actions() -> rx.Component:
    report_prefix, report_suffix = dynamic_route_parts("trace.report", "report_id")
    return card(
        rx.link(
            "Back to Trace Report",
            href=report_prefix + EvidenceState.evidence_report_id + report_suffix,
        ),
        rx.link("Open Evidence Overview", href=path_for("evidence")),
        rx.text("Refresh actions will call backend APIs only; no export action is shown here."),
        title="Actions",
    )
