# mypy: disable-error-code="attr-defined,union-attr,no-any-return,arg-type"
from __future__ import annotations

from typing import cast

import reflex as rx

from bastion_ui.components.data.provenance_badge import provenance_badge
from bastion_ui.components.feedback.loading_state import loading_state
from bastion_ui.components.ui.card import card
from bastion_ui.domain.lifecycle import LifecycleStatus
from bastion_ui.state.prompt9_state import JobsState, MarketOverviewState, MarketSignalsState
from bastion_ui.theme.styles import FOCUS_RING


def _content_state(
    lifecycle: rx.Var[str], error: rx.Var[str], content: rx.Component
) -> rx.Component:
    return cast(
        rx.Component,
        rx.cond(
            lifecycle == LifecycleStatus.LOADING.value,
            loading_state("Loading authoritative data"),
            rx.cond(
                lifecycle == LifecycleStatus.EMPTY.value,
                rx.callout("The authoritative request succeeded with no entries.", role="status"),
                rx.cond(
                    (lifecycle == LifecycleStatus.SUCCESS.value)
                    | (lifecycle == LifecycleStatus.DEGRADED.value),
                    content,
                    rx.callout(rx.text(error), role="alert"),
                ),
            ),
        ),
    )


def _job_row(job: rx.Var[object]) -> rx.Component:
    return cast(
        rx.Component,
        rx.el.li(
            rx.hstack(
                rx.text(job.name, weight="bold", class_name="job-name"),
                rx.badge(job.status, class_name="job-status"),
                justify="between",
                wrap="wrap",
            ),
            rx.text("Started: ", job.started_at),
            rx.text("Finished: ", job.finished_at),
            rx.text("Duration: ", job.duration_ms, " ms"),
            rx.text("Next run: ", job.next_run_at),
            rx.cond(
                job.safe_failure_summary != None,  # noqa: E711
                rx.text("Failure summary: ", job.safe_failure_summary, class_name="job-failure"),
                rx.fragment(),
            ),
            padding="10px 0",
            border_bottom="1px solid var(--gray-a5)",
        ),
    )


def jobs_screen() -> rx.Component:
    content = card(
        rx.el.ul(rx.foreach(JobsState.value.jobs, _job_row), aria_label="Operational jobs"),
        provenance_badge(
            JobsState.value.provenance.state,
            source=JobsState.value.provenance.source_label,
            details="Current backend job-health observation.",
        ),
        title="Background jobs",
        variant="matte",
    )
    return rx.vstack(
        _content_state(JobsState.lifecycle, JobsState.safe_error, content),
        rx.button("Refresh jobs", on_click=JobsState.load, style=FOCUS_RING),
        width="100%",
        align="start",
    )


def market_overview_screen() -> rx.Component:
    content = rx.vstack(
        card(
            rx.text("Reference price", weight="bold"),
            rx.text(
                MarketOverviewState.value.price_usd,
                " USD",
                id="market-price",
                size="7",
            ),
            rx.text(
                MarketOverviewState.value.symbol,
                " / ",
                MarketOverviewState.value.pair,
                id="market-pair",
            ),
            rx.text("Observed: ", MarketOverviewState.value.observed_at, id="market-observed"),
            title="Current market measurement",
            variant="matte",
        ),
        card(
            rx.text("Providers: ", MarketOverviewState.value.provider_count),
            rx.text(
                "Backend confidence: ",
                MarketOverviewState.value.provider_confidence,
                id="market-confidence",
            ),
            rx.text("Source: ", MarketOverviewState.value.source, id="market-source"),
            rx.el.ul(
                rx.foreach(
                    MarketOverviewState.value.limitations,
                    lambda value: rx.el.li(value),
                ),
                aria_label="Market limitations",
            ),
            provenance_badge(
                MarketOverviewState.value.provenance.state,
                source=MarketOverviewState.value.provenance.source_label,
                details="Backend aggregation; no frontend regime or recommendation.",
            ),
            title="Source posture and limitations",
            variant="matte",
        ),
        width="100%",
        spacing="4",
    )
    return rx.vstack(
        _content_state(MarketOverviewState.lifecycle, MarketOverviewState.safe_error, content),
        rx.button("Refresh market", on_click=MarketOverviewState.load, style=FOCUS_RING),
        rx.callout(
            "Analytical information only. No custody, execution, or trading instruction.",
            role="note",
        ),
        width="100%",
        align="start",
    )


def _signal_row(signal: rx.Var[object]) -> rx.Component:
    return cast(
        rx.Component,
        rx.el.li(
            rx.hstack(
                rx.text(signal.title, weight="bold", class_name="signal-title"),
                rx.badge(signal.publication_status, class_name="signal-status"),
                justify="between",
                wrap="wrap",
            ),
            rx.text("Type: ", signal.signal_type, class_name="signal-type"),
            rx.text("Backend severity: ", signal.severity, class_name="signal-severity"),
            rx.text("Backend confidence: ", signal.confidence, class_name="signal-confidence"),
            rx.text("Backend score: ", signal.backend_score, class_name="signal-score"),
            rx.text("Observed: ", signal.observed_at, class_name="signal-observed"),
            rx.text(signal.summary),
            rx.cond(
                signal.stale == True,  # noqa: E712
                rx.callout(rx.text("Stale: ", signal.stale_reason), role="status"),
                rx.fragment(),
            ),
            padding="10px 0",
            border_bottom="1px solid var(--gray-a5)",
        ),
    )


def market_signals_screen() -> rx.Component:
    content = card(
        rx.el.ul(
            rx.foreach(MarketSignalsState.value.signals, _signal_row),
            aria_label="Backend analytical signals",
        ),
        provenance_badge(
            MarketSignalsState.value.provenance.state,
            source=MarketSignalsState.value.provenance.source_label,
            details="Direction is omitted because the contract supplies no direction field.",
        ),
        title="Analytical signals",
        subtitle="Backend semantics are displayed without trading inference.",
        variant="matte",
    )
    return rx.vstack(
        _content_state(MarketSignalsState.lifecycle, MarketSignalsState.safe_error, content),
        rx.button("Refresh signals", on_click=MarketSignalsState.load, style=FOCUS_RING),
        width="100%",
        align="start",
    )
