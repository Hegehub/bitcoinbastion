from __future__ import annotations

from datetime import datetime, timedelta

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.dependencies import db_session
from app.db.base import Base
from app.db.models.btc_candle import BTCCandle
from app.db.models.candle_attribution_candidate import CandleAttributionCandidate
from app.db.models.evidence_packet import EvidenceArtifact, EvidencePacket
from app.db.models.intelligence_timeline import IntelligenceTimelineEvent
from app.db.models.news_event import NewsEvent
from app.main import app
from app.schemas.market_time_machine_web import (
    CandleAttributionDTO,
    EvidencePanelDTO,
    MarketTimelineDTO,
    NewsMarkerDTO,
)
from app.web.market_time_machine_service import MarketTimeMachineWebService, SAFETY_LIMITATIONS


def _client_with_db() -> tuple[TestClient, sessionmaker[Session]]:
    engine = create_engine(
        "sqlite+pysqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        future=True,
    )
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine, class_=Session)

    def override_db():
        with SessionLocal() as session:
            yield session

    app.dependency_overrides[db_session] = override_db
    return TestClient(app), SessionLocal


def _seed(session: Session) -> None:
    now = datetime.utcnow()
    candle = BTCCandle(
        timeframe="1h",
        open_time=now - timedelta(hours=1),
        close_time=now,
        open=100.0,
        high=110.0,
        low=95.0,
        close=105.0,
        volume=12.5,
        provider_confidence=0.91,
        evidence_packet_id="packet:1",
        is_partial=False,
    )
    session.add(candle)
    session.flush()
    event = NewsEvent(
        canonical_title="Bitcoin ETF inflow expands",
        canonical_summary="ETF event summary",
        event_type="etf",
        event_category="institutional",
        first_seen_at=now - timedelta(minutes=40),
        last_seen_at=now - timedelta(minutes=35),
        source_count=2,
        article_count=3,
        event_sentiment="POSITIVE",
        event_confidence=0.82,
        is_institutional_related=True,
        first_source_name="Example Source",
    )
    session.add(event)
    session.flush()
    session.add(
        CandleAttributionCandidate(
            candle_id=candle.id,
            candidate_type="news_event",
            event_id=event.id,
            time_distance_seconds=600,
            relevance_score=0.8,
            direction_match_score=0.7,
            normalized_score=0.76,
        )
    )
    session.add(
        IntelligenceTimelineEvent(
            event_type="news_event",
            title="ETF event added to timeline",
            summary="Timeline entry summary",
            event_time=now - timedelta(minutes=30),
            confidence_score=0.8,
            provider_confidence=0.9,
            related_event_id=event.id,
            related_candle_id=candle.id,
            evidence_refs_json=[{"packet_id": 1}],
            limitations_json=SAFETY_LIMITATIONS,
            visibility="PUBLIC",
        )
    )
    packet = EvidencePacket(
        packet_type="candle_attribution",
        source_entity_type="btc_candle",
        source_entity_id=candle.id,
        title="ETF attribution evidence",
        summary="Evidence summary",
        confidence_score=0.7,
        provider_confidence=0.9,
        source_confidence=0.8,
    )
    session.add(packet)
    session.flush()
    session.add(
        EvidenceArtifact(
            packet_id=packet.id,
            entity_type="news_event",
            entity_id=event.id,
            artifact_type="source_snapshot",
        )
    )
    session.commit()


def test_market_time_machine_routes_render_empty_states() -> None:
    client, _ = _client_with_db()
    try:
        for path, expected in [
            ("/market-time-machine", "Market Time Machine"),
            ("/intelligence/timeline", "Unified market memory timeline"),
            ("/evidence/999", "Evidence packet not generated"),
            ("/candles/999", "No attribution available"),
        ]:
            response = client.get(path)
            assert response.status_code == 200
            assert expected in response.text
            assert "Correlation is not proof of causation" in response.text
    finally:
        app.dependency_overrides.clear()


def test_market_time_machine_routes_render_seeded_dashboard_and_mobile_markup() -> None:
    client, SessionLocal = _client_with_db()
    with SessionLocal() as session:
        _seed(session)
    try:
        response = client.get("/market-time-machine?timeframe=1h")
        assert response.status_code == 200
        assert "btc_candlestick_chart" not in response.text
        assert "BTC Candlestick Chart" in response.text
        assert "Bitcoin ETF inflow expands" in response.text
        assert "viewport" in response.text
        assert 'aria-label="BTC candlestick chart with news markers"' in response.text

        timeline = client.get("/intelligence/timeline?filter=all&page=1&page_size=10")
        assert timeline.status_code == 200
        assert "ETF event added to timeline" in timeline.text
        assert "Open Candle" in timeline.text
    finally:
        app.dependency_overrides.clear()


def test_web_dto_endpoints_and_serializers_are_frontend_compatible() -> None:
    client, SessionLocal = _client_with_db()
    with SessionLocal() as session:
        _seed(session)
        service = MarketTimeMachineWebService(session)
        dashboard = service.dashboard(timeframe="1h")
        candle = service.candle_attribution(1)
        marker = service.news_markers(limit=5)[0]
        evidence = service.evidence_panel(1)

        assert isinstance(dashboard, MarketTimelineDTO)
        assert isinstance(candle, CandleAttributionDTO)
        assert isinstance(marker, NewsMarkerDTO)
        assert isinstance(evidence, EvidencePanelDTO)
        assert marker.marker_style == "marker-institutional"
        assert candle.candidate_events[0]["confidence"] == 0.76
        assert "Correlation is not proof of causation." in candle.limitations

    try:
        response = client.get("/web/market-time-machine?timeframe=1h")
        assert response.status_code == 200
        payload = response.json()
        assert payload["chart_markers"][0]["marker_priority"] == 3
        assert payload["candles"][0]["price_change_pct"] == 5.0

        response = client.get("/web/candle/1")
        assert response.status_code == 200
        assert response.json()["provider_confidence"] == 0.91

        response = client.get("/web/evidence/1")
        assert response.status_code == 200
        assert response.json()["integrity_status"] == "available"
    finally:
        app.dependency_overrides.clear()


def test_marker_duplicate_suppression_and_timeline_pagination() -> None:
    _, SessionLocal = _client_with_db()
    with SessionLocal() as session:
        now = datetime.utcnow()
        for idx in range(3):
            session.add(
                NewsEvent(
                    canonical_title=f"Duplicate regulatory marker {idx}",
                    event_type="regulatory",
                    event_category="sec",
                    first_seen_at=now,
                    last_seen_at=now,
                    is_regulatory_related=True,
                    event_confidence=0.5,
                )
            )
        for idx in range(3):
            session.add(
                IntelligenceTimelineEvent(
                    event_type="news_event",
                    title=f"Timeline {idx}",
                    summary="summary",
                    event_time=now - timedelta(minutes=idx),
                    visibility="PUBLIC",
                )
            )
        session.commit()
        service = MarketTimeMachineWebService(session)
        markers = service.news_markers(limit=10)
        assert len(markers) == 1
        assert markers[0].marker_type == "regulatory"
        page = service.timeline(page=1, page_size=2, window="all")
        assert len(page.timeline_items) == 2
        assert page.has_next is True
