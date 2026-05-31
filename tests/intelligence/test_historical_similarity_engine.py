from datetime import datetime, timedelta

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.api.dependencies import db_session
from app.db.base import Base
from app.db.models.btc_candle import BTCCandle
from app.db.models.historical_similarity_result import HistoricalSimilarityResult
from app.db.models.news_article import NewsArticle  # noqa: F401
from app.db.models.news_event import NewsEvent
from app.db.models.news_price_impact import NewsPriceImpact
from app.db.models.news_source import NewsSource  # noqa: F401
from app.main import app
from app.services.intelligence.candle_attribution_engine import CandleAttributionEngine
from app.services.intelligence.historical_profile_builder import HistoricalEventProfileBuilder
from app.services.intelligence.historical_similarity_service import HistoricalSimilarityService
from app.services.intelligence.pattern_library import MarketPattern


def _session() -> Session:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    return Session(engine)


def _event(
    seen_at: datetime,
    title: str,
    sentiment: str = "POSITIVE",
    event_type: str = "institutional_etf",
    category: str = "ETF",
    impact: float = 0.9,
    confidence: float = 0.88,
) -> NewsEvent:
    return NewsEvent(
        event_key=title.lower().replace(" ", "-"),
        canonical_title=title,
        canonical_summary=title,
        event_type=event_type,
        event_category=category,
        first_seen_at=seen_at,
        last_seen_at=seen_at + timedelta(minutes=2),
        source_count=2,
        article_count=2,
        cluster_confidence=confidence,
        btc_relevance_score=0.92,
        market_impact_score=impact,
        event_sentiment=sentiment,
        event_confidence=confidence,
        provider_confidence=0.9,
        is_high_impact=True,
        is_institutional_related=category == "ETF",
        is_security_related=category == "SECURITY",
        is_regulatory_related=category == "REGULATORY",
    )


def _impact(event: NewsEvent, move_15m: float, move_1h: float, move_4h: float, move_24h: float) -> NewsPriceImpact:
    return NewsPriceImpact(
        event_id=event.id,
        sentiment_label=event.event_sentiment,
        btc_relevance_score=event.btc_relevance_score,
        market_impact_score=event.market_impact_score,
        provider_confidence=event.provider_confidence,
        impact_confidence_score=event.event_confidence,
        dominant_window="4h",
        change_15m_pct=move_15m,
        change_1h_pct=move_1h,
        change_4h_pct=move_4h,
        change_24h_pct=move_24h,
    )


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
        provider_disagreement_score=0.05,
        is_degraded=False,
        volatility_score=0.2,
        market_regime="normal",
    )


def test_same_pattern_similarity_ranks_above_different_pattern() -> None:
    db = _session()
    base = datetime(2026, 5, 28, 12, 0, 0)
    reference = _event(base, "Bitcoin ETF inflow shock drives demand")
    same = _event(base - timedelta(days=10), "Bitcoin ETF inflows surge again")
    different = _event(
        base - timedelta(days=20),
        "Exchange hack triggers custody concern",
        sentiment="NEGATIVE",
        event_type="security_shock",
        category="SECURITY",
        impact=0.7,
    )
    db.add_all([reference, same, different])
    db.flush()
    db.add_all([_impact(reference, 0.4, 1.1, 2.2, 1.8), _impact(same, 0.5, 1.0, 2.0, 1.7), _impact(different, -0.7, -1.3, -2.7, -3.0)])
    db.commit()

    results = HistoricalSimilarityService(db).find_similar_events(reference.id, limit=10)

    assert results[0]["event_id"] == same.id
    assert results[0]["pattern_type"] == MarketPattern.ETF_INFLOW_SHOCK.value
    assert results[0]["similarity_score"] > results[1]["similarity_score"]
    assert "Correlation is not proof of causation." in results[0]["explanation"]["limitations"]
    assert db.query(HistoricalSimilarityResult).count() == 2


def test_sentiment_and_price_behavior_penalties_are_explainable() -> None:
    db = _session()
    base = datetime(2026, 5, 28, 12, 0, 0)
    reference = _event(base, "Bitcoin ETF inflow shock")
    positive = _event(base - timedelta(days=1), "Bitcoin ETF inflow expands")
    negative = _event(base - timedelta(days=2), "Bitcoin ETF inflow headline fades", sentiment="NEGATIVE")
    db.add_all([reference, positive, negative])
    db.flush()
    db.add_all([_impact(reference, 0.2, 0.8, 1.8, 2.0), _impact(positive, 0.3, 0.7, 1.7, 1.9), _impact(negative, -0.5, -1.0, -2.2, -2.5)])
    db.commit()

    results = HistoricalSimilarityService(db).find_similar_news_events(reference.id, limit=2)

    assert results[0]["event_id"] == positive.id
    negative_result = next(row for row in results if row["event_id"] == negative.id)
    assert negative_result["explanation"]["components"]["sentiment_similarity"] < 0.5
    assert negative_result["explanation"]["components"]["price_behavior_similarity"] < 0.5


