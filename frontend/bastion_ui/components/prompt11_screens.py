# mypy: disable-error-code="attr-defined,union-attr,arg-type,no-any-return"
from __future__ import annotations

from typing import cast

import reflex as rx

from bastion_ui.components.ui.card import card
from bastion_ui.state.prompt11_state import MarketSimilarityState
from bastion_ui.theme.styles import FOCUS_RING
from bastion_ui.topology import dynamic_route_parts

REPLAY_ROUTE_PREFIX, REPLAY_ROUTE_SUFFIX = dynamic_route_parts("market.replay", "event_id")


def _match(item: rx.Var[object]) -> rx.Component:
    return cast(
        rx.Component,
        rx.el.li(
            rx.heading(
                "Rank ",
                item.rank,
                ": ",
                item.candidate_title,
                size="4",
                class_name="similarity-title",
            ),
            rx.text("Historical time: ", item.candidate_occurred_at, class_name="similarity-time"),
            rx.text("Similarity ratio: ", item.score_ratio, class_name="similarity-score"),
            rx.text(
                "Meaning: ",
                item.score_meaning,
                class_name="similarity-meaning",
                overflow_wrap="anywhere",
                max_width="100%",
            ),
            rx.el.ul(
                rx.foreach(
                    item.dimensions,
                    lambda dimension: rx.el.li(
                        dimension.name, ": ", dimension.score_ratio
                    ),
                ),
                aria_label="Backend comparison dimensions",
            ),
            rx.el.ul(
                rx.foreach(item.limitations, lambda limitation: rx.el.li(limitation)),
                aria_label="Similarity limitations",
            ),
            rx.link(
                rx.button("Open historical replay", style=FOCUS_RING),
                href=REPLAY_ROUTE_PREFIX + item.replay_event_id.to_string() + REPLAY_ROUTE_SUFFIX,
                aria_label="Open canonical historical replay",
            ),
            padding="12px 0",
            border_bottom="1px solid var(--gray-a5)",
        ),
    )


def similarity_screen() -> rx.Component:
    return rx.vstack(
        rx.callout(
            "Retrospective comparison only. Similarity does not predict future outcomes.",
            role="note",
        ),
        rx.cond(
            MarketSimilarityState.report != None,  # noqa: E711
            card(
                rx.heading("Method", size="4"),
                rx.text(MarketSimilarityState.report.method),
                rx.text("Version: ", MarketSimilarityState.report.method_version),
                rx.text("Interpretation: ", MarketSimilarityState.report.interpretation),
                rx.heading("Data support", size="4"),
                rx.text("Sufficiency: ", MarketSimilarityState.report.sufficiency),
                rx.text("Sample count: ", MarketSimilarityState.report.sample_count),
                rx.text(
                    "Comparison dimensions covered: ",
                    MarketSimilarityState.report.coverage_dimension_count,
                ),
                rx.text("Confidence: not provided as probability"),
                rx.cond(
                    MarketSimilarityState.report.interval != None,  # noqa: E711
                    rx.el.section(
                        rx.heading("Empirical similarity-score interval", size="4"),
                        rx.text(
                            "Subject: ",
                            MarketSimilarityState.report.interval.subject,
                        ),
                        rx.text(
                            "Bounds: ",
                            MarketSimilarityState.report.interval.lower,
                            " to ",
                            MarketSimilarityState.report.interval.upper,
                            " ",
                            MarketSimilarityState.report.interval.unit,
                            class_name="similarity-interval-text",
                        ),
                        rx.text(
                            "Type: ",
                            MarketSimilarityState.report.interval.interval_type,
                            "; empirical quantiles ",
                            MarketSimilarityState.report.interval.lower_quantile,
                            "–",
                            MarketSimilarityState.report.interval.upper_quantile,
                        ),
                        rx.text(
                            "Method: ",
                            MarketSimilarityState.report.interval.method_id,
                            " / ",
                            MarketSimilarityState.report.interval.method_version,
                        ),
                        rx.el.svg(
                            rx.el.line(
                                x1=MarketSimilarityState.report.interval.lower.to_string(),
                                x2=MarketSimilarityState.report.interval.upper.to_string(),
                                y1="0.5",
                                y2="0.5",
                                stroke="var(--accent-9)",
                                stroke_width="0.28",
                                stroke_linecap="butt",
                            ),
                            rx.el.line(
                                x1=MarketSimilarityState.report.interval.lower.to_string(),
                                x2=MarketSimilarityState.report.interval.upper.to_string(),
                                y1="0.5",
                                y2="0.5",
                                stroke="var(--gray-12)",
                                stroke_width="0.12",
                                stroke_dasharray="0.025 0.025",
                            ),
                            view_box="0 0 1 1",
                            role="img",
                            aria_label="Empirical similarity score interval ribbon",
                            class_name="similarity-interval-ribbon",
                            width="100%",
                            height="52px",
                            preserve_aspect_ratio="none",
                        ),
                        rx.el.ul(
                            rx.foreach(
                                MarketSimilarityState.report.interval.limitations,
                                lambda limitation: rx.el.li(limitation),
                            ),
                            aria_label="Statistical interval limitations",
                        ),
                        aria_label="Backend empirical uncertainty interval",
                    ),
                    rx.callout(
                        "Empirical interval unavailable: at least five eligible "
                        "contexts are required.",
                        role="status",
                    ),
                ),
                rx.el.ol(
                    rx.foreach(MarketSimilarityState.report.results, _match),
                    aria_label="Ranked historical similarity matches",
                ),
                rx.el.details(
                    rx.el.summary("View accessible analytical data"),
                    rx.el.div(
                        rx.el.table(
                            rx.el.thead(
                                rx.el.tr(
                                    rx.el.th("Rank"),
                                    rx.el.th("Historical context"),
                                    rx.el.th("Similarity ratio"),
                                    rx.el.th("Historical time"),
                                    rx.el.th("Interval lower"),
                                    rx.el.th("Interval upper"),
                                    rx.el.th("Interval type"),
                                )
                            ),
                            rx.el.tbody(
                                rx.foreach(
                                    MarketSimilarityState.report.results,
                                    lambda item: rx.el.tr(
                                        rx.el.td(item.rank),
                                        rx.el.td(item.candidate_title),
                                        rx.el.td(item.score_ratio),
                                        rx.el.td(item.candidate_occurred_at),
                                        rx.el.td(MarketSimilarityState.report.interval.lower),
                                        rx.el.td(MarketSimilarityState.report.interval.upper),
                                        rx.el.td(
                                            MarketSimilarityState.report.interval.interval_type
                                        ),
                                    ),
                                )
                            ),
                            aria_label="Similarity analytical data table",
                        ),
                        width="100%",
                        max_width="100%",
                        overflow_x="auto",
                    ),
                ),
                title="Historical similarity analysis",
                variant="matte",
            ),
            rx.callout("Similarity results are not loaded or unavailable.", role="status"),
        ),
        rx.button("Load similarity", on_click=MarketSimilarityState.load(1), style=FOCUS_RING),
        width="100%",
        align="start",
    )
