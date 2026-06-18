from __future__ import annotations

from collections.abc import Callable

import reflex as rx

from bastion_ui.components.feedback.degraded_state import degraded_state
from bastion_ui.components.feedback.loading_state import loading_state
from bastion_ui.components.feedback.stale_data_banner import stale_data_banner
from bastion_ui.components.layout.command_palette import command_palette_preview
from bastion_ui.components.layout.console_sidebar import console_sidebar
from bastion_ui.components.layout.footer import public_footer
from bastion_ui.components.layout.grid import responsive_grid
from bastion_ui.components.layout.header import public_header
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
from bastion_ui.routes.check import check_page
from bastion_ui.routes.developers import developers_page
from bastion_ui.routes.docs import docs_page
from bastion_ui.routes.evidence import evidence_page
from bastion_ui.routes.home import home_page
from bastion_ui.routes.manifesto import manifesto_page
from bastion_ui.routes.operations import operations_page
from bastion_ui.routes.platform import platform_page
from bastion_ui.routes.proof_packet import trace_proof_packet_page
from bastion_ui.routes.roadmap import roadmap_page
from bastion_ui.routes.security import security_page
from bastion_ui.routes.status import status_page
from bastion_ui.routes.trace import trace_page
from bastion_ui.routes.trace_report import trace_report_page

PageFactory = Callable[[], rx.Component]

PUBLIC_ROUTE_REGISTRATIONS: tuple[tuple[str, PageFactory, str], ...] = (
    ("/", home_page, "Bitcoin Bastion"),
    ("/platform", platform_page, "Platform"),
    ("/developers", developers_page, "Developers"),
    ("/operations", operations_page, "Operations"),
    ("/manifesto", manifesto_page, "Manifesto"),
    ("/evidence", evidence_page, "Evidence"),
    ("/status", status_page, "Status"),
    ("/roadmap", roadmap_page, "Roadmap"),
    ("/security", security_page, "Security"),
    ("/docs", docs_page, "Docs"),
    ("/check", check_page, "Check Bitcoin Address"),
    ("/trace", trace_page, "Bastion Trace"),
    ("/trace/[report_id]", trace_report_page, "Trace Report"),
    ("/trace/[report_id]/proof-packet", trace_proof_packet_page, "Trace Proof Packet"),
)


def index() -> rx.Component:
    """Backward-compatible root page alias for scaffold tests."""

    return home_page()


def design_system_preview() -> rx.Component:
    """Render a development-only design-system preview."""

    return public_layout(
        rx.vstack(
            rx.badge("Development preview only", color_scheme="orange"),
            rx.heading("Design System Foundation", size="7"),
            rx.text("Reusable UI primitives for later public, Trace, Market, and Console pages."),
            trace_safety_banner(),
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
                card(command_palette_preview(), title="Command palette"),
                card(console_sidebar(), title="Console navigation"),
                card(mobile_nav(), title="Mobile navigation"),
            ),
            align="start",
            spacing="5",
            width="100%",
        ),
        header_slot=public_header(),
        footer_slot=public_footer(),
    )


app = rx.App(
    theme=rx.theme(
        appearance="dark",
        accent_color="orange",
        radius="large",
    )
)

for route, page, title in PUBLIC_ROUTE_REGISTRATIONS:
    app.add_page(page, route=route, title=title)

app.add_page(design_system_preview, route="/design-system", title="Design System Preview")