def test_top_n_ranking_and_profile_vector_builder() -> None:
    db = _session()
    base = datetime(2026, 5, 28, 12, 0, 0)
    reference = _event(base, "Bitcoin ETF inflow shock")
    db.add(reference)
    db.flush()
    db.add(_impact(reference, 0.1, 0.8, 1.5, 2.0))
    for index in range(12):
        candidate = _event(base - timedelta(days=index + 1), f"Bitcoin ETF inflow similar case {index}", impact=0.9 - index * 0.02)
        db.add(candidate)
        db.flush()
        db.add(_impact(candidate, 0.1, 0.8, 1.5 - index * 0.05, 2.0 - index * 0.05))
    db.commit()

    profile = HistoricalEventProfileBuilder(db).build_from_news_event(reference)
    vector = HistoricalEventProfileBuilder(db).build_feature_vector(profile)
    results = HistoricalSimilarityService(db).find_similar_events(reference.id, limit=5)

    assert len(results) == 5
    assert vector.narrative[1] == MarketPattern.ETF_INFLOW_SHOCK.value
    assert all(results[index]["similarity_score"] >= results[index + 1]["similarity_score"] for index in range(4))


def test_candle_similarity_and_evidence_packet_include_historical_events() -> None:
    db = _session()
    open_time = datetime(2026, 5, 28, 12, 0, 0)
    candle = _candle(open_time)
    reference = _event(open_time - timedelta(minutes=5), "Bitcoin ETF inflows hit record high")
    historical = _event(open_time - timedelta(days=5), "Bitcoin ETF inflows hit previous record")
    db.add_all([candle, reference, historical])
    db.flush()
    db.add_all([_impact(reference, 0.4, 1.1, 2.0, 1.9), _impact(historical, 0.5, 1.0, 2.1, 1.8)])
    db.commit()

    rows = CandleAttributionEngine(db).attribute_candle(candle.id)
    results = HistoricalSimilarityService(db).find_similar_candle_events(candle.id, limit=3)

    assert results
    assert rows[0].evidence_refs_json["similar_historical_events"]
    assert "historical_similarity_summary" in rows[0].evidence_refs_json
    assert "Past reactions do not guarantee future market behavior." in rows[0].evidence_refs_json["limitations"]


def test_similarity_api_contract_returns_frontend_ready_payload() -> None:
    client = TestClient(app, raise_server_exceptions=False)

    response = client.get("/api/v1/intelligence/similarity/event/999999")

    assert response.status_code == 200
    payload = response.json()
    assert "data" in payload
    assert "Correlation is not proof of causation." in payload["limitations"]


def test_pattern_classification_library_and_similarity_report_statistics() -> None:
    from app.db.models.historical_similarity_record import HistoricalSimilarityRecord
    from app.db.models.market_pattern_library import MarketPatternLibrary
    from app.services.intelligence.pattern_classification_service import PatternClassificationService

    db = _session()
    base = datetime(2026, 5, 28, 12, 0, 0)
    reference = _event(base, "Bitcoin ETF inflow shock accelerates")
    analog_one = _event(base - timedelta(days=1), "Bitcoin ETF inflow shock repeats")
    analog_two = _event(base - timedelta(days=2), "Bitcoin ETF inflows lift institutional demand")
    db.add_all([reference, analog_one, analog_two])
    db.flush()
    db.add_all([_impact(reference, 0.5, 1.0, 2.0, 2.5), _impact(analog_one, 0.6, 1.2, 2.4, 2.8), _impact(analog_two, 0.4, 1.0, 2.0, 2.2)])
    db.commit()

    patterns = PatternClassificationService(db).ensure_pattern_library()
    classification = PatternClassificationService(db).classification_evidence(reference)
    report = HistoricalSimilarityService(db).build_event_report(reference.id, limit=10)

    assert len(patterns) >= 20
    pattern_codes = {pattern.pattern_code for pattern in patterns}
    assert {"ETF_APPROVAL", "ETF_DELAY", "FED_LIQUIDITY_SHOCK", "MINING_DIFFICULTY_SHOCK", "HALVING_NARRATIVE"}.issubset(pattern_codes)
    etf_pattern = db.query(MarketPatternLibrary).filter(MarketPatternLibrary.pattern_code == "ETF_INFLOW_SHOCK").first()
    assert etf_pattern is not None
    assert etf_pattern.default_sentiment == "POSITIVE"
    assert etf_pattern.expected_reaction_window == "15m"
    assert etf_pattern.expected_volatility == "normal"
    assert classification[0]["pattern_code"] == "ETF_INFLOW_SHOCK"
    assert report.sample_size == 2
    assert report.median_reaction_4h == 2.2
    assert report.average_reaction_1h == 1.1
    assert report.similarity_band in {"Strong", "Very Strong"}
    assert "Historical similarity does not guarantee future outcomes." in report.limitations
    assert db.query(HistoricalSimilarityRecord).count() == 2


