from __future__ import annotations

from typing import Any

import reflex as rx

from bastion_ui.domain.prompt13 import (
    TraceClaimViewModel,
    TraceDisagreementViewModel,
    TraceHistoryIndexItemViewModel,
    TraceTopologyNodeViewModel,
    TraceTopologyRelationshipViewModel,
)
from bastion_ui.state.trace_topology_state import TraceHistoryState, TraceTopologyState


def _node(node: TraceTopologyNodeViewModel, select: Any) -> rx.Component:
    return rx.button(
        rx.vstack(
            rx.text(node.label, weight="bold"),
            rx.text(node.kind, size="1"),
            rx.code(node.id, size="1", white_space="normal", word_break="break-all"),
            align="start",
        ),
        on_click=select(node),
        aria_label="Inspect topology node " + node.label,
        variant="surface",
        width="100%",
    )


def _relationship(edge: TraceTopologyRelationshipViewModel, select: Any) -> rx.Component:
    return rx.button(
        rx.vstack(
            rx.text(edge.relationship_type, weight="bold"),
            rx.text(
                edge.source_id + " → " + edge.target_id,
                size="1",
                overflow_wrap="anywhere",
            ),
            rx.text("Direction: " + edge.direction, size="1"),
            rx.code(edge.id, size="1", white_space="normal", word_break="break-all"),
            align="start",
        ),
        on_click=select(edge),
        aria_label="Inspect directed relationship " + edge.relationship_type,
        variant="surface",
        width="100%",
    )


def _claim(claim: TraceClaimViewModel) -> rx.Component:
    return rx.card(
        rx.vstack(
            rx.text(claim.value_label, weight="bold"),
            rx.text("Producer: " + claim.producer),
            rx.text("Source: " + claim.source),
            rx.text("Predicate: " + claim.predicate),
            rx.text("Confidence: " + claim.confidence),
            rx.cond(
                claim.limitations.length() > 0,
                rx.text("Limitations: ", claim.limitations.join("; ")),
            ),
            align="start",
        ),
        width="100%",
    )


def _evaluation(item: TraceDisagreementViewModel) -> rx.Component:
    return rx.card(
        rx.vstack(
            rx.heading(item.status.replace("_", " "), size="4"),
            rx.text("Analytical question: " + item.predicate),
            rx.text("Subject identity: " + item.subject_id),
            rx.text("Resolution: " + item.resolution_status),
            rx.text("Eligible independent Claims: ", item.eligible_claim_count),
            rx.cond(
                item.claims.length() > 0,
                rx.vstack(rx.foreach(item.claims, _claim), width="100%"),
                rx.text("No comparable Claim alternatives were available."),
            ),
            rx.cond(
                item.limitations.length() > 0, rx.text("Limitations: ", item.limitations.join("; "))
            ),
            align="start",
            width="100%",
        ),
        role="status",
        width="100%",
    )


def _history_item(item: TraceHistoryIndexItemViewModel) -> rx.Component:
    return rx.link(
        rx.card(
            rx.vstack(
                rx.text(item.captured_at, weight="bold"),
                rx.code(
                    item.snapshot_id,
                    size="1",
                    white_space="normal",
                    word_break="break-all",
                ),
                rx.text(
                    "Topology: " + item.topology_snapshot_id,
                    size="1",
                    overflow_wrap="anywhere",
                ),
                align="start",
            ),
            width="100%",
        ),
        href="/trace/" + TraceTopologyState.current_report_id + "/history/" + item.snapshot_id,
        aria_label="Open exact historical Trace snapshot " + item.snapshot_id,
        width="100%",
        max_width="100%",
        overflow="hidden",
    )


def current_trace_topology() -> rx.Component:
    return rx.vstack(
        rx.heading("Authoritative topology", size="6"),
        rx.text(
            "The visual layout is presentation-only. Nodes, directed relationships, and status "
            "come from the persisted backend Graph.",
        ),
        rx.cond(
            TraceTopologyState.lifecycle == "loading", rx.text("Loading topology…", role="status")
        ),
        rx.cond(
            TraceTopologyState.safe_error != "",
            rx.callout(TraceTopologyState.safe_error, color_scheme="red"),
        ),
        rx.cond(
            TraceTopologyState.topology != None,  # noqa: E711
            rx.vstack(
                rx.text(
                    "Topology contains ",
                    TraceTopologyState.topology.nodes.length(),
                    " nodes and ",
                    TraceTopologyState.topology.relationships.length(),
                    " directed relationships.",
                    role="status",
                ),
                rx.cond(
                    TraceTopologyState.topology.metadata.limitations.length() > 0,
                    rx.callout(
                        "Limitations: "
                        + TraceTopologyState.topology.metadata.limitations.join("; "),
                        color_scheme="amber",
                    ),
                ),
                rx.box(
                    rx.heading("Topology graph", size="4"),
                    rx.grid(
                        rx.foreach(
                            TraceTopologyState.topology.nodes,
                            lambda node: _node(node, TraceTopologyState.select_node),
                        ),
                        columns=rx.breakpoints(initial="1", md="2", lg="3"),
                        gap="3",
                    ),
                    aria_label="Visual Trace topology graph",
                    width="100%",
                ),
                rx.heading("Directed relationships", size="4"),
                rx.vstack(
                    rx.foreach(
                        TraceTopologyState.topology.relationships,
                        lambda edge: _relationship(edge, TraceTopologyState.select_relationship),
                    ),
                    width="100%",
                ),
                _current_inspector(),
                width="100%",
            ),
        ),
        rx.heading("Immutable history", size="5"),
        rx.text(
            "Select a persistent snapshot identity. Snapshot payloads are loaded only on selection."
        ),
        rx.vstack(rx.foreach(TraceTopologyState.history, _history_item), width="100%"),
        rx.heading("Analytical agreement and disagreement", size="5"),
        rx.cond(
            TraceTopologyState.disagreement != None,  # noqa: E711
            rx.vstack(
                rx.foreach(TraceTopologyState.disagreement.evaluations, _evaluation), width="100%"
            ),
            rx.text("Disagreement data unavailable."),
        ),
        width="100%",
        align="start",
        spacing="4",
        max_width="100%",
        overflow="hidden",
    )


