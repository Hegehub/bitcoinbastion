# mypy: disable-error-code="union-attr,attr-defined,unused-ignore"

from __future__ import annotations

from typing import cast

import reflex as rx

from bastion_ui.components.data.provenance_badge import provenance_badge
from bastion_ui.components.feedback.loading_state import loading_state
from bastion_ui.components.layout.grid import responsive_grid
from bastion_ui.components.ui.card import card
from bastion_ui.domain.lifecycle import LifecycleStatus
from bastion_ui.state.operations_state import (
    HealthState,
    IncidentsState,
    OperationsSLOState,
    ProvidersState,
    StorageState,
)
from bastion_ui.theme.styles import FOCUS_RING
from bastion_ui.topology import path_for


def _section_state(
    lifecycle: str | rx.Var[str], error: str | rx.Var[str], content: rx.Component
) -> rx.Component:
    return cast(
        rx.Component,
        rx.cond(
            lifecycle == LifecycleStatus.LOADING.value,
            loading_state("Loading authoritative operational data"),
            rx.cond(
                lifecycle == LifecycleStatus.EMPTY.value,
                rx.callout("The authoritative request succeeded with no entries.", role="status"),
                rx.cond(
                    (lifecycle == LifecycleStatus.SUCCESS.value)
                    | (lifecycle == LifecycleStatus.DEGRADED.value),
                    content,
                    rx.callout(
                        rx.vstack(
                            rx.text("Operational data unavailable", weight="bold"),
                            rx.text(error),
                            align="start",
                        ),
                        role="alert",
                    ),
                ),
            ),
        ),
    )


def health_section(*, compact: bool = False) -> rx.Component:
    details = rx.foreach(
        HealthState.value.details,
        lambda item: rx.hstack(rx.text(item[0], weight="bold"), rx.text(item[1])),
    )
    content = card(
        rx.text("Application", HealthState.value.application, id="health-application"),
        rx.text("Status", HealthState.value.status, id="health-status", role="status"),
        details,
        provenance_badge(
            HealthState.value.provenance.state,
            source=HealthState.value.provenance.source_label,
            details="Current HTTP runtime observation.",
        ),
        title="Health",
        variant="matte",
    )
    return card(
        _section_state(HealthState.lifecycle, HealthState.safe_error, content),
        rx.link("Open Health details", href=path_for("operations.health"), style=FOCUS_RING)
        if compact
        else rx.button("Refresh Health", on_click=HealthState.load, style=FOCUS_RING),
        title="System health",
        variant="matte",
    )


def _provider_row(provider: rx.Var[object]) -> rx.Component:
    return cast(
        rx.Component,
        rx.el.li(
            rx.hstack(
                rx.text(provider.name, weight="bold"),  # type: ignore[attr-defined]
                rx.badge(provider.state),  # type: ignore[attr-defined]
                justify="between",
            ),
            rx.text("Type: ", provider.provider_type),  # type: ignore[attr-defined]
            rx.text("Latency: ", provider.latency_ms, " ms"),  # type: ignore[attr-defined]
            rx.text("Last success: ", provider.last_success_at),  # type: ignore[attr-defined]
            padding="10px 0",
        ),
    )


def providers_section(*, compact: bool = False) -> rx.Component:
    content = card(
        rx.el.ul(rx.foreach(ProvidersState.value.providers, _provider_row), aria_label="Providers"),
        provenance_badge(
            ProvidersState.value.provenance.state,
            source=ProvidersState.value.provenance.source_label,
            details="Provider health and provenance are separate semantics.",
        ),
        title="Providers",
        variant="matte",
    )
    return card(
        _section_state(ProvidersState.lifecycle, ProvidersState.safe_error, content),
        rx.link("Open Providers", href=path_for("operations.providers"), style=FOCUS_RING)
        if compact
        else rx.button("Refresh Providers", on_click=ProvidersState.load, style=FOCUS_RING),
        title="Provider availability",
        variant="matte",
    )


def _storage_row(store: rx.Var[object]) -> rx.Component:
    return cast(
        rx.Component,
        rx.el.li(
            rx.hstack(
                rx.text(store.name, weight="bold"),  # type: ignore[attr-defined]
                rx.badge(store.status),  # type: ignore[attr-defined]
                justify="between",
            ),
            rx.text("Role: ", store.role),  # type: ignore[attr-defined]
            rx.text(store.purpose),  # type: ignore[attr-defined]
            rx.text("Latency: ", store.latency_ms, " ms"),  # type: ignore[attr-defined]
            padding="10px 0",
        ),
    )


