from datetime import datetime, timedelta

from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

import app.db.models  # noqa: F401
from app.db.base import Base
from app.db.models.event_fingerprint import EventFingerprintRecord
from app.db.models.market_memory_operator_review import MarketMemoryOperatorReview
from app.db.models.market_memory_record import MarketMemoryRecord
from app.db.models.news_event import NewsEvent
from app.db.models.news_price_impact import NewsPriceImpact
from app.db.models.pattern_statistics import PatternStatistics
from app.services.intelligence.market_memory import (
    EventFingerprintBuilder,
    HistoricalSimilarityEngine,
    MarketMemoryEvidenceBuilder,
    OperatorReviewService,
    PatternMatcher,
    PatternStatisticsService,
)


def _session() -> Session:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    return Session(engine)


def _event(title: str, seen_at: datetime, category: str = "institutional", sentiment: str = "POSITIVE") -> NewsEvent:
    return NewsEvent(
        event_key=title.lower().replace(" ", "-"),
        canonical_title=title,
        canonical_summary=title,
        event_type=category,
        event_category=category,
        first_seen_at=seen_at,
        last_seen_at=seen_at + timedelta(minutes=5),
        source_count=3,
        article_count=3,
        btc_relevance_score=0.9,
        market_impact_score=0.8,
        event_sentiment=sentiment,
        event_confidence=0.82,
        is_institutional_related=category == "institutional",
        is_security_related=category == "security",
        is_regulatory_related=category == "regulatory",
        is_macro_related=category == "macro",
        provider_confidence=0.9,
    )


def _impact(event: NewsEvent, move: float) -> NewsPriceImpact:
    return NewsPriceImpact(
        event_id=event.id,
        sentiment_label=event.event_sentiment,
        expected_direction="UP" if move >= 0 else "DOWN",
        actual_direction="UP" if move >= 0 else "DOWN",
        btc_relevance_score=event.btc_relevance_score,
        market_impact_score=event.market_impact_score,
        provider_confidence=0.9,
        impact_confidence_score=0.8,
        dominant_window="4h",
        volatility_context=0.25,
        change_15m_pct=move / 4,
        change_1h_pct=move / 2,
        change_4h_pct=move,
        change_24h_pct=move + 0.5,
    )


def _seed(db: Session) -> tuple[NewsEvent, NewsEvent, NewsEvent]:
    now = datetime(2026, 6, 2, 12, 0, 0)
    reference = _event("Bitcoin ETF inflow shock accelerates", now)
    similar = _event("Bitcoin ETF inflow shock repeats", now - timedelta(days=20))
    different = _event("Exchange hack security incident", now - timedelta(days=30), "security", "NEGATIVE")
    db.add_all([reference, similar, different])
    db.flush()
    db.add_all([_impact(reference, 2.2), _impact(similar, 2.0), _impact(different, -2.6)])
    db.commit()
    return reference, similar, different


def test_event_fingerprint_creation_and_pattern_matching() -> None:
    db = _session()
    reference, _, _ = _seed(db)

    fingerprint = EventFingerprintBuilder(db).build(reference.id)
    patterns = PatternMatcher(db).match_event(reference.id)

    assert fingerprint is not None
    assert fingerprint.direction == "UP"
    assert fingerprint.price_change_4h == 2.2
    assert db.query(EventFingerprintRecord).filter_by(event_id=reference.id).one()
    assert patterns[0].confidence_score > 0.3
    assert "ETF inflow shock" in PatternMatcher(db).supported_patterns()


def test_similarity_ranking_statistics_replay_evidence_and_operator_override() -> None:
    db = _session()
    reference, similar, _ = _seed(db)

    engine = HistoricalSimilarityEngine(db)
    payload = engine.find_similar_events(reference.id)
    ranked = engine.ranked_results(reference.id)
    replay = engine.replay(reference.id)
    summary = PatternStatisticsService(db).compute("ETF_INFLOW_SHOCK")
    evidence = MarketMemoryEvidenceBuilder(db).build(reference.id)
    review = OperatorReviewService(db).record_review(
        event_id=reference.id,
        pattern="ETF_INFLOW_SHOCK",
        action="approve_pattern_assignment",
        approved=True,
        override_confidence=0.77,
        notes="Reviewed during replay.",
    )

    assert payload["similar_events"][0]["event_id"] == similar.id
    assert ranked[0].similar_event_id == similar.id
    assert replay["final_ranking"][0] == similar.id
    assert summary is not None and summary.occurrences >= 1
    assert evidence.source_events[0]["event_id"] == similar.id
    assert "Historical similarity is not prediction." in evidence.limitations
    assert db.query(MarketMemoryRecord).filter_by(event_id=reference.id).count() >= 1
    assert db.query(PatternStatistics).filter_by(pattern_slug="ETF_INFLOW_SHOCK").one()
    assert db.query(MarketMemoryOperatorReview).filter_by(id=review.id).one().audit_json["operator"] == "system"
