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
from app.db.models.narrative_observation import NarrativeObservation
from app.db.models.narrative_snapshot import NarrativeSnapshot
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


def test_bmtm33_taxonomy_classifier_observations_and_heat_scores() -> None:
    db = _session()
    now = datetime(2026, 5, 31, 15, 0, 0)
    etf = _event("Spot Bitcoin ETF inflow drives institutional adoption", now, impact=0.9)
    fed = _event("Fed rate cut improves macro liquidity for Bitcoin", now, impact=0.7)
    lightning = _event("Lightning layer 2 payment channel growth accelerates", now, impact=0.4)
    db.add_all([etf, fed, lightning])
    db.commit()

    classifier = NarrativeClassificationService(db)
    etf_obs = classifier.observe_event(etf)
    fed_types = {match.narrative.narrative_type for match in classifier.classify_event(fed)}
    lightning_types = {match.narrative.narrative_type for match in classifier.classify_event(lightning)}

    assert {row.narrative_type for row in etf_obs} >= {"ETF", "INSTITUTIONAL_ADOPTION"}
    assert {"MACRO", "FED", "LIQUIDITY"}.issubset(fed_types)
    assert {"LIGHTNING", "LAYER2"}.issubset(lightning_types)

    heatmap = NarrativeHeatmapService(db).build_heatmap(window="1h", snapshot_time=now + timedelta(minutes=5))
    db.commit()

    top = heatmap["top_narratives"][0]
    assert 0 <= top["heat_score"] <= 100
    assert top["heat_band"] in {"Quiet", "Emerging", "Active", "Dominant", "Major Narrative"}
    assert top["volume_score"] > 0
    assert top["velocity_score"] >= 0
    assert top["dominance_score"] >= 0
    assert top["supporting_events_count"] >= 1
    assert isinstance(top["supporting_events"], list)
    assert "dominance_index" in heatmap

    snapshot = db.query(NarrativeSnapshot).filter(NarrativeSnapshot.heat_score == top["heat_score"]).first()
    observation = db.query(NarrativeObservation).first()

    assert snapshot is not None
    assert snapshot.velocity_score >= 0
    assert snapshot.dominance_score >= 0
    assert snapshot.supporting_events_count >= 1
    assert observation is not None
    assert observation.narrative_id is not None
    assert observation.observation_time is not None
    assert observation.strength_score > 0
    assert observation.relevance_score > 0


def test_bmtm33_dominance_history_and_api_contracts() -> None:
    db = _session()
    now = utcnow()
    db.add(_event("CFTC regulation and SEC ETF market structure narrative", now - timedelta(minutes=5), impact=0.8))
    db.commit()
    service = NarrativeHeatmapService(db)
    service.build_heatmap(window="1h", snapshot_time=now)
    db.commit()

    dominance = service.dominance()
    history = service.history(period="month")

    assert dominance["data"]
    assert history["top_narratives"]
    assert history["growth_leaders"]
    assert "Major BTC move correlation requires candle attribution backfill." in history["limitations"]

    def override_db() -> Iterator[Session]:
        yield db

    app.dependency_overrides[db_session] = override_db
    try:
        client = TestClient(app)
        dominance_response = client.get("/api/v1/intelligence/narratives/dominance")
        emerging_response = client.get("/api/v1/intelligence/narratives/emerging")
        history_response = client.get("/api/v1/intelligence/narratives/history?period=month")
        detail_response = client.get("/api/v1/intelligence/narratives/ETF")
    finally:
        app.dependency_overrides.clear()

    assert dominance_response.status_code == 200
    assert dominance_response.json()["data"]
    assert emerging_response.status_code == 200
    assert history_response.status_code == 200
    assert history_response.json()["top_narratives"]
    assert detail_response.status_code == 200
    assert detail_response.json()["data"]["narrative_type"] == "ETF"
