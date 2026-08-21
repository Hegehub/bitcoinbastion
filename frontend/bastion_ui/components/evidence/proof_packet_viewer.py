from __future__ import annotations

import reflex as rx

from bastion_ui.components.evidence.evidence_workflow import evidence_workflow_panel
from bastion_ui.domain.prompt13 import TraceClaimViewModel
from bastion_ui.domain.prompt14 import TraceEvidenceViewModel, TracePacketDisagreementViewModel
from bastion_ui.state.trace_evidence_workflow_state import TraceEvidenceWorkflowState
from bastion_ui.state.trace_proof_packet_state import TraceProofPacketState


def _claim(claim: TraceClaimViewModel) -> rx.Component:
    return rx.card(
        rx.vstack(
            rx.heading(claim.value_label, size="4"),
            rx.text("Predicate: " + claim.predicate),
            rx.text("Producer: " + claim.producer),
            rx.text("Source: " + claim.source),
            rx.text("Confidence: " + claim.confidence),
            rx.text("Evidence linked to Claim " + claim.id),
            align="start",
        ),
        id="claim-" + claim.id,
        width="100%",
    )


def _evidence(item: TraceEvidenceViewModel) -> rx.Component:
    return rx.button(
        rx.vstack(
            rx.text(item.kind.replace("_", " "), weight="bold"),
            rx.code(
                item.evidence_id,
                color="var(--gray-12)",
                white_space="normal",
                word_break="break-all",
            ),
            rx.text("Producer: " + item.producer),
            rx.text("Verification: " + item.verification_status.replace("_", " ")),
            rx.text("Integrity: " + item.integrity_status.replace("_", " ")),
            align="start",
        ),
        on_click=[
            TraceProofPacketState.select_evidence_item(item),
            TraceEvidenceWorkflowState.prepare(
                TraceProofPacketState.packet_report_id,
                TraceProofPacketState.active_packet.graph_snapshot_id,
                item.evidence_id,
                TraceProofPacketState.packet_snapshot_id != "",
            ),
        ],
        aria_label="Inspect evidence " + item.evidence_id,
        id="evidence-trigger-" + item.evidence_id,
        variant="soft",
        color_scheme="gray",
        width="100%",
        height="auto",
        min_height="5rem",
        padding="0.75rem",
        white_space="normal",
    )


def _disagreement(item: TracePacketDisagreementViewModel) -> rx.Component:
    return rx.card(
        rx.vstack(
            rx.heading(item.status.replace("_", " "), size="4"),
            rx.text("Resolution: " + item.resolution_status.replace("_", " ")),
            rx.text("Competing Claim identities: " + item.claim_ids.join(", ")),
            align="start",
        ),
        role="status",
        width="100%",
    )


def _detail() -> rx.Component:
    return rx.cond(
        TraceProofPacketState.selected_evidence != None,  # noqa: E711
        rx.card(
            rx.vstack(
                rx.heading("Evidence details", size="5"),
                rx.code(
                    TraceProofPacketState.selected_evidence.evidence_id,
                    white_space="normal",
                    word_break="break-all",
                ),
                rx.text("Reference: " + TraceProofPacketState.selected_evidence.reference),
                rx.text(
                    "Source category: "
                    + TraceProofPacketState.selected_evidence.source_category
                ),
                rx.text(
                    "Linked Claims: "
                    + TraceProofPacketState.selected_evidence.linked_claim_ids.join(", ")
                ),
                rx.text(
                    "Linked relationships: "
                    + TraceProofPacketState.selected_evidence.linked_relationship_ids.join(", ")
                ),
                rx.text(
                    "Limitations: "
                    + TraceProofPacketState.selected_evidence.limitations.join("; ")
                ),
                rx.button(
                    "Close evidence details",
                    on_click=TraceProofPacketState.close_evidence_item,
                    aria_label="Close evidence details",
                ),
                evidence_workflow_panel(),
                align="start",
            ),
            role="dialog",
            aria_label="Evidence details",
            width="100%",
        ),
    )


def proof_packet_viewer() -> rx.Component:
    packet = TraceProofPacketState.active_packet
    return rx.vstack(
        rx.cond(TraceProofPacketState.lifecycle == "loading", rx.text("Loading Proof Packet…")),
        rx.cond(
            TraceProofPacketState.safe_error != "",
            rx.callout(TraceProofPacketState.safe_error, color_scheme="red"),
        ),
        rx.cond(
            packet != None,  # noqa: E711
            rx.vstack(
                rx.callout(
                    "Analytical packet only. Linked evidence is not independent verification, "
                    "legal proof, or Bitcoin consensus proof.",
                    color_scheme="amber",
                    high_contrast=True,
                ),
                rx.cond(
                    packet.historical,
                    rx.badge("Historical Proof Packet", color_scheme="gray", high_contrast=True),
                ),
                rx.heading("Packet summary", size="5"),
                rx.text("Subject: " + packet.subject),
                rx.code(
                    packet.packet_id,
                    color="var(--gray-12)",
                    white_space="normal",
                    word_break="break-all",
                ),
                rx.text("Graph Snapshot: " + packet.graph_snapshot_id),
                rx.text("Captured: " + packet.captured_at),
                rx.text("Verification: " + packet.verification_status.replace("_", " ")),
                rx.text("Integrity: " + packet.integrity_status.replace("_", " ")),
                rx.heading("Analytical Claims", size="5"),
                rx.vstack(rx.foreach(packet.claims, _claim), width="100%"),
                rx.heading("Agreement and disagreement", size="5"),
                rx.vstack(rx.foreach(packet.disagreements, _disagreement), width="100%"),
                rx.heading("Linked evidence", size="5"),
                rx.text("Evidence membership and linkage were selected by the backend assembler."),
                rx.vstack(rx.foreach(packet.evidence, _evidence), width="100%"),
                _detail(),
                rx.heading("Limitations", size="5"),
                rx.text(packet.limitations.join("; ")),
                align="start",
                width="100%",
            ),
        ),
        align="start",
        spacing="4",
        width="100%",
        id="trace-proof-packet",
    )
