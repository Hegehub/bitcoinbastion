from datetime import UTC, datetime
from pathlib import Path

from bastion_ui.domain.prompt15 import (
    EvidenceExportViewModel,
    adapt_evidence_export,
    adapt_evidence_lineage,
    adapt_evidence_replay,
    adapt_evidence_verification,
)
from bastion_ui.domain.prompt15_scenarios import PROMPT15_SCENARIOS
from bastion_ui.domain.provenance import ProvenanceState
from bastion_ui.transport.generated_schemas import (
    SafeEvidenceExportDTO,
    SafeEvidenceLineageDTO,
    SafeEvidenceReplayDTO,
    SafeEvidenceVerificationDTO,
)

NOW = datetime(2026, 8, 16, tzinfo=UTC)


def test_feature54_preserves_backend_lineage_direction_branching_and_completeness() -> None:
    dto = SafeEvidenceLineageDTO.model_validate(
        {
            "evidence": {
                "evidence_id": "trace_evidence:1",
                "kind": "topology_relationship_support",
                "reference": "observation:1",
                "producer": "topology-adapter",
                "source_category": "public_chain",
                "captured_at": NOW,
                "linked_claim_ids": [],
                "linked_relationship_ids": ["relationship:1"],
                "integrity_status": "not_checked",
                "verification_status": "not_verified",
                "limitations": [],
            },
            "graph_snapshot_id": "trace_snapshot:a",
            "proof_packet_id": "trace_proof_packet:a",
            "historical": True,
            "completeness": "complete",
            "nodes": [
                {"id": "source:1", "kind": "source_reference", "label": "public chain"},
                {"id": "trace_evidence:1", "kind": "evidence", "label": "Evidence"},
            ],
            "edges": [
                {
                    "id": "edge:1",
                    "source_id": "source:1",
                    "target_id": "trace_evidence:1",
                    "relation": "produced_from",
                    "direction": "directed",
                }
            ],
            "paths": [
                {
                    "path_id": "path:1",
                    "node_ids": ["source:1", "trace_evidence:1"],
                    "edge_ids": ["edge:1"],
                }
            ],
            "limitations": ["Not causal proof."],
        }
    )
    view = adapt_evidence_lineage(dto)
    assert view.historical is True
    assert view.completeness == "complete"
    assert view.edges[0].direction == "directed"
    assert view.paths[0].node_ids == ("source:1", "trace_evidence:1")


def test_replay_verification_and_export_adapters_never_upgrade_semantics() -> None:
    replay = adapt_evidence_replay(SafeEvidenceReplayDTO.model_validate({
        "replay_id": "replay:1", "evidence_id": "trace_evidence:1",
        "graph_snapshot_id": "trace_snapshot:a", "eligibility": "replayable",
        "status": "match", "immutable_input_ids": ["observation:1"],
        "method_id": "identity", "method_version": "v1",
        "original_identity": "trace_evidence:1", "reproduced_identity": "trace_evidence:1",
        "comparison_scope": "identity equality", "replayed_at": NOW,
        "limitations": ["MATCH is not generic verification."],
    }))
    verification = adapt_evidence_verification(SafeEvidenceVerificationDTO.model_validate({
        "verification_id": "verification:1", "evidence_id": "trace_evidence:1",
        "graph_snapshot_id": "trace_snapshot:a", "verifier_id": "identity-integrity",
        "verifier_version": "v1", "scope": "evidence_identity_integrity",
        "status": "verified", "verified_at": NOW,
        "proposition": "Identity matches pinned inputs.",
        "limitations": ["Does not verify analytical truth."],
    }))
    exported = adapt_evidence_export(SafeEvidenceExportDTO.model_validate({
        "export_id": "export:1", "evidence_id": "trace_evidence:1",
        "graph_snapshot_id": "trace_snapshot:a", "proof_packet_id": "packet:a",
        "schema_version": "trace-evidence-export-v1", "media_type": "application/json",
        "filename": "trace-evidence-1.json", "content": "{}", "content_digest": "digest",
        "integrity_status": "content_integrity_checked", "limitations": [],
    }))
    assert replay.status == "match"
    assert verification.scope == "evidence_identity_integrity"
    assert verification.status == "verified"
    assert exported.schema_version == "trace-evidence-export-v1"
    assert "content" not in EvidenceExportViewModel.model_fields


def test_prompt15_components_and_state_do_not_infer_or_store_raw_payloads() -> None:
    component = Path("bastion_ui/components/evidence/evidence_workflow.py").read_text()
    state = Path("bastion_ui/state/trace_evidence_workflow_state.py").read_text()
    assert "generated_schemas" not in component
    assert "dict[str" not in state
    assert "token == self.generation" in state
    assert "evidence_id == self.workflow_evidence_id" in state
    assert "snapshot_id == self.workflow_snapshot_id" in state
    assert "RELATED_TO" not in component + state
    assert "is_verified" not in component + state
    assert "json.dumps" not in component + state
    assert "TRACE_EVIDENCE_LINEAGE_PRIVACY_CANARY_NEVER_BROWSER" not in component + state


def test_prompt15_scenarios_are_typed_deterministic_demo_fixtures() -> None:
    assert len(PROMPT15_SCENARIOS) == len({item.kind for item in PROMPT15_SCENARIOS})
    assert all(item.provenance is ProvenanceState.DEMO_FIXTURE for item in PROMPT15_SCENARIOS)
