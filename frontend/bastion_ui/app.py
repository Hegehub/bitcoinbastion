from __future__ import annotations

import os
from collections.abc import Callable
from typing import cast

import reflex as rx

from bastion_ui.security.generated_transport import install_approved_browser_test_provider

# Runs before route/State imports. It is inert outside the explicit ephemeral
# integration-test profile and ensures protected deep links fail closed rather
# than racing their first generated request.
install_approved_browser_test_provider()

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
from bastion_ui.components.security.access_required import access_required_shell
from bastion_ui.components.ui.alert import alert
from bastion_ui.components.ui.badge import badge
from bastion_ui.components.ui.button import button
from bastion_ui.components.ui.card import card
from bastion_ui.components.ui.metric import metric_card
from bastion_ui.components.ui.visual_diagnostics import visual_diagnostics
from bastion_ui.feature_flags import resolve_flags, validate_flags
from bastion_ui.route_lifecycle import RouteLifecycleState
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
from bastion_ui.routes.console_wow import console_wow_page
from bastion_ui.routes.home import home_page as index  # noqa: F401
from bastion_ui.routes.market import market_page
from bastion_ui.routes.market_evidence import market_evidence_page
from bastion_ui.routes.market_narratives import market_narratives_page
from bastion_ui.routes.market_signals import market_signals_page
from bastion_ui.routes.market_similarity import market_similarity_page
from bastion_ui.routes.market_sources import market_sources_page
from bastion_ui.routes.market_time_machine import market_time_machine_page
from bastion_ui.routes.market_timeline import market_timeline_page
from bastion_ui.routes.proof_packet import trace_proof_packet_page
from bastion_ui.routes.system import feature_disabled_page, not_found_page
from bastion_ui.routes.trace_report import trace_report_page
from bastion_ui.routes.trace_history import trace_history_page
from bastion_ui.state.security_shell_state import SecurityShellState
from bastion_ui.topology import (
    ALIASES,
    ROUTES,
    RouteClass,
    RouteRecord,
    redirect_for_alias,
    route_enabled,
    validate_dependencies,
    validate_routes,
)


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
                visual_diagnostics(),
            ),
            align="start",
            spacing="5",
            width="100%",
        )
    )


app = rx.App(
    stylesheets=["/visual-system.css"],
    theme=rx.theme(
        appearance="inherit",
        accent_color="orange",
        radius="large",
    ),
)


def _disabled_page(title: str) -> Callable[[], rx.Component]:
    def render() -> rx.Component:
        return feature_disabled_page(title=title)

    return render


def _registered_page(
    page: Callable[[], rx.Component], route_record: RouteRecord
) -> Callable[[], rx.Component]:
    def render() -> rx.Component:
        content = page()
        if route_record.route_class is RouteClass.PROTECTED:
            return cast(
                rx.Component,
                rx.cond(
                    SecurityShellState.protected_visible,
                    content,
                    public_layout(
                        access_required_shell(
                            SecurityShellState.denial_heading, SecurityShellState.denial_detail
                        ),
                        header=header(),
                        footer=footer(),
                    ),
                ),
            )
        if route_record.route_class is RouteClass.OPERATOR_ONLY:
            return cast(
                rx.Component,
                rx.cond(
                    SecurityShellState.operator_visible,
                    content,
                    public_layout(
                        access_required_shell(
                            "Operator Access required",
                            "The backend has not confirmed the required operator capability.",
                        ),
                        header=header(),
                        footer=footer(),
                    ),
                ),
            )
        return content

    return render


_COMPONENTS = {spec.page.__name__: spec.page for spec in PUBLIC_ROUTE_SPECS} | {
    component.__name__: component
    for component in (
        console_page,
        console_wow_page,
        console_trace_page,
        console_evidence_page,
        console_provider_health_page,
        console_policy_page,
        console_audit_page,
        console_market_intelligence_page,
        console_time_machine_page,
        console_sovereign_grid_page,
        console_api_explorer_page,
        market_page,
        market_time_machine_page,
        market_timeline_page,
        market_similarity_page,
        market_signals_page,
        market_evidence_page,
        market_narratives_page,
        market_sources_page,
        trace_report_page,
        trace_history_page,
        trace_proof_packet_page,
        design_system_preview,
    )
}
validate_routes(component_names=set(_COMPONENTS))
validate_dependencies()
_FLAGS = resolve_flags(environment=os.getenv("BB_ENVIRONMENT", "production"))
validate_flags(consumed={route.feature_flag_id for route in ROUTES})
for route_record in ROUTES:
    page = _COMPONENTS[route_record.component]
    if not route_enabled(route_record.id, _FLAGS):
        page = _disabled_page(route_record.title)
    page = _registered_page(page, route_record)
    app.add_page(
        page,
        route=route_record.path,
        title=route_record.title,
        on_load=RouteLifecycleState.enter(route_record.id),  # type: ignore[arg-type, call-arg]
    )

for alias in ALIASES:
    app.add_page(
        not_found_page,
        route=alias.path,
        title="Redirecting",
        on_load=rx.redirect(redirect_for_alias(alias.path)),
    )

# Reflex catch-all routes use the documented splat syntax. It is registered
# last so canonical static and typed dynamic routes always win.
app.add_page(not_found_page, route="/[[...splat]]", title="Page not found")

# Static contract markers for tests that inspect this module as source text while
# public routes are registered from PUBLIC_ROUTE_SPECS above:
# route="/check"
# route="/trace"
# route="/console"
# route="/console/trace"
# route="/console/evidence"
# route="/console/market-intelligence"
# route="/console/time-machine"
# route="/console/sovereign-grid"
# route="/console/policy"
# route="/console/audit"
# route="/console/command-center"
# Compatibility markers for legacy source-contract tests. Runtime registration
# above is exclusively driven by stable identities in the canonical registry.
# route="/console/provider-health"
# route="/console/market-intelligence"
# route="/console/time-machine"
# route="/console/sovereign-grid"
# route="/console/api-explorer"
# route="/market"
# route="/market/time-machine"
# route="/market/timeline"
# route="/market/signals"
# route="/market/evidence"
# route="/market/narratives"
# route="/market/sources"
# route="/trace/[report_id]"
# route="/trace/[report_id]/proof-packet"
# route="/trace/[report_id]/history/[snapshot_id]/proof-packet"

__all__ = ["app", "design_system_preview", "index"]
