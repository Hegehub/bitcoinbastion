from __future__ import annotations

from typing import cast

import reflex as rx

from bastion_ui.components.layout.public_layout import public_layout
from bastion_ui.components.trace.trace_confidence_panel import trace_confidence_panel
from bastion_ui.components.trace.trace_counterparty_panel import trace_counterparty_panel
from bastion_ui.components.trace.trace_evidence_summary import trace_evidence_summary
from bastion_ui.components.trace.trace_limitations_card import trace_limitations_card
from bastion_ui.components.trace.trace_origin_panel import trace_origin_panel
from bastion_ui.components.trace.trace_overview_card import trace_overview_card
from bastion_ui.components.trace.trace_policy_panel import trace_policy_panel
from bastion_ui.components.trace.trace_privacy_panel import trace_privacy_panel
from bastion_ui.components.trace.trace_report_header import trace_report_header
from bastion_ui.components.trace.trace_status_banner import trace_status_banner
from bastion_ui.components.trace.trace_timeline import trace_timeline
from bastion_ui.components.ui.safety_banner import safety_banner
from bastion_ui.components.ui.skeleton import skeleton
from bastion_ui.state.trace_state import TraceState


def trace_report_page() -> rx.Component:
    return public_layout(cast(rx.Component, rx.vstack(
        trace_report_header(TraceState.trace_report_id),
        safety_banner("trace"),
        trace_status_banner(),
        rx.cond(TraceState.loading, skeleton(height="4rem")),
        rx.cond(TraceState.error != "", rx.callout(TraceState.error, color_scheme="red")),
        trace_overview_card(TraceState.report),
        trace_timeline(TraceState.evidence),
        trace_privacy_panel(TraceState.privacy),
        trace_origin_panel(TraceState.origin),
        trace_confidence_panel(TraceState.provider_disagreement),
        trace_counterparty_panel(TraceState.counterparty),
        trace_policy_panel(TraceState.policy_facts),
        trace_evidence_summary(TraceState.evidence),
        trace_limitations_card(),
        rx.link("Open Proof Packet", href=f"/trace/{TraceState.trace_report_id}/proof-packet"),
        spacing="5",
        align="start",
        width="100%",
    )))
