from collections.abc import Iterator
from datetime import datetime, timedelta

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

import app.db.models  # noqa: F401
from app.api.dependencies import db_session
from app.db.base import Base
from app.db.models.intelligence_timeline import IntelligenceTimelineEvent
from app.db.models.news_event import NewsEvent
from app.db.models.time_utils import utcnow
from app.main import app
from app.services.intelligence.narrative_heatmap import (
    NARRATIVE_LIMITATION,
    NarrativeClassificationService,
    NarrativeHeatmapService,
    NarrativeRotationService,
    NarrativeTrendService,
)


def _session() -> Session:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    return Session(engine)


def _event(title: str, when: datetime, *, impact: float = 0.7, source_count: int = 2) -> NewsEvent:
    return NewsEvent(
        event_key=title.lower().replace(" ", "-"),
        canonical_title=title,
        canonical_summary=title,
        event_type="market",
        event_category="market_structure",
        first_seen_at=when,
        last_seen_at=when + timedelta(minutes=5),
        source_count=source_count,
        article_count=source_count,
        cluster_confidence=0.8,
        btc_relevance_score=0.9,
        market_impact_score=impact,
        event_sentiment="POSITIVE",
        event_confidence=0.8,
        provider_confidence=0.85,
        is_active=True,
    )


def test_narrative_classification_and_multi_tag_matches() -> None:
    db = _session()
    event = _event(
        "Spot Bitcoin ETF inflow accelerates institutional allocation and treasury demand",
        datetime(2026, 5, 31, 12, 0, 0),
    )
    db.add(event)
    db.commit()

    matches = NarrativeClassificationService(db).classify_event(event)
    slugs = {match.narrative.slug for match in matches}

    assert {"etf", "institutional-adoption", "treasury-adoption"}.issubset(slugs)
    assert matches[0].keyword_score >= matches[-1].keyword_score


def test_trend_detection_is_deterministic() -> None:
    trends = NarrativeTrendService()

    assert trends.detect_trend(90.0, 30.0) == "SPIKING"
    assert trends.detect_trend(55.0, 40.0) == "RISING"
    assert trends.detect_trend(20.0, 55.0) == "COOLING"
    assert trends.detect_trend(38.0, 40.0) == "STABLE"


def test_heatmap_dominance_evidence_timeline_and_rotation() -> None:
    db = _session()
    first_time = datetime(2026, 5, 31, 12, 0, 0)
    second_time = datetime(2026, 5, 31, 14, 0, 0)
    db.add(_event("Bitcoin mining difficulty and miner capitulation dominate discussion", first_time - timedelta(minutes=30), impact=0.6))
    db.commit()

    service = NarrativeHeatmapService(db)
    first = service.build_heatmap(window="1h", snapshot_time=first_time)
    db.commit()
    db.add(_event("Spot Bitcoin ETF inflow spikes as BlackRock fund allocation rises", second_time - timedelta(minutes=20), impact=0.95, source_count=4))
    db.commit()
    second = service.build_heatmap(window="1h", snapshot_time=second_time)
    db.commit()

    assert first["top_narratives"]
    assert second["top_narratives"][0]["slug"] == "etf"
    assert second["top_narratives"][0]["dominance_pct"] > 0
    assert second["top_narratives"][0]["evidence"]["top_events"]
    assert NARRATIVE_LIMITATION in second["limitations"]
    assert db.query(IntelligenceTimelineEvent).filter(IntelligenceTimelineEvent.event_type == "NARRATIVE_HEATMAP").count() >= 1

    rotations = NarrativeRotationService(db).detect_rotations()

    assert rotations
    assert rotations[0]["to_narrative"] == "etf"
    assert "may be rotating" in rotations[0]["summary"]


def test_narrative_api_contracts() -> None:
    db = _session()
    now = utcnow()
    db.add(_event("SEC regulation and ETF approval discussion lifts Bitcoin narrative", now - timedelta(minutes=10)))
    db.commit()

    def override_db() -> Iterator[Session]:
        yield db

    app.dependency_overrides[db_session] = override_db
    try:
        client = TestClient(app)
        narratives = client.get("/api/v1/intelligence/narratives")
        heatmap = client.get("/api/v1/intelligence/narratives/heatmap?window=1h")
        top = client.get("/api/v1/intelligence/narratives/top")
        detail = client.get("/api/v1/intelligence/narratives/etf")
        rising = client.get("/api/v1/intelligence/narratives/rising")
        falling = client.get("/api/v1/intelligence/narratives/falling")
        rotations = client.get("/api/v1/intelligence/narratives/rotations")
    finally:
        app.dependency_overrides.clear()

    assert narratives.status_code == 200
    assert any(row["slug"] == "etf" for row in narratives.json()["data"])
    assert heatmap.status_code == 200
    assert heatmap.json()["top_narratives"]
    assert top.status_code == 200
    assert detail.status_code == 200
    assert detail.json()["data"]["slug"] == "etf"
    assert rising.status_code == 200
    assert falling.status_code == 200
    assert rotations.status_code == 200
