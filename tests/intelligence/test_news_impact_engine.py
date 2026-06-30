from datetime import datetime, timedelta

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db.base import Base
from app.db.models.btc_candle import BTCCandle
from app.db.models.impact_confidence_breakdown import ImpactConfidenceBreakdown
from app.db.models.impact_window_snapshot import ImpactWindowSnapshot
from app.db.models.news_article import NewsArticle
from app.db.models.news_event import NewsEvent
from app.db.models.news_source import NewsSource
from app.services.intelligence.news_impact_engine import NewsImpactEngine


def _db() -> Session:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    return Session(engine)


def _source(db: Session) -> NewsSource:
    src = NewsSource(
        name="Impact Source",
        slug="impact-source",
        kind="RSS",
        base_url="https://impact.example",
        category="markets",
        tier="MARKET_MEDIA",
    )
    db.add(src)
    db.flush()
    return src


def _article(
    db: Session, src: NewsSource, sentiment: str = "POSITIVE", published_at: datetime | None = None
) -> NewsArticle:
    published_at = published_at or datetime(2026, 5, 28, 12, 0, 0)
    article = NewsArticle(
        source_id=src.id,
        title="Bitcoin ETF approval inflow",
        normalized_title="bitcoin etf approval inflow",
        raw_url=f"https://impact.example/{sentiment.lower()}",
        url=f"https://impact.example/{sentiment.lower()}",
        canonical_url=f"https://impact.example/{sentiment.lower()}",
        url_hash=f"url-{sentiment}",
        canonical_url_hash=f"canonical-{sentiment}",
        title_hash=f"title-{sentiment}",
        content_hash=f"content-{sentiment}",
        published_at=published_at,
        sentiment_label=sentiment,
        provider_confidence=0.9,
        credibility_score=0.85,
        btc_relevance_score=0.95,
        market_impact_score=0.9,
    )
    db.add(article)
    db.flush()
    return article


def _candle(
    open_time: datetime, price: float, provider_count: int = 3, volatility: float = 0.1
) -> BTCCandle:
    return BTCCandle(
        timeframe="1m",
        open_time=open_time,
        close_time=open_time + timedelta(minutes=1),
        open=price,
        high=price * 1.001,
        low=price * 0.999,
        close=price,
        provider_count=provider_count,
        provider_confidence=0.9 if provider_count > 1 else 0.3,
        volatility_score=volatility,
        is_degraded=provider_count <= 1,
    )


def _add_price_windows(
    db: Session,
    start: datetime,
    prices: dict[int, float],
    provider_count: int = 3,
    volatility: float = 0.1,
) -> None:
    for minutes, price in prices.items():
        db.add(
            _candle(
                start + timedelta(minutes=minutes),
                price,
                provider_count=provider_count,
                volatility=volatility,
            )
        )
    db.flush()


def test_positive_sentiment_positive_move_persists_windows_and_breakdown() -> None:
    db = _db()
    src = _source(db)
    article = _article(db, src)
    _add_price_windows(
        db, article.published_at, {0: 100000, 15: 101000, 60: 103000, 240: 102000, 1440: 101500}
    )

    impact = NewsImpactEngine().calculate_article_impact(db, article.id)
    db.commit()

    assert impact is not None
    assert impact.direction_match == "true"
    assert impact.dominant_window in {"1h", "4h", "24h", "15m"}
    assert 0.0 <= impact.impact_confidence_score <= 1.0
    assert impact.price_at_publish == 100000
    assert "correlation_not_causation" in impact.limitations_json["limitations"]
    assert db.query(ImpactWindowSnapshot).count() == 4
    assert db.query(ImpactConfidenceBreakdown).count() == 1


def test_negative_sentiment_down_move_matches_direction() -> None:
    db = _db()
    src = _source(db)
    article = _article(db, src, sentiment="NEGATIVE")
    _add_price_windows(
        db, article.published_at, {0: 100000, 15: 99000, 60: 97000, 240: 98000, 1440: 98500}
    )

    impact = NewsImpactEngine().calculate_article_impact(db, article.id)

    assert impact is not None
    assert impact.direction_match == "true"
    assert impact.actual_direction == "DOWN"


def test_direction_mismatch_and_partial_flat_move() -> None:
    db = _db()
    src = _source(db)
    mismatch = _article(db, src, sentiment="POSITIVE")
    _add_price_windows(
        db, mismatch.published_at, {0: 100000, 15: 99900, 60: 99000, 240: 99500, 1440: 99600}
    )

    impact = NewsImpactEngine().calculate_article_impact(db, mismatch.id)
    assert impact is not None
    assert impact.direction_match == "false"

    assert NewsImpactEngine().calculate_direction_match("POSITIVE", "FLAT", 0.01) == "partial"


def test_degraded_missing_candles_lower_confidence_and_emit_limitations() -> None:
    db = _db()
    src = _source(db)
    article = _article(db, src)
    _add_price_windows(
        db, article.published_at, {0: 100000, 15: 100800}, provider_count=1, volatility=0.8
    )

    impact = NewsImpactEngine().calculate_article_impact(db, article.id)

    assert impact is not None
    limitations = impact.limitations_json["limitations"]
    assert "insufficient_price_data" in limitations
    assert "low_provider_confidence" in limitations
    assert "high_market_volatility" in limitations
    assert impact.provider_confidence < 0.5


def test_event_level_impact_uses_event_scores_and_is_idempotent() -> None:
    db = _db()
    start = datetime(2026, 5, 28, 12, 0, 0)
    event = NewsEvent(
        event_key="etf-flow",
        canonical_title="Bitcoin ETF flow confirmed by multiple sources",
        canonical_summary="Bitcoin ETF flow confirmed",
        event_type="institutional",
        event_category="ETF",
        first_seen_at=start,
        last_seen_at=start + timedelta(minutes=5),
        source_count=4,
        article_count=3,
        cluster_confidence=0.85,
        btc_relevance_score=0.95,
        market_impact_score=0.9,
        event_sentiment="POSITIVE",
        event_confidence=0.9,
        provider_confidence=0.9,
    )
    db.add(event)
    db.flush()
    _add_price_windows(db, start, {0: 100000, 15: 100600, 60: 101500, 240: 101000, 1440: 100500})

    first = NewsImpactEngine().calculate_event_impact(db, event.id)
    second = NewsImpactEngine().calculate_event_impact(db, event.id)
    db.commit()

    assert first is not None and second is not None
    assert first.id == second.id
    assert db.query(ImpactWindowSnapshot).count() == 4
    assert second.source_credibility_score > 0.85
