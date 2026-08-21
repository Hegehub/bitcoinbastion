from __future__ import annotations

import reflex as rx

from bastion_ui.domain.prompt15 import (
    EvidenceLineageEdgeViewModel,
    EvidenceLineageNodeViewModel,
)
from bastion_ui.state.trace_evidence_workflow_state import TraceEvidenceWorkflowState


def _node(node: EvidenceLineageNodeViewModel) -> rx.Component:
    return rx.el.li(
        rx.vstack(
            rx.text(node.kind.replace("_", " "), weight="bold"),
            rx.text(node.label),
            rx.code(node.id, color="var(--gray-12)", white_space="normal", word_break="break-all"),
            rx.text("Producer: " + node.producer),
            align="start",
        )
    )


def _edge(edge: EvidenceLineageEdgeViewModel) -> rx.Component:
    return rx.el.li(
        rx.vstack(
            rx.text(edge.relation.replace("_", " "), weight="bold"),
            rx.text(edge.source_id + " → " + edge.target_id, overflow_wrap="anywhere"),
            rx.text("Direction: " + edge.direction),
            align="start",
        )
    )


def evidence_workflow_panel() -> rx.Component:
    return rx.vstack(
        rx.heading("Evidence lineage and reproducibility", size="5"),
        rx.text(
            "Lineage describes explicit provenance and support links. It is not Bitcoin "
            "transaction topology and does not establish causality."
        ),
        rx.hstack(
            rx.button("Load lineage", on_click=TraceEvidenceWorkflowState.load_lineage),
            rx.button("Run deterministic replay", on_click=TraceEvidenceWorkflowState.run_replay),
            rx.button(
                "Verify Evidence identity integrity",
                on_click=TraceEvidenceWorkflowState.run_verification,
            ),
            rx.button("Export safe JSON", on_click=TraceEvidenceWorkflowState.export_evidence),
            wrap="wrap",
        ),
        rx.hstack(
            rx.button(
                "Copy full safe Evidence ID",
                on_click=[
                    rx.set_clipboard(TraceEvidenceWorkflowState.workflow_evidence_id),
                    TraceEvidenceWorkflowState.mark_copied,
                ],
            ),
            rx.text(TraceEvidenceWorkflowState.copy_status, role="status", aria_live="polite"),
            wrap="wrap",
        ),
        rx.cond(
            TraceEvidenceWorkflowState.safe_error != "",
            rx.callout(TraceEvidenceWorkflowState.safe_error, color_scheme="red"),
        ),
        rx.cond(
            TraceEvidenceWorkflowState.lineage_lifecycle == "loading",
            rx.text("Loading authoritative Evidence lineage…", role="status"),
        ),
        rx.cond(
            TraceEvidenceWorkflowState.lineage != None,  # noqa: E711
            rx.card(
                rx.vstack(
                    rx.heading("Structured Evidence lineage", size="5"),
                    rx.text(
                        "Completeness: " + TraceEvidenceWorkflowState.lineage.completeness,
                        role="status",
                    ),
                    rx.text(
                        "Graph Snapshot: "
                        + TraceEvidenceWorkflowState.lineage.graph_snapshot_id
                    ),
                    rx.text(
                        "Historical context: ", TraceEvidenceWorkflowState.lineage.historical
                    ),
                    rx.heading("Lineage nodes", size="4"),
                    rx.el.ul(rx.foreach(TraceEvidenceWorkflowState.lineage.nodes, _node)),
                    rx.heading("Directed lineage relationships", size="4"),
                    rx.el.ul(rx.foreach(TraceEvidenceWorkflowState.lineage.edges, _edge)),
                    rx.text(
                        "Limitations: "
                        + TraceEvidenceWorkflowState.lineage.limitations.join("; ")
                    ),
                    align="start",
                ),
                width="100%",
            ),
        ),
        rx.cond(
            TraceEvidenceWorkflowState.replay_lifecycle == "loading",
            rx.text("Running deterministic Evidence replay…", role="status"),
        ),
        rx.cond(
            TraceEvidenceWorkflowState.replay != None,  # noqa: E711
            rx.card(
                rx.vstack(
                    rx.heading("Replay result", size="5"),
                    rx.text("Eligibility: " + TraceEvidenceWorkflowState.replay.eligibility),
                    rx.text(
                        "Replay status: " + TraceEvidenceWorkflowState.replay.status,
                        role="status",
                    ),
                    rx.text("Method: " + TraceEvidenceWorkflowState.replay.method_id),
                    rx.text("Method version: " + TraceEvidenceWorkflowState.replay.method_version),
                    rx.text("Original: " + TraceEvidenceWorkflowState.replay.original_identity),
                    rx.text(
                        "Reproduced: " + TraceEvidenceWorkflowState.replay.reproduced_identity
                    ),
                    rx.text(
                        "Comparison scope: " + TraceEvidenceWorkflowState.replay.comparison_scope
                    ),
                    rx.text(
                        "Immutable replay inputs: "
                        + TraceEvidenceWorkflowState.replay.immutable_input_ids.join(", ")
                    ),
                    rx.text(
                        "Limitations: " + TraceEvidenceWorkflowState.replay.limitations.join("; ")
                    ),
                    align="start",
                ),
                width="100%",
            ),
        ),
        rx.cond(
            TraceEvidenceWorkflowState.verification_lifecycle == "loading",
            rx.text("Running scoped Evidence verification…", role="status"),
        ),
        rx.cond(
            TraceEvidenceWorkflowState.verification != None,  # noqa: E711
            rx.card(
                rx.vstack(
                    rx.heading("Scoped verification result", size="5"),
                    rx.text("Scope: " + TraceEvidenceWorkflowState.verification.scope),
                    rx.text(
                        "Status: " + TraceEvidenceWorkflowState.verification.status, role="status"
                    ),
                    rx.text("Verifier: " + TraceEvidenceWorkflowState.verification.verifier_id),
                    rx.text(
                        "Verifier version: "
                        + TraceEvidenceWorkflowState.verification.verifier_version
                    ),
                    rx.text("Proposition: " + TraceEvidenceWorkflowState.verification.proposition),
                    rx.text(
                        "Limitations: "
                        + TraceEvidenceWorkflowState.verification.limitations.join("; ")
                    ),
                    align="start",
                ),
                width="100%",
            ),
        ),
        rx.cond(
            TraceEvidenceWorkflowState.export_lifecycle == "loading",
            rx.text("Preparing privacy-safe Evidence export…", role="status"),
        ),
        rx.cond(
            TraceEvidenceWorkflowState.export != None,  # noqa: E711
            rx.card(
                rx.vstack(
                    rx.heading("Safe export ready", size="5"),
                    rx.text("Schema: " + TraceEvidenceWorkflowState.export.schema_version),
                    rx.text("Filename: " + TraceEvidenceWorkflowState.export.filename),
                    rx.text("Integrity: " + TraceEvidenceWorkflowState.export.integrity_status),
                    rx.code(
                        TraceEvidenceWorkflowState.export.content_digest,
                        color="var(--gray-12)",
                        white_space="normal",
                        word_break="break-all",
                    ),
                    align="start",
                ),
                role="status",
                width="100%",
            ),
        ),
        align="start",
        spacing="3",
        width="100%",
        id="trace-evidence-workflow",
    )
