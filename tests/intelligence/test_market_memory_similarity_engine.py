from collections.abc import Iterator
from datetime import datetime, timedelta

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

import app.db.models  # noqa: F401
from app.api.dependencies import db_session
from app.db.base import Base
from app.db.models.event_pattern_match import EventPatternMatch
from app.db.models.historical_event_similarity import HistoricalEventSimilarity
from app.db.models.news_event import NewsEvent
from app.db.models.news_price_impact import NewsPriceImpact
from app.main import app
from app.services.intelligence.historical_confidence_calibrator import (
    HistoricalConfidenceCalibrator,
)
from app.services.intelligence.historical_similarity_engine import HistoricalSimilarityEngine
from app.services.intelligence.market_memory_service import MarketMemoryService
from app.services.intelligence.pattern_classification_service import PatternClassificationService


def _session() -> Session:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    return Session(engine)


def _event(
    title: str,
    *,
    seen_at: datetime,
    sentiment: str = "POSITIVE",
    event_type: str = "institutional",
    category: str = "institutional",
    btc_relevance: float = 0.9,
    impact: float = 0.8,
    provider_confidence: float = 0.9,
    source_count: int = 3,
) -> NewsEvent:
    return NewsEvent(
        event_key=title.lower().replace(" ", "-"),
        canonical_title=title,
        canonical_summary=title,
        event_type=event_type,
        event_category=category,
        first_seen_at=seen_at,
        last_seen_at=seen_at + timedelta(minutes=5),
        source_count=source_count,
        article_count=source_count,
        cluster_confidence=0.86,
        btc_relevance_score=btc_relevance,
        market_impact_score=impact,
        event_sentiment=sentiment,
        event_confidence=0.82,
        is_high_impact=impact >= 0.7,
        is_institutional_related=category == "institutional",
        is_security_related=category == "security",
        is_regulatory_related=category == "regulatory",
        is_macro_related=category == "macro",
        provider_confidence=provider_confidence,
    )


def _impact(
    event: NewsEvent,
    *,
    change_15m: float,
    change_1h: float,
    change_4h: float,
    change_24h: float,
    volatility: float = 0.25,
    provider_confidence: float = 0.9,
) -> NewsPriceImpact:
    return NewsPriceImpact(
        event_id=event.id,
        sentiment_label=event.event_sentiment,
        expected_direction="UP" if event.event_sentiment == "POSITIVE" else "DOWN",
        actual_direction="UP" if change_4h >= 0 else "DOWN",
        btc_relevance_score=event.btc_relevance_score,
        market_impact_score=event.market_impact_score,
        provider_confidence=provider_confidence,
        impact_confidence_score=event.event_confidence,
        dominant_window="4h",
        volatility_context=volatility,
        change_15m_pct=change_15m,
        change_1h_pct=change_1h,
        change_4h_pct=change_4h,
        change_24h_pct=change_24h,
    )


def _seed_similarity_dataset(db: Session) -> tuple[NewsEvent, NewsEvent, NewsEvent]:
    now = datetime(2026, 5, 30, 12, 0, 0)
    reference = _event("Bitcoin ETF inflow shock accelerates institutional demand", seen_at=now)
    analog = _event(
        "Bitcoin ETF inflows surge as institutional demand returns",
        seen_at=now - timedelta(days=20),
    )
    different = _event(
        "Exchange hack sparks custody failure concerns",
        seen_at=now - timedelta(days=30),
        sentiment="NEGATIVE",
        event_type="security",
        category="security",
        impact=0.7,
        provider_confidence=0.55,
        source_count=1,
    )
    db.add_all([reference, analog, different])
    db.flush()
    db.add_all(
        [
            _impact(reference, change_15m=0.4, change_1h=1.1, change_4h=2.2, change_24h=2.7),
            _impact(analog, change_15m=0.5, change_1h=1.0, change_4h=2.0, change_24h=2.5),
            _impact(
                different,
                change_15m=-0.8,
                change_1h=-1.4,
                change_4h=-2.6,
                change_24h=-3.2,
                volatility=0.7,
            ),
        ]
    )
    db.commit()
    return reference, analog, different


def test_pattern_classification_supports_ranked_multi_pattern_matches() -> None:
    db = _session()
    event = _event(
        "SEC approval clears Bitcoin ETF inflow shock",
        seen_at=datetime(2026, 5, 30, 12, 0, 0),
        category="regulatory",
    )
    db.add(event)
    db.commit()

    candidates = MarketMemoryService(db).classify_event(event)
    slugs = {candidate.pattern.slug for candidate in candidates}

    assert "ETF_INFLOW_SHOCK" in slugs
    assert "SEC_APPROVAL" in slugs
    assert candidates[0].confidence >= candidates[-1].confidence
    assert db.query(EventPatternMatch).filter(EventPatternMatch.event_id == event.id).count() >= 2


