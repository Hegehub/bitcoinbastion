from __future__ import annotations

import reflex as rx

from bastion_ui.components.layout.grid import responsive_grid
from bastion_ui.components.trace.trace_confidence_panel import trace_confidence_panel
from bastion_ui.components.trace.trace_counterparty_panel import trace_counterparty_panel
from bastion_ui.components.trace.trace_evidence_summary import trace_evidence_summary
from bastion_ui.components.trace.trace_limitations_card import trace_limitations_card
from bastion_ui.components.trace.trace_origin_panel import trace_origin_panel
from bastion_ui.components.trace.trace_overview_card import trace_overview_card
from bastion_ui.components.trace.trace_policy_facts_panel import trace_policy_facts_panel
from bastion_ui.components.trace.trace_privacy_panel import trace_privacy_panel
from bastion_ui.components.trace.trace_report_header import trace_report_header
from bastion_ui.components.trace.trace_safety_banner import trace_safety_banner
from bastion_ui.components.trace.trace_source_disagreement_panel import (
    trace_source_disagreement_panel,
)
from bastion_ui.components.trace.trace_status_banner import trace_status_banner
from bastion_ui.components.trace.trace_utxo_hygiene_panel import trace_utxo_hygiene_panel
from bastion_ui.routes._shared import link_card, public_page
from bastion_ui.state.trace_report_state import TraceReportState


def trace_report_page() -> rx.Component:
    return public_page(
        "Trace report",
        trace_report_header(),
        trace_safety_banner(),
        trace_status_banner(),
        rx.cond(TraceReportState.error != "", rx.text(TraceReportState.error)),
        responsive_grid(
            trace_overview_card(),
            trace_confidence_panel(),
            trace_evidence_summary(),
            trace_origin_panel(),
            trace_privacy_panel(),
            trace_source_disagreement_panel(),
            trace_utxo_hygiene_panel(),
            trace_counterparty_panel(),
            trace_policy_facts_panel(),
        ),
        trace_limitations_card(),
        responsive_grid(
            link_card(
                "Proof packet", "/trace/[report_id]/proof-packet", "Open proof packet route."
            ),
            link_card("Back to Trace", "/trace", "Start another public-address review."),
        ),
        subtitle="Detailed advisory Trace report. Dynamic data loads only from backend APIs.",
    )
