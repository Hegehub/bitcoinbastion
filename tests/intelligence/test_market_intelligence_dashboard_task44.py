from __future__ import annotations

from app.db.models.intelligence_signals import IntelligenceOperatorReview, IntelligenceSignalCandidate
from app.db.models.news_source import NewsSource
from app.db.models.source_reputation_profile import SourceReputationProfile
from app.main import app
from app.web.market_time_machine_service import MarketTimeMachineWebService
from app.web.view_models.market import build_market_dto
from tests.intelligence.test_market_time_machine_web_task41 import _client_with_db, _seed


def test_task44_market_intelligence_routes_and_navigation() -> None:
    client, SessionLocal = _client_with_db()
    with SessionLocal() as session:
        _seed(session)
        _seed_market_intelligence(session)
    try:
        for path, expected in [
            ("/market", "Market Intelligence"),
            ("/market/timeline", "Market Timeline"),
            ("/market/time-machine", "Timeline Controls"),
            ("/market/signals", "Pending Review"),
            ("/market/evidence", "Evidence Packet Viewer"),
            ("/market/narratives", "Narrative Panel"),
            ("/market/sources?sort=quality", "Source Intelligence"),
        ]:
            response = client.get(path)
            assert response.status_code == 200
            assert expected in response.text
            assert "Correlation is not proof of causation." in response.text
            assert "Bitcoin Bastion provides evidence-based market context" in response.text or "evidence-based" in response.text
        landing = client.get("/market")
        assert "BTC Price" in landing.text
        assert "News Shock Index" in landing.text
        assert "Latest High Impact Event" in landing.text
        assert "Latest Published Signal" in landing.text
        assert "Provider Health" in landing.text
        assert "Operator Queue" in landing.text
        assert "Evidence Replay Requests" in landing.text
    finally:
        app.dependency_overrides.clear()


def test_task44_dto_contract_sources_signals_evidence_and_replay() -> None:
    client, SessionLocal = _client_with_db()
    with SessionLocal() as session:
        _seed(session)
        _seed_market_intelligence(session)
        service = MarketTimeMachineWebService(session)
        dashboard = service.dashboard(timeframe="1h")
        payload = service.landing_payload(timeframe="1h")
        vm = build_market_dto(dashboard, selected_timeframe="1h", api_payload=payload)
        assert set([
            "market_timeline",
            "timeline_events",
            "candle_details",
            "attribution_details",
            "evidence_summary",
            "replay_summary",
            "source_summary",
            "narrative_summary",
            "shock_index_summary",
        ]).issubset(vm)
        assert vm["source_summary"]["items"][0]["source_name"] == "Task44 Source"
        assert vm["signal_summary"]["counts"]["pending_review"] >= 1
        assert vm["evidence_summary"]["packets"]
        assert "timeline_supports" in vm["chart_data"]
    try:
        payload = client.get("/web/market-time-machine?timeframe=1h").json()
        assert "source_summary" in payload
        assert "replay_summary" in payload
        assert "shock_index_summary" in payload
    finally:
        app.dependency_overrides.clear()


def test_task44_empty_states_are_visible() -> None:
    client, _ = _client_with_db()
    try:
        response = client.get("/market/sources")
        assert response.status_code == 200
        assert "Source registry is empty or unavailable." in response.text
        evidence = client.get("/market/evidence")
        assert evidence.status_code == 200
        assert "No evidence packets available." in evidence.text
    finally:
        app.dependency_overrides.clear()


def _seed_market_intelligence(session) -> None:
    source = NewsSource(
        name="Task44 Source",
        slug="task44-source",
        base_url="https://example.test",
        rss_url="https://example.test/rss",
        homepage_url="https://example.test",
        provider_confidence=0.84,
        avg_latency_ms=123.0,
        failure_count=2,
        health_band="ACTIVE",
        signal_quality_weight=0.77,
    )
    session.add(source)
    session.flush()
    session.add(
        SourceReputationProfile(
            source_id=source.id,
            reliability_score=0.81,
            signal_quality_score=0.79,
            first_mover_score=0.67,
            provider_confidence=0.84,
        )
    )
    signal = IntelligenceSignalCandidate(
        signal_type="news_market_impact",
        source_entity_type="news_event",
        source_entity_id=1,
        event_id=1,
        candle_id=1,
        title="Pending ETF impact signal",
        summary="Operator should review before publication.",
        confidence_score=0.74,
        provider_confidence=0.84,
        status="pending_review",
        policy_decision="pending",
        requires_operator_review=True,
    )
    session.add(signal)
    session.flush()
    session.add(IntelligenceOperatorReview(signal_candidate_id=signal.id, review_status="pending"))
    session.commit()
