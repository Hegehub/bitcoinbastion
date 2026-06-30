from datetime import datetime, timedelta

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db.base import Base
from app.db.models.attribution_replay_log import AttributionReplayLog
from app.db.models.btc_candle import BTCCandle
from app.db.models.candle_attribution import CandleAttribution
from app.db.models.news_article import NewsArticle  # noqa: F401
from app.db.models.news_event import NewsEvent
from app.db.models.news_source import NewsSource  # noqa: F401
from app.services.intelligence.candle_attribution import CandleAttributionEngine
from app.services.intelligence.candle_attribution.scoring import AttributionScoringService


def _session() -> Session:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    return Session(engine)


def _candle(open_time: datetime) -> BTCCandle:
    return BTCCandle(
        timeframe="1h",
        open_time=open_time,
        close_time=open_time + timedelta(hours=1),
        open=100000.0,
        high=103000.0,
        low=99500.0,
        close=102000.0,
        provider_confidence=0.9,
        provider_count=3,
        is_degraded=False,
    )


def _event(
    seen_at: datetime,
    title: str,
    sentiment: str = "POSITIVE",
    relevance: float = 0.95,
    impact: float = 0.9,
) -> NewsEvent:
    return NewsEvent(
        event_key=title.lower().replace(" ", "-"),
        canonical_title=title,
        canonical_summary=title,
        event_type="institutional",
        event_category="ETF",
        first_seen_at=seen_at,
        last_seen_at=seen_at + timedelta(minutes=2),
        source_count=2,
        article_count=2,
        cluster_confidence=0.85,
        btc_relevance_score=relevance,
        market_impact_score=impact,
        event_sentiment=sentiment,
        event_confidence=0.9,
        provider_confidence=0.9,
        is_high_impact=True,
        is_institutional_related=True,
    )


def test_candle_attribution_discovers_ranks_persists_and_replays_candidates() -> None:
    db = _session()
    open_time = datetime(2026, 5, 28, 12, 0, 0)
    candle = _candle(open_time)
    event = _event(open_time - timedelta(minutes=10), "Bitcoin ETF inflows hit record high")
    db.add_all([candle, event])
    db.commit()

    rows = CandleAttributionEngine(db).attribute_candle(candle.id)
    db.commit()

    assert len(rows) == 1
    assert rows[0].rank == 1
    assert rows[0].confidence_score <= 0.92
    assert rows[0].candidate_category == "ETF"
    assert rows[0].direction_match is True
    assert "Correlation is not proof of causation." in rows[0].limitations_json["limitations"]
    assert db.query(CandleAttribution).count() == 1
    assert db.query(AttributionReplayLog).count() == 1


def test_candle_attribution_time_distance_weight_and_confidence_cap() -> None:
    open_time = datetime(2026, 5, 28, 12, 0, 0)
    candle = _candle(open_time)
    event = _event(open_time, "Bitcoin ETF approval")
    scorer = AttributionScoringService()

    scored = scorer.score_candidate(candle, event)

    assert scored.time_distance_weight == 1.0
    assert scored.confidence_score <= 0.92
    assert scorer.time_distance_weight(90 * 60) < scorer.time_distance_weight(10 * 60)


def test_candle_attribution_no_candidates_generates_replay_when_enabled() -> None:
    db = _session()
    candle = _candle(datetime(2026, 5, 28, 12, 0, 0))
    db.add(candle)
    db.commit()

    rows = CandleAttributionEngine(db).attribute_candle(candle.id)
    db.commit()

    assert rows == []
    replay = db.query(AttributionReplayLog).one()
    assert replay.candidate_event_count == 0
    assert (
        "Correlation is not proof of causation." in replay.explanation_snapshot_json["limitations"]
    )


def test_candle_attribution_stale_event_is_not_selected() -> None:
    db = _session()
    open_time = datetime(2026, 5, 28, 12, 0, 0)
    candle = _candle(open_time)
    stale = _event(open_time - timedelta(hours=10), "Old Bitcoin ETF note")
    db.add_all([candle, stale])
    db.commit()

    rows = CandleAttributionEngine(db).attribute_candle(candle.id)

    assert rows == []
