from __future__ import annotations

from enum import Enum
from typing import Mapping

TRACE_PRIVACY_POLICY_VERSION = "trace-browser-policy-v1"


class TraceDataClassification(str, Enum):
    PUBLIC_CHAIN = "public_chain"
    BROWSER_SAFE_ANALYTICAL = "browser_safe_analytical"
    REDACTABLE = "redactable"
    INTERNAL = "internal"
    SECRET = "secret"


class TracePrivacyAction(str, Enum):
    ALLOW = "allow"
    DENY = "deny"
    REDACT = "redact"


class TracePrivacyPolicy:
    """Central default-deny authority for the Trace browser boundary."""

    DEFAULT_ACTION = TracePrivacyAction.DENY

    _FIELDS: Mapping[str, Mapping[str, TraceDataClassification]] = {
        "graph": {name: TraceDataClassification.BROWSER_SAFE_ANALYTICAL for name in (
            "metadata", "objects", "relationships", "observations", "snapshot"
        )},
        "claim": {name: TraceDataClassification.BROWSER_SAFE_ANALYTICAL for name in (
            "id", "subject", "predicate", "value", "producer", "source", "producer_version",
            "evaluated_at", "confidence", "provenance", "limitations"
        )},
        "disagreement": {name: TraceDataClassification.BROWSER_SAFE_ANALYTICAL for name in (
            "evaluation_id", "status", "resolution_status", "subject", "predicate", "claims",
            "coverage", "evaluator_version", "graph_snapshot_id", "limitations"
        )},
        "provenance": {name: TraceDataClassification.BROWSER_SAFE_ANALYTICAL for name in (
            "producer", "producer_version", "source_category", "input_references", "limitations"
        )},
        "evidence": {name: TraceDataClassification.BROWSER_SAFE_ANALYTICAL for name in (
            "evidence_id", "kind", "reference", "producer", "source_category", "captured_at",
            "linked_claim_ids", "linked_relationship_ids", "integrity_status",
            "verification_status", "limitations"
        )},
        "proof_packet": {name: TraceDataClassification.BROWSER_SAFE_ANALYTICAL for name in (
            "packet_id", "packet_schema_version", "assembler_version", "trace_id",
            "graph_snapshot_id", "claim_capture_id", "subject", "captured_at", "historical",
            "topology", "claims", "disagreements", "evidence", "packet_digest",
            "integrity_status", "verification_status", "advisory_only",
            "not_legal_verification", "not_bitcoin_consensus_proof", "limitations"
        )},
        "evidence_lineage": {
            name: TraceDataClassification.BROWSER_SAFE_ANALYTICAL
            for name in (
                "evidence", "graph_snapshot_id", "proof_packet_id", "historical",
                "completeness", "nodes", "edges", "paths", "limitations",
            )
        },
        "evidence_replay": {
            name: TraceDataClassification.BROWSER_SAFE_ANALYTICAL
            for name in (
                "replay_id", "evidence_id", "graph_snapshot_id", "eligibility", "status",
                "immutable_input_ids", "method_id", "method_version", "original_identity",
                "reproduced_identity", "comparison_scope", "replayed_at", "limitations",
            )
        },
        "evidence_verification": {
            name: TraceDataClassification.BROWSER_SAFE_ANALYTICAL
            for name in (
                "verification_id", "evidence_id", "graph_snapshot_id", "verifier_id",
                "verifier_version", "scope", "status", "verified_at", "proposition",
                "limitations",
            )
        },
        "evidence_export": {
            name: TraceDataClassification.BROWSER_SAFE_ANALYTICAL
            for name in (
                "export_id", "evidence_id", "graph_snapshot_id", "proof_packet_id",
                "schema_version", "media_type", "filename", "content", "content_digest",
                "integrity_status", "limitations",
            )
        },
    }

    def decision(self, domain_type: str, field: str) -> TracePrivacyAction:
        classification = self._FIELDS.get(domain_type, {}).get(field)
        if classification in {
            TraceDataClassification.PUBLIC_CHAIN,
            TraceDataClassification.BROWSER_SAFE_ANALYTICAL,
        }:
            return TracePrivacyAction.ALLOW
        if classification is TraceDataClassification.REDACTABLE:
            return TracePrivacyAction.REDACT
        return TracePrivacyAction.DENY

    def allowlisted(self, domain_type: str, values: Mapping[str, object]) -> dict[str, object]:
        return {
            key: value
            for key, value in values.items()
            if self.decision(domain_type, key) is TracePrivacyAction.ALLOW
        }
