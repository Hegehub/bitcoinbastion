from datetime import datetime, timedelta

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.api.dependencies import db_session
from app.db.base import Base
from app.db.models.btc_candle import BTCCandle
from app.db.models.candle_attribution import CandleAttribution
from app.db.models.historical_similarity_result import HistoricalSimilarityResult
from app.db.models.news_article import NewsArticle  # noqa: F401
from app.db.models.news_event import NewsEvent
from app.db.models.news_source import NewsSource  # noqa: F401
from app.main import app
from app.services.intelligence.candle_attribution_ranking import CandleAttributionRankingEngine


def _session() -> Session:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    return Session(engine)


def _candle(
    open_time: datetime, close: float = 102000.0, provider_confidence: float = 0.9
) -> BTCCandle:
    return BTCCandle(
        timeframe="1h",
        open_time=open_time,
        close_time=open_time + timedelta(hours=1),
        open=100000.0,
        high=max(103000.0, close),
        low=min(99500.0, close),
        close=close,
        provider_confidence=provider_confidence,
        provider_count=3,
        provider_disagreement_score=0.04,
        is_degraded=provider_confidence < 0.5,
        volatility_score=0.2,
        market_regime="normal",
    )


def _event(
    seen_at: datetime,
    title: str,
    sentiment: str = "POSITIVE",
    source_count: int = 3,
    impact: float = 0.9,
    confidence: float = 0.9,
) -> NewsEvent:
    return NewsEvent(
        event_key=title.lower().replace(" ", "-"),
        canonical_title=title,
        canonical_summary=title,
        event_type="institutional_etf",
        event_category="ETF",
        first_seen_at=seen_at,
        last_seen_at=seen_at + timedelta(minutes=2),
        source_count=source_count,
        article_count=source_count,
        cluster_confidence=confidence,
        btc_relevance_score=0.95,
        market_impact_score=impact,
        event_sentiment=sentiment,
        event_confidence=confidence,
        provider_confidence=confidence,
        is_high_impact=True,
        is_institutional_related=True,
    )


def test_single_candidate_ranking_persists_score_explanation_and_limitations() -> None:
    db = _session()
    open_time = datetime(2026, 5, 30, 12, 0, 0)
    candle = _candle(open_time)
    event = _event(open_time - timedelta(minutes=17), "Bitcoin ETF inflow shock")
    db.add_all([candle, event])
    db.commit()

    payload = CandleAttributionRankingEngine(db).attribute_candle(candle.id)
    db.commit()

    row = db.query(CandleAttribution).one()
    assert payload["candidate_events"][0]["rank"] == 1
    assert row.rank == 1
    assert row.sentiment_direction_match == "strong_match"
    assert row.confidence_band in {"LOW", "MEDIUM", "HIGH"}
    assert "factor_contributions" in row.explanation_json
    assert (
        "Correlation-based attribution. Not proof of causation."
        in row.limitations_json["limitations"]
    )


def test_multiple_candidates_rank_by_time_proximity_and_summary_mentions_combination() -> None:
    db = _session()
    open_time = datetime(2026, 5, 30, 12, 0, 0)
    candle = _candle(open_time)
    stale = _event(open_time - timedelta(hours=3), "Older Bitcoin ETF note")
    fresh = _event(open_time - timedelta(minutes=5), "Fresh Bitcoin ETF note")
    inside = _event(open_time + timedelta(minutes=10), "Inside candle ETF update", impact=0.7)
    db.add_all([candle, stale, fresh, inside])
    db.commit()

    payload = CandleAttributionRankingEngine(db).attribute_candle(candle.id)

    assert payload["candidate_events"][0]["event_id"] in {fresh.id, inside.id}
    assert len(payload["candidate_events"]) == 3
    assert "Likely combination" in payload["summary"]


def test_contradictory_direction_lowers_but_preserves_confidence() -> None:
    db = _session()
    open_time = datetime(2026, 5, 30, 12, 0, 0)
    candle = _candle(open_time, close=98000.0)
    event = _event(open_time - timedelta(minutes=5), "Positive ETF approval", sentiment="POSITIVE")
    db.add_all([candle, event])
    db.commit()

    payload = CandleAttributionRankingEngine(db).attribute_candle(candle.id)

    candidate = payload["candidate_events"][0]
    assert candidate["direction_match"] == "contradictory"
    assert candidate["confidence"] > 0.0
    assert "event sentiment contradicted the candle direction" in candidate["limitations"]


def test_provider_degradation_low_source_confidence_and_historical_bonus() -> None:
    db = _session()
    open_time = datetime(2026, 5, 30, 12, 0, 0)
    candle = _candle(open_time, provider_confidence=0.4)
    weak = _event(
        open_time - timedelta(minutes=8), "Single source ETF rumor", source_count=1, confidence=0.35
    )
    supported = _event(
        open_time - timedelta(minutes=9), "Supported ETF inflow analog", confidence=0.85
    )
    db.add_all([candle, weak, supported])
    db.flush()
    db.add(
        HistoricalSimilarityResult(
            reference_event_id=supported.id, candidate_event_id=weak.id, similarity_score=0.88
        )
    )
    db.commit()

    payload = CandleAttributionRankingEngine(db).attribute_candle(candle.id)
    supported_payload = next(
        item for item in payload["candidate_events"] if item["event_id"] == supported.id
    )
    weak_payload = next(item for item in payload["candidate_events"] if item["event_id"] == weak.id)

    assert supported_payload["explanation"]["factor_scores"]["historical_pattern_support"] >= 0.88
    assert "provider degradation" in payload["limitations"]
    assert "low source confidence" in weak_payload["limitations"]


def test_candle_attribution_api_returns_ranking_payload() -> None:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    open_time = datetime(2026, 5, 30, 12, 0, 0)
    with Session(engine) as session:
        candle = _candle(open_time)
        event = _event(open_time - timedelta(minutes=6), "API Bitcoin ETF inflow")
        session.add_all([candle, event])
        session.commit()
        candle_id = candle.id

    def override_db() -> Session:
        with Session(engine) as session:
            yield session

    app.dependency_overrides[db_session] = override_db
    try:
        client = TestClient(app, raise_server_exceptions=False)
        response = client.get(f"/api/v1/intelligence/candles/{candle_id}/attribution")
        payload = response.json()
        assert response.status_code == 200
        assert payload["candidate_events"]
        assert payload["ranking"]
        assert payload["confidence"] == payload["candidate_events"][0]["confidence"]
    finally:
        app.dependency_overrides.clear()
