from __future__ import annotations

from datetime import UTC, datetime
import hashlib
import json

from app.schemas.trace_evidence_workflow import (
    EvidenceLineageCompleteness,
    EvidenceLineageEdgeDTO,
    EvidenceLineageNodeDTO,
    EvidenceLineageNodeKind,
    EvidenceLineagePathDTO,
    EvidenceLineageRelation,
    EvidenceReplayEligibility,
    EvidenceReplayStatus,
    EvidenceVerificationScope,
    EvidenceVerificationStatus,
    SafeEvidenceExportDTO,
    SafeEvidenceLineageDTO,
    SafeEvidenceReplayDTO,
    SafeEvidenceVerificationDTO,
)
from app.schemas.trace_proof_packet import SafeTraceEvidenceDTO
from app.services.bastion_trace.privacy_policy import TracePrivacyPolicy
from app.services.bastion_trace.proof_packet import (
    TracePacketEvidence,
    TraceProofPacket,
    stable_evidence_id,
)
from app.services.bastion_trace.proof_packet_projection import TraceProofPacketApiProjection

REPLAY_METHOD_ID = "trace-evidence-identity-derivation"
REPLAY_METHOD_VERSION = "trace-evidence-identity-v1"
VERIFIER_ID = "trace-evidence-identity-integrity"
VERIFIER_VERSION = "trace-evidence-identity-integrity-v1"
EXPORT_SCHEMA_VERSION = "trace-evidence-export-v1"


class EvidenceNotFoundError(LookupError):
    pass


