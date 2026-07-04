from datetime import datetime, timedelta

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

import app.db.models  # noqa: F401
from app.api.dependencies import db_session
from app.db.base import Base
from app.db.models.candle_attribution import CandleAttribution
from app.db.models.intelligence_signals import IntelligenceSignalCandidate
from app.db.models.news_event import NewsEvent
from app.db.models.news_price_impact import NewsPriceImpact
from app.main import app
from app.services.intelligence.operator_review_service import OperatorReviewService
from app.services.intelligence.publishing_policy_service import PublishingPolicyService
from app.services.intelligence.signal_candidate_service import SignalCandidateService
from app.services.intelligence.signal_delivery_log_service import SignalDeliveryLogService
from app.services.intelligence.signal_governance_service import SignalGovernanceService
from app.services.intelligence.signal_governance_metrics import (
    INTELLIGENCE_POLICY_BLOCKS_TOTAL,
    INTELLIGENCE_SIGNAL_CANDIDATES_TOTAL,
    INTELLIGENCE_SIGNAL_DELIVERY_FAILURES_TOTAL,
)


def _session() -> Session:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    return Session(engine)


def _event(db: Session) -> NewsEvent:
    now = datetime(2026, 6, 3, 12, 0, 0)
    row = NewsEvent(
        event_key="etf-impact",
        canonical_title="Bitcoin ETF inflow impact",
        canonical_summary="ETF inflow coincided with BTC move",
        event_type="institutional",
        event_category="institutional",
        first_seen_at=now,
        last_seen_at=now + timedelta(minutes=5),
        source_count=3,
        article_count=3,
        cluster_confidence=0.9,
        btc_relevance_score=0.9,
        market_impact_score=0.8,
        event_sentiment="POSITIVE",
        event_confidence=0.82,
        provider_confidence=0.9,
        is_institutional_related=True,
    )
    db.add(row)
    db.flush()
    return row


def _impact(
    event: NewsEvent, *, confidence: float = 0.82, provider: float = 0.9
) -> NewsPriceImpact:
    return NewsPriceImpact(
        event_id=event.id,
        sentiment_label="POSITIVE",
        expected_direction="UP",
        actual_direction="UP",
        btc_relevance_score=0.9,
        market_impact_score=0.8,
        source_credibility_score=0.8,
        provider_confidence=provider,
        impact_confidence_score=confidence,
        confidence_score=confidence,
        dominant_window="4h",
        volatility_context=0.25,
        change_15m_pct=0.3,
        change_1h_pct=0.8,
        change_4h_pct=2.1,
        change_24h_pct=2.4,
        explanation_summary="This event coincided with BTC movement and may have contributed.",
    )


def _attribution(event: NewsEvent) -> CandleAttribution:
    return CandleAttribution(
        candle_id=1,
        event_id=event.id,
        timeframe="1h",
        candle_open_time=event.first_seen_at,
        candle_close_time=event.first_seen_at + timedelta(hours=1),
        confidence_score=0.8,
        btc_relevance_score=0.9,
        market_impact_score=0.8,
        source_confidence=0.8,
        source_credibility_score=0.8,
        provider_confidence=0.85,
        candle_direction="UP",
        dominant_window="1h",
        summary_text="Candle attribution candidate",
    )