def _current_inspector() -> rx.Component:
    return rx.vstack(
        rx.cond(
            TraceTopologyState.selected_node != None,  # noqa: E711
            rx.card(
                rx.heading("Node inspector", size="4"),
                rx.text("ID: " + TraceTopologyState.selected_node.id),
                rx.text("Type: " + TraceTopologyState.selected_node.kind),
                rx.text("Producer: " + TraceTopologyState.selected_node.producer),
                width="100%",
            ),
        ),
        rx.cond(
            TraceTopologyState.selected_relationship != None,  # noqa: E711
            rx.card(
                rx.heading("Relationship inspector", size="4"),
                rx.text("ID: " + TraceTopologyState.selected_relationship.id),
                rx.text("Source: " + TraceTopologyState.selected_relationship.source_id),
                rx.text("Target: " + TraceTopologyState.selected_relationship.target_id),
                rx.text("Relation: " + TraceTopologyState.selected_relationship.relationship_type),
                rx.text("Direction: " + TraceTopologyState.selected_relationship.direction),
                width="100%",
            ),
        ),
        width="100%",
    )


def historical_trace_topology() -> rx.Component:
    return rx.vstack(
        rx.callout(
            rx.vstack(
                rx.text("Historical Trace", weight="bold"),
                rx.code(TraceHistoryState.selected_snapshot_id),
                rx.text(
                    "This mode uses an exact persisted Graph Snapshot; it is not reconstructed."
                ),
                align="start",
            ),
            color_scheme="blue",
            width="100%",
        ),
        rx.link(
            "Return to current topology", href="/trace/" + TraceHistoryState.historical_report_id
        ),
        rx.cond(
            TraceHistoryState.lifecycle == "loading",
            rx.text("Loading exact snapshot…", role="status"),
        ),
        rx.cond(
            TraceHistoryState.safe_error != "",
            rx.callout(TraceHistoryState.safe_error, color_scheme="red"),
        ),
        rx.cond(
            TraceHistoryState.topology != None,  # noqa: E711
            rx.vstack(
                rx.text(
                    "Historical topology contains ",
                    TraceHistoryState.topology.nodes.length(),
                    " nodes and ",
                    TraceHistoryState.topology.relationships.length(),
                    " relationships.",
                    role="status",
                ),
                rx.grid(
                    rx.foreach(
                        TraceHistoryState.topology.nodes,
                        lambda node: _node(node, TraceHistoryState.select_node),
                    ),
                    columns=rx.breakpoints(initial="1", md="2", lg="3"),
                    gap="3",
                    width="100%",
                ),
                rx.heading("Historical directed relationships", size="4"),
                rx.vstack(
                    rx.foreach(
                        TraceHistoryState.topology.relationships,
                        lambda edge: _relationship(edge, TraceHistoryState.select_relationship),
                    ),
                    width="100%",
                ),
                _historical_inspector(),
                width="100%",
            ),
        ),
        rx.heading("Historically bound analytical status", size="5"),
        rx.cond(
            TraceHistoryState.disagreement != None,  # noqa: E711
            rx.vstack(
                rx.foreach(TraceHistoryState.disagreement.evaluations, _evaluation), width="100%"
            ),
            rx.text("Historical disagreement data unavailable."),
        ),
        width="100%",
        align="start",
        spacing="4",
        max_width="100%",
        overflow="hidden",
    )


def _historical_inspector() -> rx.Component:
    return rx.vstack(
        rx.cond(
            TraceHistoryState.selected_node != None,  # noqa: E711
            rx.card(
                rx.heading("Historical node inspector", size="4"),
                rx.text("ID: " + TraceHistoryState.selected_node.id),
                rx.text("Type: " + TraceHistoryState.selected_node.kind),
                rx.text("Producer: " + TraceHistoryState.selected_node.producer),
                width="100%",
            ),
        ),
        rx.cond(
            TraceHistoryState.selected_relationship != None,  # noqa: E711
            rx.card(
                rx.heading("Historical relationship inspector", size="4"),
                rx.text("ID: " + TraceHistoryState.selected_relationship.id),
                rx.text("Source: " + TraceHistoryState.selected_relationship.source_id),
                rx.text("Target: " + TraceHistoryState.selected_relationship.target_id),
                rx.text("Relation: " + TraceHistoryState.selected_relationship.relationship_type),
                rx.text("Direction: " + TraceHistoryState.selected_relationship.direction),
                width="100%",
            ),
        ),
        width="100%",
    )
