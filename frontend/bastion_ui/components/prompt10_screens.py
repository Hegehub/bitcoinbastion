# mypy: disable-error-code="attr-defined,union-attr,arg-type,no-any-return,call-arg"
from __future__ import annotations

from typing import cast

import reflex as rx

from bastion_ui.components.data.provenance_badge import provenance_badge
from bastion_ui.components.ui.card import card
from bastion_ui.state.prompt10_state import MarketHistoryState
from bastion_ui.theme.styles import FOCUS_RING


def _limitations(values: rx.Var[object]) -> rx.Component:
    return rx.el.ul(rx.foreach(values, lambda item: rx.el.li(item)), aria_label="Limitations")


def _evidence(values: rx.Var[object]) -> rx.Component:
    return rx.el.ul(
        rx.foreach(
            values,
            lambda item: rx.el.li(
                rx.text(item.label),
                rx.text("Relationship: ", item.relation),
                rx.text("Evidence status: ", item.verification_status),
            ),
        ),
        aria_label="Related Evidence references",
    )


def _timeline_row(item: rx.Var[object]) -> rx.Component:
    return cast(
        rx.Component,
        rx.el.li(
            rx.heading(item.title, size="4"),
            rx.text("Event type: ", item.kind, " (", item.producer_type, ")"),
            rx.text("Occurred: ", item.occurred_at),
            rx.text("Observed: ", item.observed_at),
            rx.text("Source: ", item.source_name, " — ", item.source_type),
            rx.text(item.summary),
            _evidence(item.evidence_links),
            _limitations(item.limitations),
            rx.button(
                "Open historical replay",
                on_click=MarketHistoryState.load_replay(item.event_id),
                style=FOCUS_RING,
                aria_label="Open historical replay for event",
            ),
            class_name="market-timeline-item",
            padding="12px 0",
            border_bottom="1px solid var(--gray-a5)",
        ),
    )


def timeline_screen() -> rx.Component:
    return rx.vstack(
        rx.callout(
            "Historical chronology. Ordering is backend-owned; proximity does not imply causality.",
            role="note",
        ),
        provenance_badge(
            MarketHistoryState.provenance,
            source="Historical Market store",
            details="Historical domain context is separate from Feature-52 transport provenance.",
        ),
        rx.cond(
            MarketHistoryState.timeline_items.length() > 0,
            card(
                rx.el.ol(
                    rx.foreach(MarketHistoryState.timeline_items, _timeline_row),
                    aria_label="Authoritative Market timeline",
                ),
                rx.text("Ordering: ", MarketHistoryState.timeline_ordering),
                title="Market timeline",
                variant="matte",
            ),
            rx.callout("No historical events returned.", role="status"),
        ),
        rx.button("Refresh timeline", on_click=MarketHistoryState.load_timeline, style=FOCUS_RING),
        width="100%",
        align="start",
    )


def replay_screen() -> rx.Component:
    return rx.cond(
        MarketHistoryState.replay != None,  # noqa: E711
        card(
            rx.callout("Historical replay — not current Market state.", role="status"),
            provenance_badge(
                MarketHistoryState.provenance,
                source="Content-addressed historical capture",
                details=(
                    "LIVE request transport; historical content. "
                    "Digest is not Evidence verification."
                ),
            ),
            rx.text("Capture: ", MarketHistoryState.replay.capture_id, id="replay-capture-id"),
            rx.text("Schema: ", MarketHistoryState.replay.schema_version),
            rx.text("Effective time: ", MarketHistoryState.replay.effective_at),
            rx.text("Captured: ", MarketHistoryState.replay.captured_at),
            rx.text("Historical event: ", MarketHistoryState.replay.event.title),
            rx.text(
                "Integrity: ",
                MarketHistoryState.replay.digest_algorithm,
                " ",
                MarketHistoryState.replay.content_digest,
            ),
            rx.text("Integrity meaning: ", MarketHistoryState.replay.integrity_meaning),
            _limitations(MarketHistoryState.replay.limitations),
            title="Historical replay capture",
            variant="matte",
        ),
        rx.callout("Select an event from Timeline to load a historical replay.", role="status"),
    )


def _attribution(item: rx.Var[object]) -> rx.Component:
    return cast(
        rx.Component,
        rx.el.li(
            rx.heading("Candle ", item.subject_candle_id, size="4"),
            rx.text("Backend relationship: ", item.relation),
            rx.text("Backend confidence ratio: ", item.confidence_ratio),
            rx.text(item.explanation),
            _limitations(item.limitations),
            _evidence(item.evidence_links),
            padding="12px 0",
            border_bottom="1px solid var(--gray-a5)",
        ),
    )


def attribution_screen() -> rx.Component:
    return card(
        rx.el.ul(
            rx.foreach(MarketHistoryState.attributions, _attribution),
            aria_label="Backend Market attribution relationships",
        ),
        title="Attribution relationships",
        variant="matte",
    )


def _narrative(item: rx.Var[object]) -> rx.Component:
    return cast(
        rx.Component,
        rx.el.li(
            rx.heading(item.title, size="4"),
            rx.text(item.body_plain_text),
            rx.text("Origin: ", item.origin),
            rx.text("Generated: ", item.generated_at),
            rx.text("Backend confidence ratio: ", item.confidence_ratio),
            _limitations(item.limitations),
            padding="12px 0",
        ),
    )


def narratives_screen() -> rx.Component:
    return card(
        rx.el.ul(
            rx.foreach(MarketHistoryState.narratives, _narrative),
            aria_label="Backend stored Market narratives",
        ),
        title="Market narratives",
        variant="matte",
    )


def _source(item: rx.Var[object]) -> rx.Component:
    return cast(
        rx.Component,
        rx.el.li(
            rx.heading(item.display_name, size="4"),
            rx.text("Source ID: ", item.source_id),
            rx.text("Type: ", item.source_type),
            rx.text("Category: ", item.category),
            rx.cond(
                item.homepage_url != None,  # noqa: E711
                rx.el.a(
                    "Open source homepage",
                    href=item.homepage_url.to_string(),
                    target="_blank",
                    rel="noopener noreferrer",
                ),
                rx.text("No browser-safe external URL."),
            ),
            rx.text("Observed: ", item.observed_at),
            _limitations(item.limitations),
            padding="12px 0",
        ),
    )


def sources_screen() -> rx.Component:
    return card(
        rx.el.ul(
            rx.foreach(MarketHistoryState.sources, _source),
            aria_label="Browser-safe Market sources",
        ),
        title="Market sources",
        variant="matte",
    )