def storage_section(*, compact: bool = False) -> rx.Component:
    content = card(
        rx.text("Profile", StorageState.value.profile, id="storage-profile"),
        rx.text("Status", StorageState.value.status, id="storage-status", role="status"),
        rx.text("Critical failures", StorageState.value.critical_failures),
        rx.text("Warnings", StorageState.value.warnings),
        rx.el.ul(rx.foreach(StorageState.value.stores, _storage_row), aria_label="Storage systems"),
        provenance_badge(
            StorageState.value.provenance.state,
            source=StorageState.value.provenance.source_label,
            details="Sanitized status excludes backend driver details and connection metadata.",
        ),
        title="Storage",
        variant="matte",
    )
    return card(
        _section_state(StorageState.lifecycle, StorageState.safe_error, content),
        rx.link("Open Storage", href=path_for("operations.storage"), style=FOCUS_RING)
        if compact
        else rx.button("Refresh Storage", on_click=StorageState.load, style=FOCUS_RING),
        title="Storage posture",
        variant="matte",
    )


def overview_cockpit() -> rx.Component:
    return cast(
        rx.Component,
        rx.vstack(
            health_section(compact=True),
            responsive_grid(providers_section(compact=True), storage_section(compact=True)),
            card(
                rx.heading("Domain entry points", size="4", as_="h2"),
                rx.hstack(
                    *[
                        rx.link(label, href=path_for(route_id), style=FOCUS_RING)
                        for label, route_id in (
                            ("Operations", "operations"),
                            ("Market", "market.home"),
                            ("Trace", "trace"),
                            ("Evidence", "evidence"),
                            ("Access", "access"),
                        )
                    ],
                    wrap="wrap",
                ),
                variant="matte",
            ),
            width="100%",
            spacing="4",
        ),
    )


def _incident_row(item: rx.Var[object]) -> rx.Component:
    return cast(
        rx.Component,
        rx.el.li(
            rx.hstack(
                rx.text(item.summary, weight="bold"),
                rx.badge(item.severity),
                rx.badge(item.status),
                justify="between",
            ),  # type: ignore[attr-defined]
            rx.text("Affected: ", item.target),
            rx.text("Opened: ", item.opened_at),  # type: ignore[attr-defined]
            rx.text("Updated: ", item.updated_at),
            rx.text("Source: ", item.source),  # type: ignore[attr-defined]
            role="listitem",
            padding="10px 0",
        ),
    )


def incidents_section() -> rx.Component:
    content = card(
        rx.el.ul(
            rx.foreach(IncidentsState.value.incidents, _incident_row),
            aria_label="Operations incidents",
        ),
        provenance_badge(
            IncidentsState.value.provenance.state,
            source=IncidentsState.value.provenance.source_label,
            details="Detector-owned durable incident lifecycle.",
        ),
        title="Incident timeline",
        variant="matte",
    )
    return card(
        _section_state(IncidentsState.lifecycle, IncidentsState.safe_error, content),
        rx.button("Refresh incidents", on_click=IncidentsState.load, style=FOCUS_RING),
        title="Incidents",
        variant="matte",
    )


def _slo_row(item: rx.Var[object]) -> rx.Component:
    return cast(
        rx.Component,
        rx.el.li(
            rx.hstack(rx.text(item.title, weight="bold"), rx.badge(item.status), justify="between"),  # type: ignore[attr-defined]
            rx.text("Target: ", item.comparison, " ", item.target, " ", item.unit),  # type: ignore[attr-defined]
            rx.text("Current: ", item.current, " ", item.unit),  # type: ignore[attr-defined]
            rx.text("Window: ", item.window_seconds, " seconds"),  # type: ignore[attr-defined]
            rx.text("Samples: ", item.sample_count),
            rx.text("Observed: ", item.observed_at),  # type: ignore[attr-defined]
            role="listitem",
            padding="10px 0",
        ),
    )


def slo_section() -> rx.Component:
    content = card(
        rx.el.ul(
            rx.foreach(OperationsSLOState.value.objectives, _slo_row),
            aria_label="Operations service level objectives",
        ),
        provenance_badge(
            OperationsSLOState.value.provenance.state,
            source=OperationsSLOState.value.provenance.source_label,
            details="Compliance is calculated only by the backend evaluator.",
        ),
        title="Current objectives",
        variant="matte",
    )
    return card(
        _section_state(OperationsSLOState.lifecycle, OperationsSLOState.safe_error, content),
        rx.button("Refresh SLO", on_click=OperationsSLOState.load, style=FOCUS_RING),
        title="Service-level posture",
        variant="matte",
    )
