from datetime import datetime, timedelta

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.api.dependencies import db_session
from app.db.base import Base
from app.db.models.historical_reaction_statistics import HistoricalReactionStatistics
from app.db.models.market_pattern import MarketPattern
from app.db.models.narrative_memory_snapshot import NarrativeMemorySnapshot
from app.db.models.news_event import NewsEvent
from app.db.models.news_price_impact import NewsPriceImpact
from app.db.models.pattern_occurrence import PatternOccurrence
from app.main import app
from app.services.intelligence.historical_similarity_service import HistoricalSimilarityService
from app.services.intelligence.market_memory_service import MarketMemoryService
from app.services.intelligence.narrative_memory_service import NarrativeMemoryService


def _session() -> Session:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    return Session(engine)


def _event(title: str, seen_at: datetime, sentiment: str = "POSITIVE", category: str = "ETF") -> NewsEvent:
    return NewsEvent(
        event_key=title.lower().replace(" ", "-"),
        canonical_title=title,
        canonical_summary=title,
        event_type=category.lower(),
        event_category=category,
        first_seen_at=seen_at,
        last_seen_at=seen_at + timedelta(minutes=5),
        source_count=3,
        article_count=2,
        cluster_confidence=0.9,
        btc_relevance_score=0.9,
        market_impact_score=0.8,
        event_sentiment=sentiment,
        event_confidence=0.85,
        provider_confidence=0.9,
        is_high_impact=True,
        is_institutional_related=category == "ETF",
        is_regulatory_related=category == "REGULATION",
        is_security_related=category == "SECURITY",
    )


def _impact(event: NewsEvent, move: float) -> NewsPriceImpact:
    return NewsPriceImpact(
        event_id=event.id,
        sentiment_label=event.event_sentiment,
        btc_relevance_score=event.btc_relevance_score,
        market_impact_score=event.market_impact_score,
        provider_confidence=event.provider_confidence,
        impact_confidence_score=event.event_confidence,
        dominant_window="4h",
        change_15m_pct=move / 4,
        change_1h_pct=move / 2,
        change_4h_pct=move,
        change_24h_pct=move * 1.2,
    )


def test_task39_pattern_seed_contains_required_library_and_frontend_fields() -> None:
    db = _session()
    rows = MarketMemoryService(db).ensure_patterns()
    codes = {row.slug for row in rows}

    required = {
        "ETF_INFLOW_SHOCK",
        "ETF_OUTFLOW_SHOCK",
        "SEC_ENFORCEMENT",
        "REGULATORY_APPROVAL",
        "REGULATORY_DELAY",
        "FED_LIQUIDITY",
        "FED_TIGHTENING",
        "CPI_SURPRISE",
        "MACRO_RISK_ON",
        "MACRO_RISK_OFF",
        "EXCHANGE_HACK",
        "CUSTODY_FAILURE",
        "MINER_CAPITULATION",
        "MINER_ACCUMULATION",
        "LARGE_LIQUIDATION",
        "BITCOIN_CORE_RELEASE",
        "LIGHTNING_ADOPTION",
        "INSTITUTIONAL_TREASURY",
        "SELF_CUSTODY_NARRATIVE",
        "SECURITY_VULNERABILITY",
    }
    assert required.issubset(codes)
    etf = db.query(MarketPattern).filter(MarketPattern.slug == "ETF_INFLOW_SHOCK").one()
    assert etf.display_name
    assert etf.typical_sentiment == "POSITIVE"
    assert etf.typical_direction == "UP"
    assert etf.default_time_window == "1h"


def test_task39_similarity_evidence_statistics_and_limitations_are_deterministic() -> None:
    db = _session()
    base = datetime(2026, 6, 1, 12, 0, 0)
    reference = _event("Bitcoin ETF inflows hit record high", base)
    same = _event("Bitcoin ETF inflow shock drives demand", base - timedelta(days=7))
    different = _event("Exchange hack triggers custody concern", base - timedelta(days=8), sentiment="NEGATIVE", category="SECURITY")
    db.add_all([reference, same, different])
    db.flush()
    db.add_all([_impact(reference, 2.6), _impact(same, 2.4), _impact(different, -3.0)])
    db.commit()

    service = HistoricalSimilarityService(db)
    first = service.find_similar_events(reference.id, limit=5)
    second = service.find_similar_events(reference.id, limit=5, persist_results=False)
    assert first[0]["event_id"] == same.id
    assert first[0]["similarity_score"] == second[0]["similarity_score"]

    context = service.build_historical_context(reference.id, limit=5)
    assert "historical_examples" in context
    assert "confidence_breakdown" in context
    assert "narrative_tags" in context
    for limitation in [
        "historical_sample_count_low",
        "pattern_confidence_low",
        "provider_diversity_low",
        "correlation_not_causation",
        "market_structure_changed",
        "historical_reference_only",
        "not_financial_advice",
        "evidence_based",
    ]:
        assert limitation in context["limitations"]

    pattern_id = db.query(PatternOccurrence).filter(PatternOccurrence.event_id == same.id).first().pattern_id
    stats = service.build_reaction_statistics(pattern_id)
    assert stats["samples"] >= 1
    assert db.query(HistoricalReactionStatistics).filter(HistoricalReactionStatistics.pattern_id == pattern_id).count() == 1
    evidence = service.build_similarity_evidence(reference.id, limit=3)
    assert evidence["historical_samples_used"] >= 1
    assert "reaction_statistics" in evidence


def test_task39_narrative_memory_and_api_contracts() -> None:
    db = _session()
    now = datetime.utcnow()
    event = _event("Bitcoin ETF inflows and institutional treasury adoption accelerate", now)
    db.add(event)
    db.flush()
    db.add(_impact(event, 1.5))
    db.commit()

    snapshot = NarrativeMemoryService(db).build_narrative_snapshot()
    assert snapshot["data"][0]["heat_score"] >= 0.0
    assert db.query(NarrativeMemorySnapshot).count() == 10

    def override_session():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[db_session] = override_session
    try:
        client = TestClient(app, raise_server_exceptions=False)
        patterns = client.get("/api/v1/intelligence/patterns")
        assert patterns.status_code == 200
        assert "data" in patterns.json()
        active = client.get("/api/v1/intelligence/narratives/active")
        assert active.status_code == 200
        assert "data" in active.json()
        similarity = client.get(f"/api/v1/intelligence/similarity/{event.id}")
        assert similarity.status_code == 200
        assert "historical_examples" in similarity.json()
    finally:
        app.dependency_overrides.clear()
