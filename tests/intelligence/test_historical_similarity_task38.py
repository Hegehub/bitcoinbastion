from datetime import datetime, timedelta

from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

import app.db.models  # noqa: F401
from app.db.base import Base
from app.db.models.event_pattern_match import EventPatternMatch
from app.db.models.market_pattern import MarketPattern
from app.db.models.news_event import NewsEvent
from app.db.models.news_price_impact import NewsPriceImpact
from app.db.models.pattern_occurrence import PatternOccurrence
from app.db.models.pattern_reaction_snapshot import PatternReactionSnapshot
from app.services.intelligence.historical_similarity_service import HistoricalSimilarityService
from app.services.intelligence.market_memory_service import MarketMemoryService
from app.services.intelligence.pattern_confidence_service import PatternConfidenceService


def _session() -> Session:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    return Session(engine)


def _event(title: str, seen_at: datetime, sentiment: str = "POSITIVE") -> NewsEvent:
    return NewsEvent(
        event_key=title.lower().replace(" ", "-"),
        canonical_title=title,
        canonical_summary=title,
        event_type="institutional",
        event_category="institutional",
        first_seen_at=seen_at,
        last_seen_at=seen_at + timedelta(minutes=5),
        source_count=3,
        article_count=2,
        btc_relevance_score=0.9,
        market_impact_score=0.8,
        event_sentiment=sentiment,
        event_confidence=0.82,
        provider_confidence=0.9,
        is_institutional_related=True,
    )


def _impact(event_id: int, move: float) -> NewsPriceImpact:
    return NewsPriceImpact(
        event_id=event_id,
        sentiment_label="POSITIVE" if move >= 0 else "NEGATIVE",
        expected_direction="UP" if move >= 0 else "DOWN",
        actual_direction="UP" if move >= 0 else "DOWN",
        btc_relevance_score=0.9,
        market_impact_score=0.8,
        provider_confidence=0.9,
        impact_confidence_score=0.8,
        dominant_window="4h",
        change_15m_pct=move / 4,
        change_1h_pct=move / 2,
        change_4h_pct=move,
        change_24h_pct=move + 0.3,
    )


def test_task38_pattern_library_context_occurrences_and_confidence() -> None:
    db = _session()
    now = datetime(2026, 6, 3, 12, 0, 0)
    reference = _event("Bitcoin ETF inflow shock hits record", now)
    analog = _event("Bitcoin ETF inflow shock repeats", now - timedelta(days=30))
    db.add_all([reference, analog])
    db.flush()
    db.add_all([_impact(reference.id, 2.0), _impact(analog.id, 2.2)])
    db.commit()

    patterns = MarketMemoryService(db).ensure_patterns()
    pattern_codes = {pattern.slug for pattern in patterns}
    assert {
        "ETF_INFLOW_SHOCK",
        "SEC_APPROVAL",
        "RATE_CUT_SIGNAL",
        "RATE_HIKE_SIGNAL",
        "PRIVATE_KEY_LEAK",
        "LIQUIDATION_CASCADE",
        "VOLATILITY_EXPANSION",
    }.issubset(pattern_codes)

    context = HistoricalSimilarityService(db).build_historical_context(reference.id)
    assert context["similarity_band"] in {"VERY_HIGH", "HIGH", "MEDIUM", "LOW", "VERY_LOW"}
    assert context["historical_matches"]
    assert "historical_similarity_not_prediction" in context["limitations"]
    assert "correlation_not_causation" in context["limitations"]
    assert "evidence_based" in context["safety"]
    assert db.query(PatternOccurrence).count() >= 1
    assert db.query(PatternReactionSnapshot).count() >= 1

    etf = db.query(MarketPattern).filter_by(slug="ETF_INFLOW_SHOCK").one()
    db.add(
        EventPatternMatch(
            event_id=reference.id,
            pattern_id=etf.id,
            classification_confidence=0.86,
            reasons_json=[],
        )
    )
    db.add(
        EventPatternMatch(
            event_id=analog.id, pattern_id=etf.id, classification_confidence=0.84, reasons_json=[]
        )
    )
    db.commit()
    breakdown = PatternConfidenceService(db).calculate(etf.id).as_dict()
    assert breakdown["score"] > 0.0
    assert set(breakdown) >= {
        "sample_size",
        "source_diversity",
        "market_regime_diversity",
        "reaction_consistency",
        "provider_confidence",
        "event_freshness",
    }
