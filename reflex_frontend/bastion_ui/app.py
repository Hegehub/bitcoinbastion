from __future__ import annotations

import reflex as rx

from bastion_ui.components.feedback.degraded_state import degraded_state
from bastion_ui.components.feedback.loading_state import loading_state
from bastion_ui.components.feedback.stale_data_banner import stale_data_banner
from bastion_ui.components.layout.command_palette import command_palette
from bastion_ui.components.layout.console_sidebar import console_sidebar
from bastion_ui.components.layout.footer import footer
from bastion_ui.components.layout.grid import responsive_grid
from bastion_ui.components.layout.header import header
from bastion_ui.components.layout.mobile_nav import mobile_nav
from bastion_ui.components.layout.public_layout import public_layout
from bastion_ui.components.safety.advisory_notice import advisory_notice
from bastion_ui.components.safety.no_custody_notice import no_custody_notice
from bastion_ui.components.safety.safety_banner import trace_safety_banner
from bastion_ui.components.ui.alert import alert
from bastion_ui.components.ui.badge import badge
from bastion_ui.components.ui.button import button
from bastion_ui.components.ui.card import card
from bastion_ui.components.ui.metric import metric_card
from bastion_ui.routes import PUBLIC_ROUTE_SPECS
from bastion_ui.routes.console import console_page
from bastion_ui.routes.console_api_explorer import console_api_explorer_page
from bastion_ui.routes.console_audit import console_audit_page
from bastion_ui.routes.console_evidence import console_evidence_page
from bastion_ui.routes.console_market_intelligence import console_market_intelligence_page
from bastion_ui.routes.console_policy import console_policy_page
from bastion_ui.routes.console_provider_health import console_provider_health_page
from bastion_ui.routes.console_sovereign_grid import console_sovereign_grid_page
from bastion_ui.routes.console_time_machine import console_time_machine_page
from bastion_ui.routes.console_trace import console_trace_page
from bastion_ui.routes.home import home_page as index  # noqa: F401
from bastion_ui.routes.market import market_page
from bastion_ui.routes.market_evidence import market_evidence_page
from bastion_ui.routes.market_narratives import market_narratives_page
from bastion_ui.routes.market_signals import market_signals_page
from bastion_ui.routes.market_sources import market_sources_page
from bastion_ui.routes.market_time_machine import market_time_machine_page
from bastion_ui.routes.market_timeline import market_timeline_page
from bastion_ui.routes.proof_packet import trace_proof_packet_page
from bastion_ui.routes.trace_report import trace_report_page


def design_system_preview() -> rx.Component:
    """Render a development-only design-system preview."""

    return public_layout(
        rx.vstack(
            rx.badge("Development preview only", color_scheme="orange"),
            rx.heading("Design System Foundation", size="7"),
            rx.text("Reusable UI primitives for later public, Trace, Market, and Console pages."),
            trace_safety_banner(),
            header(),
            footer(),
            mobile_nav(),
            console_sidebar(),
            command_palette(),
            responsive_grid(
                card(
                    button("Primary action"),
                    button("Secondary action", "secondary"),
                    button("Ghost action", "ghost"),
                    title="Buttons",
                ),
                card(
                    badge("Advisory", "info"),
                    badge("Manual review recommended", "warning"),
                    badge("Elevated risk band", "risk_medium"),
                    title="Badges",
                ),
                card(
                    alert("This view may be incomplete.", "advisory"),
                    degraded_state(),
                    stale_data_banner(),
                    title="Alerts and feedback",
                ),
                card(
                    metric_card("Provider state", "Degraded", state="warning"),
                    loading_state(),
                    title="Metrics and loading",
                ),
                card(advisory_notice(), no_custody_notice(), title="Safety notices"),
            ),
            align="start",
            spacing="5",
            width="100%",
        )
    )


app = rx.App(
    theme=rx.theme(
        appearance="dark",
        accent_color="orange",
        radius="large",
    )
)

for route_spec in PUBLIC_ROUTE_SPECS:
    app.add_page(route_spec.page, route=route_spec.route, title=route_spec.title)

app.add_page(console_page, route="/console", title="Bastion Console")
app.add_page(console_trace_page, route="/console/trace", title="Trace Console")
app.add_page(console_evidence_page, route="/console/evidence", title="Evidence Console")
app.add_page(
    console_provider_health_page,
    route="/console/provider-health",
    title="Provider Health Console",
)
app.add_page(console_policy_page, route="/console/policy", title="Policy Engine Console")
app.add_page(console_audit_page, route="/console/audit", title="Audit Log Console")
app.add_page(
    console_market_intelligence_page,
    route="/console/market-intelligence",
    title="Market Intelligence",
)
app.add_page(console_time_machine_page, route="/console/time-machine", title="Console Time Machine")
app.add_page(
    console_sovereign_grid_page,
    route="/console/sovereign-grid",
    title="Sovereign Grid",
)
app.add_page(
    console_api_explorer_page,
    route="/console/api-explorer",
    title="API Explorer",
)
app.add_page(market_page, route="/market", title="Market Intelligence")
app.add_page(market_time_machine_page, route="/market/time-machine", title="Market Time Machine")
app.add_page(market_timeline_page, route="/market/timeline", title="Market Timeline")
app.add_page(market_signals_page, route="/market/signals", title="Market Signals")
app.add_page(market_evidence_page, route="/market/evidence", title="Market Evidence")
app.add_page(market_narratives_page, route="/market/narratives", title="Market Narratives")
app.add_page(market_sources_page, route="/market/sources", title="Market Sources")
app.add_page(trace_report_page, route="/trace/[report_id]", title="Trace Report")
app.add_page(
    trace_proof_packet_page,
    route="/trace/[report_id]/proof-packet",
    title="Trace Proof Packet",
)
app.add_page(design_system_preview, route="/design-system", title="Design System Preview")

__all__ = ["app", "design_system_preview", "index"]
