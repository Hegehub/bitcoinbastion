from __future__ import annotations

from datetime import datetime

from app.db.models.narrative_memory_snapshot import NarrativeMemorySnapshot
from app.db.models.news_price_impact import NewsPriceImpact
from app.web.market_time_machine_service import MarketTimeMachineWebService
from tests.intelligence.test_market_time_machine_web_task41 import _client_with_db, _seed
from app.main import app


def test_task42_market_route_panels_and_news_click_dto() -> None:
    client, SessionLocal = _client_with_db()
    with SessionLocal() as session:
        _seed(session)
        session.add(
            NewsPriceImpact(
                event_id=1,
                price_at_publish=100.0,
                price_after_15m=101.0,
                price_after_1h=102.0,
                price_after_4h=103.0,
                price_after_24h=104.0,
                change_15m_pct=1.0,
                change_1h_pct=2.0,
                change_4h_pct=3.0,
                change_24h_pct=4.0,
                sentiment_label="POSITIVE",
                btc_relevance_score=0.91,
                source_credibility_score=0.82,
                provider_confidence=0.88,
                impact_confidence_score=0.79,
            )
        )
        session.add(
            NarrativeMemorySnapshot(
                narrative="ETF",
                snapshot_time=datetime.utcnow(),
                event_count=3,
                weighted_impact=0.8,
                source_quality=0.9,
                market_reaction=0.1,
                heat_score=0.76,
                strength_score=0.8,
                decay_score=0.2,
            )
        )
        session.commit()
    try:
        response = client.get("/market?timeframe=1h")
        assert response.status_code == 200
        assert "Historical Similarity Panel" in response.text
        assert "Narrative Panel" in response.text
        assert "Dominant Direction" in response.text
        assert "BTC Price At Publish" in response.text

        event_response = client.get("/api/v1/intelligence/events/1/timeline")
        assert event_response.status_code == 200
        payload = event_response.json()
        assert payload["data"]["data"]["btc_price_at_publish"] == 100.0
        assert payload["data"]["data"]["change_4h"] == 3.0
        assert payload["chart_markers"][0]["marker_style"] == "marker-institutional"
    finally:
        app.dependency_overrides.clear()


def test_task42_candle_api_contracts_evidence_similarity_and_filters() -> None:
    client, SessionLocal = _client_with_db()
    with SessionLocal() as session:
        _seed(session)
        service = MarketTimeMachineWebService(session)
        combined = service.timeline(filter_name="news,high_confidence", page_size=10, window="all")
        assert combined.filters["active_filters"] == ["news", "high_confidence"]
        assert combined.timeline_items[0]["title"] == "ETF event added to timeline"
    try:
        candle = client.get("/api/v1/intelligence/candles/1")
        assert candle.status_code == 200
        candle_payload = candle.json()
        assert candle_payload["data"]["open"] == 100.0
        assert candle_payload["data"]["dominant_direction"] == "up"
        assert candle_payload["data"]["safety_flags"]["correlation_not_causation"] is True
        assert "confidence_breakdown" in candle_payload
        assert "similarity_preview" in candle_payload

        events = client.get("/api/v1/intelligence/candles/1/events")
        assert events.status_code == 200
        assert events.json()["candidate_news_events"][0]["event_id"] == 1

        evidence = client.get("/api/v1/intelligence/candles/1/evidence")
        assert evidence.status_code == 200
        assert evidence.json()["limitations"]

        similar = client.get("/api/v1/intelligence/candles/1/similar")
        assert similar.status_code == 200
        assert "Historical similarity is reference-only." in similar.json()["limitations"]

        day = client.get("/api/v1/intelligence/timeline/day?filter=news,high_confidence")
        assert day.status_code == 200
        assert day.json()["filters"]["active_filters"] == ["news", "high_confidence"]

        hour = client.get("/api/v1/intelligence/timeline/hour")
        assert hour.status_code == 200
        assert "timeline_items" in hour.json()
    finally:
        app.dependency_overrides.clear()