def test_single_analog_and_empty_report_are_safe() -> None:
    db = _session()
    base = datetime(2026, 5, 28, 12, 0, 0)
    reference = _event(base, "Exchange hack security incident", sentiment="NEGATIVE", event_type="security_shock", category="SECURITY")
    analog = _event(base - timedelta(days=3), "Exchange hack security incident repeats", sentiment="NEGATIVE", event_type="security_shock", category="SECURITY")
    db.add_all([reference, analog])
    db.flush()
    db.add_all([_impact(reference, -0.4, -1.0, -2.0, -2.8), _impact(analog, -0.5, -1.1, -2.1, -2.9)])
    db.commit()

    report = HistoricalSimilarityService(db).build_event_report(reference.id, limit=1)
    empty = HistoricalSimilarityService(db).build_event_report(999999, limit=10)

    assert report.sample_size == 1
    assert report.evidence["reaction_statistics"]["dispersion"]["reaction_4h"] == 0.0
    assert empty.sample_size == 0
    assert empty.similar_events == []


def test_similarity_report_and_pattern_api_endpoints() -> None:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)

    def override_db() -> Session:
        with Session(engine) as session:
            yield session

    app.dependency_overrides[db_session] = override_db
    try:
        client = TestClient(app, raise_server_exceptions=False)
        event_response = client.get("/api/v1/intelligence/similarity/events/999999")
        article_response = client.get("/api/v1/intelligence/similarity/articles/999999")
        patterns_response = client.get("/api/v1/intelligence/patterns")

        assert event_response.status_code == 200
        assert event_response.json()["sample_size"] == 0
        assert "Historical similarity does not guarantee future outcomes." in event_response.json()["limitations"]
        assert article_response.status_code == 200
        assert article_response.json()["sample_size"] == 0
        assert patterns_response.status_code == 200
        assert patterns_response.json()["data"]
    finally:
        app.dependency_overrides.clear()


def test_prompt28_packaged_similarity_response_and_signal_endpoint() -> None:
    from app.services.intelligence.historical_similarity.historical_similarity_service import (
        HistoricalSimilarityService as PackagedHistoricalSimilarityService,
    )
    from app.services.intelligence.historical_similarity.similarity_scoring import SimilarityScoring

    db = _session()
    base = datetime(2026, 5, 28, 12, 0, 0)
    reference = _event(base, "Bitcoin ETF inflow shock prompt28")
    analog = _event(base - timedelta(days=4), "Bitcoin ETF inflow shock historical prompt28")
    db.add_all([reference, analog])
    db.flush()
    db.add_all([_impact(reference, 0.3, 1.0, 2.0, 2.4), _impact(analog, 0.4, 1.1, 2.2, 2.6)])
    db.commit()

    response = PackagedHistoricalSimilarityService(db).find_for_event(reference.id)

    assert response.current_item["event_id"] == reference.id
    assert response.top_similar_events
    assert response.pattern_name == "ETF_INFLOW_SHOCK"
    assert response.median_reaction["4h"] == 2.2
    assert response.similarity_band in {"strong", "very strong"}
    assert "Historical similarity does not guarantee future outcomes." in response.limitations
    assert SimilarityScoring().band(0.29) == "weak"
    assert SimilarityScoring().band(0.45) == "moderate"
    assert SimilarityScoring().band(0.70) == "strong"
    assert SimilarityScoring().band(0.90) == "very strong"


def test_prompt28_signal_api_endpoint_returns_safe_empty_response() -> None:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)

    def override_db() -> Session:
        with Session(engine) as session:
            yield session

    app.dependency_overrides[db_session] = override_db
    try:
        client = TestClient(app, raise_server_exceptions=False)
        response = client.get("/api/v1/intelligence/similarity/signals/999999")

        assert response.status_code == 200
        payload = response.json()
        assert payload["current_item"]["signal_id"] == 999999
        assert payload["matched_items"] == []
        assert "Historical similarity does not guarantee future outcomes." in payload["limitations"]
    finally:
        app.dependency_overrides.clear()
