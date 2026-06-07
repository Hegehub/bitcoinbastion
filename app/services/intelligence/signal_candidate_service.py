from __future__ import annotations

from sqlalchemy.orm import Session

from app.db.models.candle_attribution import CandleAttribution
from app.db.models.intelligence_signals import IntelligenceSignalCandidate
from app.db.models.news_event import NewsEvent
from app.db.models.news_price_impact import NewsPriceImpact
from app.repositories.intelligence_signal_repository import IntelligenceSignalRepository
from app.services.intelligence.publishing_policy_service import PublishingPolicyService
from app.services.events.domain_event_publisher import publish_domain_event
from app.services.intelligence.signal_governance_metrics import (
    INTELLIGENCE_SIGNAL_CANDIDATES_TOTAL,
    INTELLIGENCE_SIGNAL_PENDING_REVIEW_TOTAL,
)

MVP_SIGNAL_TYPES = {
    "news_market_impact",
    "candle_attribution",
    "delayed_reaction",
    "false_signal",
    "security_shock",
    "regulatory_risk",
    "macro_shock",
    "narrative_spike",
    "news_shock_index",
}


class SignalCandidateService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = IntelligenceSignalRepository(db)
        self.policy = PublishingPolicyService(db)

    def create_from_price_impact(self, impact: NewsPriceImpact) -> IntelligenceSignalCandidate:
        signal_type = "false_signal" if impact.false_signal_detected else "delayed_reaction" if impact.delayed_reaction_detected else "news_market_impact"
        candidate = IntelligenceSignalCandidate(
            signal_type=signal_type,
            source_entity_type="news_price_impact",
            source_entity_id=impact.id,
            article_id=impact.article_id,
            event_id=impact.event_id,
            impact_id=impact.id,
            title=f"BTC market impact: {impact.sentiment_label}",
            summary=impact.explanation_summary or "BTC movement coincided with a news impact window.",
            confidence_score=impact.impact_confidence_score or impact.confidence_score or 0.0,
            btc_relevance_score=impact.btc_relevance_score,
            market_impact_score=impact.market_impact_score,
            source_confidence=impact.source_credibility_score,
            provider_confidence=impact.provider_confidence,
            direction_label=impact.actual_direction,
            dominant_window=impact.dominant_window,
            evidence_packet_id=f"news_price_impact:{impact.id}",
            policy_reason="provider_degraded" if impact.provider_confidence < 0.5 else "",
        )
        return self._persist_and_apply(candidate)

    def create_from_candle_attribution(self, attribution: CandleAttribution) -> IntelligenceSignalCandidate:
        candidate = IntelligenceSignalCandidate(
            signal_type="candle_attribution",
            source_entity_type="candle_attribution",
            source_entity_id=attribution.id,
            article_id=attribution.article_id,
            event_id=attribution.event_id,
            candle_id=attribution.candle_id,
            attribution_id=attribution.id,
            title=attribution.summary_text or "BTC candle attribution candidate",
            summary="Event coincided with BTC candle movement; attribution is correlation-based.",
            confidence_score=attribution.confidence_score,
            btc_relevance_score=attribution.btc_relevance_score,
            market_impact_score=attribution.market_impact_score,
            source_confidence=attribution.source_confidence or attribution.source_credibility_score,
            provider_confidence=attribution.provider_confidence,
            direction_label=attribution.candle_direction,
            dominant_window=attribution.dominant_window or attribution.window_used,
            evidence_packet_id=f"candle_attribution:{attribution.id}",
        )
        return self._persist_and_apply(candidate)

    def create_from_news_event(self, event: NewsEvent) -> IntelligenceSignalCandidate:
        candidate = IntelligenceSignalCandidate(
            signal_type=self._event_signal_type(event),
            source_entity_type="news_event",
            source_entity_id=event.id,
            event_id=event.id,
            title=event.canonical_title,
            summary=event.canonical_summary,
            confidence_score=event.event_confidence,
            btc_relevance_score=event.btc_relevance_score,
            market_impact_score=event.market_impact_score,
            source_confidence=event.cluster_confidence,
            provider_confidence=event.provider_confidence,
            direction_label=event.event_sentiment,
            evidence_packet_id=f"news_event:{event.id}",
            policy_reason="provider_degraded" if event.provider_confidence < 0.5 else "",
        )
        return self._persist_and_apply(candidate)

    def generate_from_high_confidence_impacts(self, limit: int = 50) -> list[IntelligenceSignalCandidate]:
        impacts = (
            self.db.query(NewsPriceImpact)
            .filter(NewsPriceImpact.impact_confidence_score >= 0.65)
            .order_by(NewsPriceImpact.calculated_at.desc(), NewsPriceImpact.id.desc())
            .limit(limit)
            .all()
        )
        return [self.create_from_price_impact(impact) for impact in impacts]

    def placeholder_detectors(self) -> dict[str, list[IntelligenceSignalCandidate]]:
        return {
            "security_shock_detector": [],
            "regulatory_risk_detector": [],
            "narrative_heatmap_spike_detector": [],
            "news_shock_index_spike_detector": [],
        }

    def _persist_and_apply(self, candidate: IntelligenceSignalCandidate) -> IntelligenceSignalCandidate:
        self.repo.add_candidate(candidate)
        self.policy.apply(candidate)
        INTELLIGENCE_SIGNAL_CANDIDATES_TOTAL.labels(signal_type=self._bounded_type(candidate.signal_type), status=self._bounded_status(candidate.status)).inc()
        if candidate.requires_operator_review:
            reason = (candidate.policy_reason.split(",") or ["review_required"])[0] or "review_required"
            INTELLIGENCE_SIGNAL_PENDING_REVIEW_TOTAL.labels(signal_type=self._bounded_type(candidate.signal_type), reason_code=self._bounded_reason(reason)).inc()
        self._publish_candidate_events(candidate)
        return candidate

    def _event_signal_type(self, event: NewsEvent) -> str:
        if event.is_security_related:
            return "security_shock"
        if event.is_regulatory_related:
            return "regulatory_risk"
        if event.is_macro_related:
            return "macro_shock"
        return "news_market_impact"

    def _publish_candidate_events(self, candidate: IntelligenceSignalCandidate) -> None:
        payload = {
            "signal_id": candidate.id,
            "signal_type": candidate.signal_type,
            "status": candidate.status,
            "confidence": candidate.confidence_score,
            "policy_status": candidate.policy_decision,
            "policy_reason": candidate.policy_reason,
            "operator_review_required": candidate.requires_operator_review,
            "created_at": candidate.created_at.isoformat() if candidate.created_at else None,
            "updated_at": candidate.updated_at.isoformat() if candidate.updated_at else None,
            "limitations": [
                "Signal output is informational and not financial advice.",
                "Correlation is not proof of causation.",
                "No automatic execution is performed by event publication.",
            ],
            "not_financial_advice": True,
            "correlation_not_causation": True,
            "no_auto_execution": True,
        }
        publish_domain_event(
            self.db,
            "signal.created",
            payload,
            aggregate_type="signal",
            aggregate_id=candidate.id,
            source="signal_governance",
            idempotency_key=f"signal.created:signal:{candidate.id}:created",
        )
        if candidate.requires_operator_review:
            publish_domain_event(
                self.db,
                "signal.operator_review_required",
                payload,
                aggregate_type="signal",
                aggregate_id=candidate.id,
                source="signal_governance",
                idempotency_key=f"signal.operator_review_required:signal:{candidate.id}:review",
            )

    def _bounded_type(self, value: str) -> str:
        return value if value in MVP_SIGNAL_TYPES else "other"

    def _bounded_status(self, value: str) -> str:
        return value if value in {"draft", "pending_review", "approved", "rejected", "held", "published", "expired", "degraded"} else "other"

    def _bounded_reason(self, value: str) -> str:
        allowed = {"low_btc_relevance", "low_impact_confidence", "low_source_confidence", "provider_confidence_low", "missing_evidence", "auto_publish_disabled", "review_required"}
        return value if value in allowed else "other"
