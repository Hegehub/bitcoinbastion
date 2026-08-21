from __future__ import annotations

from app.schemas.trace_disagreement import (
    SafeBitcoinNetworkClaimValueDTO,
    SafeRiskBandClaimValueDTO,
    SafeTraceClaimDTO,
    SafeTraceClaimProvenanceDTO,
    SafeTraceClaimSubjectDTO,
    SafeTraceDisagreementCollectionDTO,
    SafeTraceDisagreementCoverageDTO,
    SafeTraceDisagreementDTO,
)
from app.services.bastion_trace.claims.domain import (
    RiskBandClaimValue,
    TraceClaim,
    TraceClaimSubject,
)
from app.services.bastion_trace.disagreement.domain import TraceDisagreementEvaluation
from app.services.bastion_trace.privacy_policy import TracePrivacyPolicy


class TraceDisagreementApiProjection:
    """Privacy-policy-backed projection; it performs no analytical comparison."""

    def __init__(self, policy: TracePrivacyPolicy | None = None) -> None:
        self._policy = policy or TracePrivacyPolicy()

    def collection(
        self, graph_snapshot_id: str, evaluations: tuple[TraceDisagreementEvaluation, ...]
    ) -> SafeTraceDisagreementCollectionDTO:
        return SafeTraceDisagreementCollectionDTO(
            graph_snapshot_id=graph_snapshot_id,
            evaluations=tuple(self._evaluation(graph_snapshot_id, item) for item in evaluations),
        )

    def claim(self, claim: TraceClaim) -> SafeTraceClaimDTO:
        return self._claim(claim)

    def evaluation(
        self, graph_snapshot_id: str, item: TraceDisagreementEvaluation
    ) -> SafeTraceDisagreementDTO:
        return self._evaluation(graph_snapshot_id, item)

    def _evaluation(
        self, snapshot_id: str, item: TraceDisagreementEvaluation
    ) -> SafeTraceDisagreementDTO:
        subject = item.claim_set.subject if item.claim_set else None
        predicate = item.claim_set.predicate.value if item.claim_set else None
        values = self._policy.allowlisted("disagreement", {
            "evaluation_id": item.id,
            "status": item.status.value,
            "resolution_status": item.resolution_status.value,
            "subject": self._subject(subject) if subject else None,
            "predicate": predicate,
            "claims": tuple(self._claim(claim) for claim in item.participating_claims),
            "coverage": SafeTraceDisagreementCoverageDTO(
                eligible_claim_count=item.coverage.eligible_claim_count,
                eligible_producer_count=item.coverage.eligible_producer_count,
                unavailable_producer_count=item.coverage.unavailable_producer_count,
                insufficient_producer_count=item.coverage.insufficient_producer_count,
                failed_producer_count=item.coverage.failed_producer_count,
            ),
            "evaluator_version": item.evaluator_version,
            "graph_snapshot_id": snapshot_id,
            "limitations": item.limitations,
        })
        return SafeTraceDisagreementDTO.model_validate(values)

    def _claim(self, claim: TraceClaim) -> SafeTraceClaimDTO:
        value = (
            SafeRiskBandClaimValueDTO(kind="risk_band", band=claim.value.band.value)
            if isinstance(claim.value, RiskBandClaimValue)
            else SafeBitcoinNetworkClaimValueDTO(kind="bitcoin_network", network=claim.value.network)
        )
        values = self._policy.allowlisted("claim", {
            "id": claim.id, "subject": self._subject(claim.subject),
            "predicate": claim.predicate.value, "value": value,
            "producer": claim.producer_id, "source": claim.source_id,
            "producer_version": claim.producer_version, "evaluated_at": claim.evaluated_at,
            "confidence": claim.confidence,
            "provenance": SafeTraceClaimProvenanceDTO(
                input_references=claim.provenance.input_references,
                limitations=claim.provenance.limitations,
            ),
            "limitations": claim.limitations,
        })
        return SafeTraceClaimDTO.model_validate(values)

    @staticmethod
    def _subject(subject: TraceClaimSubject) -> SafeTraceClaimSubjectDTO:
        return SafeTraceClaimSubjectDTO(
            kind=subject.kind.value, object_id=subject.object_id, public_value=subject.public_value
        )