def test_candidate_generation_policy_review_delivery_and_public_safety() -> None:
    db = _session()
    event = _event(db)
    impact = _impact(event)
    db.add(impact)
    db.flush()
    attribution = _attribution(event)
    db.add(attribution)
    db.commit()

    service = SignalCandidateService(db)
    candidate = service.create_from_price_impact(impact)
    candle_candidate = service.create_from_candle_attribution(attribution)
    low_event = _event(db)
    low_event.event_key = "low-impact"
    degraded_event = _event(db)
    degraded_event.event_key = "degraded-impact"
    db.flush()
    low_impact = _impact(low_event, confidence=0.2, provider=0.9)
    degraded_impact = _impact(degraded_event, confidence=0.8, provider=0.2)
    db.add_all([low_impact, degraded_impact])
    db.flush()
    low = service.create_from_price_impact(low_impact)
    degraded = service.create_from_price_impact(degraded_impact)
    missing = IntelligenceSignalCandidate(
        signal_type="news_market_impact",
        source_entity_type="manual",
        source_entity_id=1,
        title="Missing evidence",
        confidence_score=0.9,
        btc_relevance_score=0.9,
        market_impact_score=0.9,
        source_confidence=0.9,
        provider_confidence=0.9,
    )
    db.add(missing)
    db.flush()
    PublishingPolicyService(db).apply(missing)

    assert candidate.status == "pending_review"
    assert "auto_publish_disabled" in candidate.policy_reason
    assert candle_candidate.signal_type == "candle_attribution"
    assert low.requires_operator_review is True and "low_impact_confidence" in low.policy_reason
    assert (
        degraded.requires_operator_review is True
        and "provider_confidence_low" in degraded.policy_reason
    )
    assert degraded.status == "degraded"
    assert missing.requires_operator_review is True and "missing_evidence" in missing.policy_reason

    approved = OperatorReviewService(db).review(
        candidate.id, "approved", decision_reason="evidence accepted", confidence_override=0.77
    )
    assert candidate.status == "approved"
    assert approved.confidence_override == 0.77
    OperatorReviewService(db).review(low.id, "rejected", decision_reason="weak evidence")
    assert low.status == "rejected"
    OperatorReviewService(db).review(degraded.id, "held", decision_reason="provider degraded")
    assert degraded.status == "held"
    OperatorReviewService(db).review(missing.id, "false_positive", false_positive_marker=True)
    assert missing.status == "rejected"
    assert SignalGovernanceService(db).public_payload(missing)["evidence_based"] is False

    duplicate = service.create_from_price_impact(impact)
    assert "duplicate_signal" in duplicate.policy_reason

    ok_log = SignalDeliveryLogService(db).record(
        candidate.id, channel="web", delivery_status="success", target="public-web"
    )
    fail_log = SignalDeliveryLogService(db).record(
        candidate.id,
        channel="telegram",
        delivery_status="failed",
        target="chat",
        error_type="Token Error",
        error_message="token=secret leaked",
    )
    public = SignalGovernanceService(db).public_payload(candidate)

    assert ok_log.delivered_at is not None
    assert "secret" not in (fail_log.error_message_sanitized or "")
    assert public["correlation_not_causation"] is True
    assert public["not_financial_advice"] is True
    assert public["operator_reviewed"] is True
    assert public["evidence_based"] is True
    assert public["can_mark_false_positive"] is False
    assert public["evidence_refs"]["provider_confidence_snapshot"]["provider_confidence"] == 0.9
    assert INTELLIGENCE_SIGNAL_CANDIDATES_TOTAL._labelnames == ("signal_type", "status")
    assert INTELLIGENCE_POLICY_BLOCKS_TOTAL._labelnames == ("reason_code",)
    assert INTELLIGENCE_SIGNAL_DELIVERY_FAILURES_TOTAL._labelnames == ("channel", "reason_code")


def test_operator_and_public_signal_api_contracts() -> None:
    db = _session()
    event = _event(db)
    impact = _impact(event)
    db.add(impact)
    db.flush()
    candidate = SignalCandidateService(db).create_from_price_impact(impact)
    db.commit()

    def override() -> Session:
        return db

    app.dependency_overrides[db_session] = override
    client = TestClient(app, raise_server_exceptions=False)
    try:
        assert client.get("/api/v1/operator/signals/pending").status_code == 200
        assert client.get(f"/api/v1/operator/signals/{candidate.id}").status_code == 200
        assert (
            client.post(
                f"/api/v1/operator/signals/{candidate.id}/approve", json={"decision_reason": "ok"}
            ).status_code
            == 200
        )
        assert (
            client.post(
                f"/api/v1/operator/signals/{candidate.id}/confidence-override",
                json={"confidence_override": 0.7},
            ).status_code
            == 200
        )
        assert client.get("/api/v1/signals/news-market-impact").status_code == 200
        latest = client.get("/api/v1/signals/latest")
        assert latest.status_code == 200
        assert latest.json()["data"][0]["correlation_not_causation"] is True
        assert client.get(f"/api/v1/signals/{candidate.id}").status_code == 200
        assert client.get(f"/api/v1/signals/{candidate.id}/evidence").status_code == 200
        assert client.get(f"/api/v1/signals/{candidate.id}/delivery-logs").status_code == 200
    finally:
        app.dependency_overrides.clear()
