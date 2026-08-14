from __future__ import annotations

from typing import cast

import reflex as rx

from bastion_ui.components.evidence.proof_packet_viewer import proof_packet_viewer
from bastion_ui.routes._shared import public_page
from bastion_ui.routes.system import not_found_page
from bastion_ui.state.trace_report_state import TraceReportState


def trace_proof_packet_page() -> rx.Component:
    content = public_page(
        "Trace proof packet",
        proof_packet_viewer(),
        subtitle="Proof Packet availability depends on backend endpoint access.",
    )
    return cast(
        rx.Component,
        rx.cond(
            TraceReportState.route_validated & TraceReportState.route_valid,
            content,
            not_found_page(),
        ),
    )