def test_pattern_classification_service_exposes_production_pattern_evidence() -> None:
    db = _session()
    event = _event(
        "Lightning adoption expands Bitcoin payment routing",
        seen_at=datetime(2026, 5, 30, 12, 0, 0),
        category="protocol",
        event_type="protocol",
        sentiment="NEUTRAL",
    )
    db.add(event)
    db.commit()

    evidence = PatternClassificationService(db).classify_market_patterns(event)

    assert evidence[0]["pattern_slug"] == "LIGHTNING_ADOPTION"
    assert evidence[0]["confidence"] > 0.3


def test_similarity_score_ranks_same_pattern_above_security_shock_and_persists_replayable_rows() -> (
    None
):
    db = _session()
    reference, analog, different = _seed_similarity_dataset(db)

    report = HistoricalSimilarityEngine(db).find_similar_events(reference.id, limit=10)
    db.commit()

    assert report["similar_events"][0]["event_id"] == analog.id
    assert (
        report["similar_events"][0]["similarity_score"]
        > report["similar_events"][1]["similarity_score"]
    )
    assert report["similar_events"][1]["event_id"] == different.id
    assert (
        "Historical similarity does not guarantee future market behavior." in report["limitations"]
    )
    assert (
        db.query(HistoricalEventSimilarity)
        .filter(HistoricalEventSimilarity.event_id == reference.id)
        .count()
        == 2
    )


def test_reaction_profile_generation_calculates_medians_and_confidence() -> None:
    db = _session()
    reference, analog, _ = _seed_similarity_dataset(db)
    memory = MarketMemoryService(db)
    memory.classify_event(reference)
    memory.classify_event(analog)
    pattern = memory.get_pattern("ETF_INFLOW_SHOCK")
    assert pattern is not None

    profile = memory.generate_reaction_profile(pattern)

    assert profile.sample_size == 2
    assert profile.median_change_4h == 2.1
    assert profile.average_change_1h == 1.05
    assert profile.confidence_score > 0.4


def test_confidence_calibration_handles_small_samples_and_provider_disagreement() -> None:
    calibrator = HistoricalConfidenceCalibrator()

    strong = calibrator.calibrate(
        base_confidence=0.7, sample_size=25, consistency_score=0.9, provider_confidence=0.9
    )
    weak = calibrator.calibrate(
        base_confidence=0.7, sample_size=1, consistency_score=0.3, provider_confidence=0.4
    )

    assert strong.confidence > weak.confidence
    assert any("small historical sample" in limitation for limitation in weak.limitations)
    assert any("provider confidence" in limitation for limitation in weak.limitations)


def test_empty_history_and_missing_event_return_limitations() -> None:
    db = _session()

    missing = HistoricalSimilarityEngine(db).find_similar_events(999)

    assert missing["sample_size"] == 0
    assert "reference_event_not_found" in missing["limitations"]


def test_similarity_replay_is_deterministic() -> None:
    db = _session()
    reference, _, _ = _seed_similarity_dataset(db)
    engine = HistoricalSimilarityEngine(db)

    first = engine.find_similar_events(reference.id, limit=10)
    second = engine.find_similar_events(reference.id, limit=10)
    db.commit()

    assert [row["event_id"] for row in first["similar_events"]] == [
        row["event_id"] for row in second["similar_events"]
    ]
    assert (
        db.query(HistoricalEventSimilarity)
        .filter(HistoricalEventSimilarity.event_id == reference.id)
        .count()
        == 2
    )


def test_market_memory_api_endpoints() -> None:
    db = _session()
    reference, _, _ = _seed_similarity_dataset(db)

    def override_db() -> Iterator[Session]:
        yield db

    app.dependency_overrides[db_session] = override_db
    try:
        client = TestClient(app)
        similarity = client.get(f"/api/v1/intelligence/events/{reference.id}/similar")
        patterns = client.get("/api/v1/intelligence/patterns")
        pattern = client.get("/api/v1/intelligence/patterns/ETF_INFLOW_SHOCK")
        history = client.get("/api/v1/intelligence/patterns/ETF_INFLOW_SHOCK/history")
        profile = client.get("/api/v1/intelligence/patterns/ETF_INFLOW_SHOCK/reaction-profile")
        memory = client.get(f"/api/v1/intelligence/events/{reference.id}/memory")
    finally:
        app.dependency_overrides.clear()

    assert similarity.status_code == 200
    assert similarity.json()["sample_size"] == 2
    assert patterns.status_code == 200
    assert len(patterns.json()["data"]) >= 22
    assert pattern.status_code == 200
    assert pattern.json()["data"]["slug"] == "ETF_INFLOW_SHOCK"
    assert history.status_code == 200
    assert isinstance(history.json()["data"], list)
    assert profile.status_code == 200
    assert profile.json()["data"]["sample_size"] >= 1
    assert memory.status_code == 200
    assert "pattern_matches" in memory.json()
