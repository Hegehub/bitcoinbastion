from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.db.models.intelligence_signals import IntelligencePublishingPolicy, IntelligenceSignalCandidate
from app.repositories.intelligence_signal_repository import IntelligenceSignalRepository
from app.services.intelligence.signal_governance_metrics import INTELLIGENCE_POLICY_BLOCKS_TOTAL


@dataclass(frozen=True)
class PublishingDecision:
    decision: str
    reason_codes: list[str]
    requires_operator_review: bool
    status: str


class PublishingPolicyService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = IntelligenceSignalRepository(db)

    def default_policy(self) -> IntelligencePublishingPolicy:
        return self.repo.active_policy()

    def evaluate(self, candidate: IntelligenceSignalCandidate) -> PublishingDecision:
        policy = self.default_policy()
        reasons: list[str] = []
        if (candidate.btc_relevance_score or 0.0) < policy.min_btc_relevance_score:
            reasons.append("low_btc_relevance")
        if candidate.confidence_score < policy.min_impact_confidence:
            reasons.append("low_impact_confidence")
        if (candidate.source_confidence or 0.0) < policy.min_source_confidence:
            reasons.append("low_source_confidence")
        if (candidate.provider_confidence or 0.0) < policy.min_provider_confidence:
            reasons.append("provider_confidence_low")
        if candidate.evidence_packet_id is None and not any([candidate.article_id, candidate.event_id, candidate.impact_id, candidate.attribution_id, candidate.candle_id]):
            reasons.append("missing_evidence")
        if self.repo.duplicate_count(candidate) > 0:
            reasons.append("duplicate_signal")
        if candidate.signal_type in {"security_shock"} and policy.require_review_for_security_shock:
            reasons.append("security_review_required")
        if candidate.signal_type in {"regulatory_risk"} and policy.require_review_for_regulatory_shock:
            reasons.append("regulatory_review_required")
        if candidate.signal_type == "false_signal" and policy.require_review_for_false_signal:
            reasons.append("false_signal_review_required")
        if "provider_degraded" in candidate.policy_reason and policy.require_review_for_provider_degraded:
            reasons.append("provider_degraded")
        if reasons:
            for reason in reasons:
                INTELLIGENCE_POLICY_BLOCKS_TOTAL.labels(reason_code=self._bounded(reason)).inc()
        requires_review = bool(reasons) or not policy.allow_auto_publish
        if not policy.allow_auto_publish and "auto_publish_disabled" not in reasons:
            reasons.append("auto_publish_disabled")
        decision = "blocked" if reasons else "approved"
        status = "pending_review" if requires_review else "approved"
        if "provider_degraded" in reasons:
            status = "degraded"
        return PublishingDecision(decision=decision, reason_codes=reasons, requires_operator_review=requires_review, status=status)

    def apply(self, candidate: IntelligenceSignalCandidate) -> IntelligenceSignalCandidate:
        decision = self.evaluate(candidate)
        candidate.policy_decision = decision.decision
        candidate.policy_reason = ",".join(decision.reason_codes)
        candidate.requires_operator_review = decision.requires_operator_review
        candidate.status = decision.status
        self.db.flush()
        return candidate

    def _bounded(self, value: str) -> str:
        allowed = {
            "low_btc_relevance",
            "low_impact_confidence",
            "low_source_confidence",
            "provider_confidence_low",
            "missing_evidence",
            "security_review_required",
            "regulatory_review_required",
            "false_signal_review_required",
            "provider_degraded",
            "auto_publish_disabled",
            "duplicate_signal",
        }
        return value if value in allowed else "other"
