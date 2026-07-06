from collections.abc import Iterator
from datetime import datetime, timedelta

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

import app.db.models  # noqa: F401
from app.api.dependencies import db_session
from app.db.base import Base
from app.db.models.historical_similarity_match import HistoricalSimilarityMatch
from app.db.models.news_event import NewsEvent
from app.db.models.news_price_impact import NewsPriceImpact
from app.main import app
from app.services.intelligence.historical_similarity_foundation import (
    DISCLAIMER,
    HistoricalReactionService,
    HistoricalSimilarityService,
)


def _session() -> Session:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    return Session(engine)


def _event(title: str, when: datetime, sentiment: str = "POSITIVE") -> NewsEvent:
    return NewsEvent(
        event_key=title.lower().replace(" ", "-"),
        canonical_title=title,
        canonical_summary=title,
        event_type="institutional",
        event_category="institutional",
        first_seen_at=when,
        last_seen_at=when + timedelta(minutes=5),
        source_count=2,
        article_count=2,
        cluster_confidence=0.85,
        btc_relevance_score=0.9,
        market_impact_score=0.8,
        event_sentiment=sentiment,
        event_confidence=0.8,
        provider_confidence=0.9,
        is_institutional_related=True,
    )


def _impact(event: NewsEvent, change_4h: float) -> NewsPriceImpact:
    return NewsPriceImpact(
        event_id=event.id,
        sentiment_label=event.event_sentiment,
        dominant_window="4h",
        change_15m_pct=change_4h / 4,
        change_1h_pct=change_4h / 2,
        change_4h_pct=change_4h,
        change_24h_pct=change_4h * 1.2,
        btc_relevance_score=event.btc_relevance_score,
        market_impact_score=event.market_impact_score,
        impact_confidence_score=0.8,
        provider_confidence=0.9,
    )


def _seed(db: Session) -> tuple[NewsEvent, NewsEvent, NewsEvent]:
    now = datetime(2026, 5, 31, 12, 0, 0)
    current = _event("Bitcoin ETF inflow shock lifts institutional demand", now)
    similar = _event("Bitcoin ETF inflow shock returns as funds buy BTC", now - timedelta(days=40))
    different = _event(
        "Exchange hack triggers security vulnerability concerns",
        now - timedelta(days=70),
        "NEGATIVE",
    )
    different.event_type = "security"
    different.event_category = "security"
    different.is_institutional_related = False
    different.is_security_related = True
    db.add_all([current, similar, different])
    db.flush()
    db.add_all([_impact(current, 2.2), _impact(similar, 2.0), _impact(different, -2.8)])
    db.commit()
    return current, similar, different


def test_pattern_library_seed_and_reaction_profile_generation() -> None:
    db = _session()
    current, _, _ = _seed(db)
    service = HistoricalSimilarityService(db)

    patterns = service.ensure_patterns()
    profile = HistoricalReactionService(db).build_reaction_profile(current.id)

    assert {pattern.slug for pattern in patterns} >= {"ETF_INFLOW_SHOCK", "SECURITY_VULNERABILITY"}
    assert profile is not None
    assert profile.reaction_4h_pct == 2.2
    assert profile.max_positive_move_pct == 2.64
    assert profile.max_negative_move_pct == 0.55
    assert profile.confidence_score > 0.7


def test_similarity_scoring_and_persistence_with_limitations() -> None:
    db = _session()
    current, similar, different = _seed(db)

    report = HistoricalSimilarityService(db).find_similar_events(current.id)
    db.commit()

    assert report["similar_events"][0]["event_id"] == similar.id
    assert (
        report["similar_events"][0]["similarity_score"]
        > report["similar_events"][1]["similarity_score"]
    )
    assert report["similar_events"][1]["event_id"] == different.id
    assert DISCLAIMER in report["limitations"]
    assert "Evidence Packet" in report["evidence"]["attachable_to"]
    assert (
        db.query(HistoricalSimilarityMatch)
        .filter(HistoricalSimilarityMatch.event_id == current.id)
        .count()
        == 2
    )


def test_empty_history_single_match_and_api_responses() -> None:
    db = _session()
    current, similar, different = _seed(db)
    db.delete(different)
    db.commit()

    def override_db() -> Iterator[Session]:
        yield db

    app.dependency_overrides[db_session] = override_db
    try:
        client = TestClient(app)
        response = client.get(f"/api/v1/intelligence/similar-events/{current.id}")
        profile = client.get(f"/api/v1/intelligence/reaction-profile/{similar.id}")
        missing = client.get("/api/v1/intelligence/similar-events/999999")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["similar_events"][0]["event_id"] == similar.id
    assert response.json()["median_reaction"]["reaction_4h_pct"] == 2.0
    assert profile.status_code == 200
    assert profile.json()["data"]["reaction_4h_pct"] == 2.0
    assert missing.status_code == 200
    assert "Limited historical sample." in missing.json()["limitations"]
