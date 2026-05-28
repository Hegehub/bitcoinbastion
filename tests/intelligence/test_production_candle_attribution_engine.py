from datetime import datetime, timedelta

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db.base import Base
from app.db.models.attribution_context_snapshot import AttributionContextSnapshot
from app.db.models.attribution_replay_log import AttributionReplayLog
from app.db.models.btc_candle import BTCCandle
from app.db.models.candle_attribution_candidate import CandleAttributionCandidate
from app.db.models.news_article import NewsArticle  # noqa: F401
from app.db.models.news_event import NewsEvent
from app.db.models.news_source import NewsSource  # noqa: F401
from app.services.intelligence.candle_attribution_engine import CandleAttributionEngine


def _session() -> Session:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    return Session(engine)


def _candle(open_time: datetime, close: float = 102000.0) -> BTCCandle:
    return BTCCandle(
        timeframe="1h",
        open_time=open_time,
        close_time=open_time + timedelta(hours=1),
        open=100000.0,
        high=max(103000.0, close),
        low=99500.0,
        close=close,
        provider_confidence=0.9,
        provider_count=3,
        provider_disagreement_score=0.05,
        is_degraded=False,
        volatility_score=0.2,
        market_regime="normal",
    )


def _event(seen_at: datetime, title: str, sentiment: str = "POSITIVE", impact: float = 0.9) -> NewsEvent:
    return NewsEvent(
        event_key=title.lower().replace(" ", "-"),
        canonical_title=title,
        canonical_summary=title,
        event_type="institutional_etf",
        event_category="ETF",
        first_seen_at=seen_at,
        last_seen_at=seen_at + timedelta(minutes=2),
        source_count=2,
        article_count=2,
        cluster_confidence=0.85,
        btc_relevance_score=0.95,
        market_impact_score=impact,
        event_sentiment=sentiment,
        event_confidence=0.9,
        provider_confidence=0.9,
        is_high_impact=True,
        is_institutional_related=True,
    )


def test_production_engine_persists_ranked_candidates_context_and_evidence() -> None:
    db = _session()
    open_time = datetime(2026, 5, 28, 12, 0, 0)
    candle = _candle(open_time)
    near = _event(open_time - timedelta(minutes=5), "Bitcoin ETF inflows hit record high")
    far = _event(open_time - timedelta(hours=3), "Bitcoin treasury adoption expands", impact=0.7)
    db.add_all([candle, near, far])
    db.commit()

    rows = CandleAttributionEngine(db).attribute_candle(candle.id)
    db.commit()

    assert len(rows) == 2
    assert rows[0].candidate_rank == 1
    assert rows[0].is_primary_candidate is True
    assert rows[0].confidence_band in {"LOW", "MEDIUM", "HIGH", "VERY_HIGH"}
    assert "score_contributions" in rows[0].evidence_refs_json
    assert "Correlation is not proof of causation." in rows[0].limitations_json["limitations"]
    assert db.query(CandleAttributionCandidate).count() == 2
    assert db.query(AttributionContextSnapshot).count() == 1
    assert db.query(AttributionReplayLog).count() == 1


def test_time_decay_ranks_closer_candidate_first() -> None:
    db = _session()
    open_time = datetime(2026, 5, 28, 12, 0, 0)
    candle = _candle(open_time)
    stale = _event(open_time - timedelta(hours=3), "Older Bitcoin ETF note")
    fresh = _event(open_time - timedelta(minutes=3), "Fresh Bitcoin ETF note")
    db.add_all([candle, stale, fresh])
    db.commit()

    rows = CandleAttributionEngine(db).attribute_candle(candle.id)

    assert rows[0].event_id == fresh.id
    assert rows[0].freshness_weight > rows[1].freshness_weight


def test_direction_mismatch_reduces_but_does_not_zero_confidence() -> None:
    db = _session()
    open_time = datetime(2026, 5, 28, 12, 0, 0)
    candle = _candle(open_time, close=98000.0)
    event = _event(open_time - timedelta(minutes=5), "Positive Bitcoin ETF launch", sentiment="POSITIVE")
    db.add_all([candle, event])
    db.commit()

    row = CandleAttributionEngine(db).attribute_candle(candle.id)[0]

    assert row.sentiment_direction_match == "mismatch"
    assert row.confidence_score > 0.0
    assert "News sentiment and candle direction were conflicting." in row.limitations_json["limitations"]


def test_provider_disagreement_and_operator_review_hooks() -> None:
    db = _session()
    open_time = datetime(2026, 5, 28, 12, 0, 0)
    candle = _candle(open_time)
    candle.provider_disagreement_score = 0.4
    candle.provider_confidence = 0.45
    event = _event(open_time - timedelta(minutes=5), "Bitcoin security shock", sentiment="NEGATIVE")
    db.add_all([candle, event])
    db.commit()

    engine = CandleAttributionEngine(db)
    row = engine.attribute_candle(candle.id)[0]
    reviewed = engine.review_attribution(row.id, "downgraded", "operator found competing macro event")

    assert "Provider disagreement reduced attribution certainty." in row.limitations_json["limitations"]
    assert reviewed is not None
    assert reviewed.is_operator_reviewed is True
    assert reviewed.operator_review_status == "downgraded"
    assert reviewed.operator_note == "operator found competing macro event"


def test_explain_candle_returns_frontend_ready_payload() -> None:
    db = _session()
    open_time = datetime(2026, 5, 28, 12, 0, 0)
    candle = _candle(open_time)
    event = _event(open_time - timedelta(minutes=5), "Bitcoin ETF inflows surge")
    db.add_all([candle, event])
    db.commit()

    payload = CandleAttributionEngine(db).explain_candle(candle.id)

    assert payload["candle"]["chart_marker"]["has_attribution"] is True
    assert payload["ranked_candidate_events"]
    assert payload["side_panel"]["candidate_count"] == 1
    assert payload["evidence_drawer"]["items"]