class TraceEvidenceWorkflowService:
    """Bounded lineage, deterministic replay and narrowly scoped verification authority."""

    def __init__(self, policy: TracePrivacyPolicy | None = None) -> None:
        self._policy = policy or TracePrivacyPolicy()

    def lineage(self, packet: TraceProofPacket, evidence_id: str) -> SafeEvidenceLineageDTO:
        evidence = self._evidence(packet, evidence_id)
        source_id = _digest_id("trace_source_reference", evidence.reference)
        graph_id = packet.graph_snapshot_id
        capture_id = packet.claim_capture_id
        nodes = {
            source_id: EvidenceLineageNodeDTO(
                id=source_id,
                kind=EvidenceLineageNodeKind.SOURCE_REFERENCE,
                label=evidence.source_category,
                captured_at=evidence.captured_at,
            ),
            evidence.evidence_id: EvidenceLineageNodeDTO(
                id=evidence.evidence_id,
                kind=EvidenceLineageNodeKind.EVIDENCE,
                label=evidence.kind,
                producer=evidence.producer,
                captured_at=evidence.captured_at,
                limitations=evidence.limitations,
            ),
            graph_id: EvidenceLineageNodeDTO(
                id=graph_id,
                kind=EvidenceLineageNodeKind.GRAPH_SNAPSHOT,
                label="Immutable Trace Graph Snapshot",
                captured_at=packet.captured_at,
            ),
            capture_id: EvidenceLineageNodeDTO(
                id=capture_id,
                kind=EvidenceLineageNodeKind.REPORT_CAPTURE,
                label="Trace analytical capture",
                captured_at=packet.captured_at,
            ),
            packet.packet_id: EvidenceLineageNodeDTO(
                id=packet.packet_id,
                kind=EvidenceLineageNodeKind.PROOF_PACKET,
                label="Trace Proof Packet",
                producer_version="trace-proof-packet-assembler-v1",
                captured_at=packet.captured_at,
                limitations=packet.limitations,
            ),
        }
        edges: list[EvidenceLineageEdgeDTO] = []

        def add_edge(source: str, target: str, relation: EvidenceLineageRelation) -> str:
            edge_id = _digest_id("trace_lineage_edge", source, target, relation.value)
            edges.append(
                EvidenceLineageEdgeDTO(
                    id=edge_id, source_id=source, target_id=target, relation=relation
                )
            )
            return edge_id

        source_edge = add_edge(
            source_id, evidence.evidence_id, EvidenceLineageRelation.PRODUCED_FROM
        )
        paths: list[EvidenceLineagePathDTO] = []
        for claim_id in evidence.linked_claim_ids:
            claim = next((item for item in packet.claims if item.id == claim_id), None)
            nodes[claim_id] = EvidenceLineageNodeDTO(
                id=claim_id,
                kind=EvidenceLineageNodeKind.CLAIM,
                label=claim.predicate.value if claim else "Trace Claim",
                producer=claim.producer_id if claim else None,
                producer_version=claim.producer_version if claim else None,
                captured_at=claim.evaluated_at if claim else packet.captured_at,
                limitations=claim.limitations if claim else ("Claim reference unavailable.",),
            )
            support = add_edge(evidence.evidence_id, claim_id, EvidenceLineageRelation.SUPPORTS)
            captured = add_edge(claim_id, capture_id, EvidenceLineageRelation.CAPTURED_IN)
            paths.append(
                _path(source_id, evidence.evidence_id, claim_id, capture_id,
                      edge_ids=(source_edge, support, captured))
            )
        for relationship_id in evidence.linked_relationship_ids:
            relationship = next(
                (item for item in packet.graph.relationships if item.id == relationship_id), None
            )
            nodes[relationship_id] = EvidenceLineageNodeDTO(
                id=relationship_id,
                kind=EvidenceLineageNodeKind.TOPOLOGY_RELATIONSHIP,
                label=relationship.relationship_type if relationship else "Trace relationship",
                producer=relationship.provenance.producer if relationship else None,
                captured_at=packet.captured_at,
                limitations=(
                    tuple(relationship.limitations)
                    if relationship
                    else ("Relationship reference unavailable.",)
                ),
            )
            support = add_edge(
                evidence.evidence_id, relationship_id, EvidenceLineageRelation.SUPPORTS
            )
            captured = add_edge(
                relationship_id, graph_id, EvidenceLineageRelation.CAPTURED_IN
            )
            paths.append(
                _path(source_id, evidence.evidence_id, relationship_id, graph_id,
                      edge_ids=(source_edge, support, captured))
            )
        included = add_edge(
            evidence.evidence_id, packet.packet_id, EvidenceLineageRelation.INCLUDED_IN
        )
        if not paths:
            paths.append(
                _path(source_id, evidence.evidence_id, packet.packet_id,
                      edge_ids=(source_edge, included))
            )
        graph_capture = add_edge(graph_id, capture_id, EvidenceLineageRelation.REFERENCED_BY)
        capture_packet = add_edge(
            capture_id, packet.packet_id, EvidenceLineageRelation.REFERENCED_BY
        )
        paths.append(
            _path(graph_id, capture_id, packet.packet_id,
                  edge_ids=(graph_capture, capture_packet))
        )
        return SafeEvidenceLineageDTO.model_validate(
            self._policy.allowlisted(
                "evidence_lineage",
                {
                    "evidence": self._safe_evidence(packet, evidence_id),
                    "graph_snapshot_id": packet.graph_snapshot_id,
                    "proof_packet_id": packet.packet_id,
                    "historical": packet.historical,
                    "completeness": EvidenceLineageCompleteness.COMPLETE,
                    "nodes": tuple(nodes[key] for key in sorted(nodes)),
                    "edges": tuple(sorted(edges, key=lambda item: item.id)),
                    "paths": tuple(sorted(paths, key=lambda item: item.path_id)),
                    "limitations": (
                        "Lineage records explicit support/provenance links, not causal proof.",
                        "Evidence lineage is distinct from Bitcoin transaction topology.",
                    ),
                },
            )
        )

    def replay(self, packet: TraceProofPacket, evidence_id: str) -> SafeEvidenceReplayDTO:
        evidence = self._evidence(packet, evidence_id)
        owner = _single_owner(evidence)
        if owner is None:
            eligibility = EvidenceReplayEligibility.NOT_REPLAYABLE
            status = EvidenceReplayStatus.NOT_REPLAYABLE
            reproduced = None
            inputs: tuple[str, ...] = ()
        else:
            eligibility = EvidenceReplayEligibility.REPLAYABLE
            reproduced = stable_evidence_id(evidence.kind, evidence.reference, owner)
            status = (
                EvidenceReplayStatus.MATCH
                if reproduced == evidence.evidence_id
                else EvidenceReplayStatus.MISMATCH
            )
            inputs = (evidence.reference, owner, packet.graph_snapshot_id)
        return SafeEvidenceReplayDTO.model_validate(
            self._policy.allowlisted(
                "evidence_replay",
                {
                    "replay_id": _digest_id(
                        "trace_evidence_replay", evidence.evidence_id, packet.graph_snapshot_id
                    ),
                    "evidence_id": evidence.evidence_id,
                    "graph_snapshot_id": packet.graph_snapshot_id,
                    "eligibility": eligibility,
                    "status": status,
                    "immutable_input_ids": inputs,
                    "method_id": REPLAY_METHOD_ID,
                    "method_version": REPLAY_METHOD_VERSION,
                    "original_identity": evidence.evidence_id,
                    "reproduced_identity": reproduced,
                    "comparison_scope": "stable Evidence identity equality",
                    "replayed_at": datetime.now(UTC),
                    "limitations": (
                        "Replay MATCH proves deterministic identity reproduction only.",
                        "Replay does not verify Claim truth, source authenticity, or causality.",
                    ),
                },
            )
        )

    def verification(
        self, packet: TraceProofPacket, evidence_id: str
    ) -> SafeEvidenceVerificationDTO:
        replay = self.replay(packet, evidence_id)
        status = (
            EvidenceVerificationStatus.VERIFIED
            if replay.status is EvidenceReplayStatus.MATCH
            else EvidenceVerificationStatus.FAILED
            if replay.status is EvidenceReplayStatus.MISMATCH
            else EvidenceVerificationStatus.UNSUPPORTED
        )
        return SafeEvidenceVerificationDTO.model_validate(
            self._policy.allowlisted(
                "evidence_verification",
                {
                    "verification_id": _digest_id(
                        "trace_evidence_verification", evidence_id, packet.graph_snapshot_id
                    ),
                    "evidence_id": evidence_id,
                    "graph_snapshot_id": packet.graph_snapshot_id,
                    "verifier_id": VERIFIER_ID,
                    "verifier_version": VERIFIER_VERSION,
                    "scope": EvidenceVerificationScope.EVIDENCE_IDENTITY_INTEGRITY,
                    "status": status,
                    "verified_at": datetime.now(UTC),
                    "proposition": (
                        "Stored Evidence identity matches its pinned kind/reference/owner inputs."
                    ),
                    "limitations": (
                        "This verifier checks Evidence identity integrity only.",
                        "It does not verify analytical conclusions or Bitcoin inclusion.",
                    ),
                },
            )
        )

    def export(self, packet: TraceProofPacket, evidence_id: str) -> SafeEvidenceExportDTO:
        lineage = self.lineage(packet, evidence_id)
        replay = self.replay(packet, evidence_id)
        verification = self.verification(packet, evidence_id)
        limitations = (
            "Export is a privacy-safe projection, not new analytical authority.",
            "Export digest protects these bytes; it is not a truth or signature proof.",
        )
        content_value = {
            "schema_version": EXPORT_SCHEMA_VERSION,
            "evidence": lineage.evidence.model_dump(mode="json"),
            "graph_snapshot_id": packet.graph_snapshot_id,
            "proof_packet_id": packet.packet_id,
            "lineage": lineage.model_dump(mode="json", exclude={"evidence"}),
            "replay": replay.model_dump(mode="json"),
            "verification": verification.model_dump(mode="json"),
            "limitations": limitations,
        }
        content = json.dumps(content_value, sort_keys=True, separators=(",", ":"))
        digest = hashlib.sha256(content.encode()).hexdigest()
        return SafeEvidenceExportDTO.model_validate(
            self._policy.allowlisted(
                "evidence_export",
                {
                    "export_id": f"trace_evidence_export:{digest[:24]}",
                    "evidence_id": evidence_id,
                    "graph_snapshot_id": packet.graph_snapshot_id,
                    "proof_packet_id": packet.packet_id,
                    "schema_version": EXPORT_SCHEMA_VERSION,
                    "media_type": "application/json",
                    "filename": f"trace-evidence-{_safe_filename_id(evidence_id)}.json",
                    "content": content,
                    "content_digest": digest,
                    "integrity_status": "content_integrity_checked",
                    "limitations": limitations,
                },
            )
        )

    @staticmethod
    def _evidence(packet: TraceProofPacket, evidence_id: str) -> TracePacketEvidence:
        evidence = next((item for item in packet.evidence if item.evidence_id == evidence_id), None)
        if evidence is None:
            raise EvidenceNotFoundError(evidence_id)
        return evidence

    @staticmethod
    def _safe_evidence(packet: TraceProofPacket, evidence_id: str) -> SafeTraceEvidenceDTO:
        projected = TraceProofPacketApiProjection().project(packet)
        evidence = next((item for item in projected.evidence if item.evidence_id == evidence_id), None)
        if evidence is None:
            raise EvidenceNotFoundError(evidence_id)
        return evidence


def _single_owner(evidence: TracePacketEvidence) -> str | None:
    owners = evidence.linked_claim_ids + evidence.linked_relationship_ids
    return owners[0] if len(owners) == 1 else None


def _path(*node_ids: str, edge_ids: tuple[str, ...]) -> EvidenceLineagePathDTO:
    return EvidenceLineagePathDTO(
        path_id=_digest_id("trace_lineage_path", *node_ids, *edge_ids),
        node_ids=node_ids,
        edge_ids=edge_ids,
    )


def _digest_id(prefix: str, *values: str) -> str:
    digest = hashlib.sha256("\x1f".join(values).encode()).hexdigest()[:24]
    return f"{prefix}:{digest}"


def _safe_filename_id(value: str) -> str:
    return "".join(character if character.isalnum() else "-" for character in value)[-48:]
