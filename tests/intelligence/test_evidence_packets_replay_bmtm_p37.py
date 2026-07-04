from datetime import datetime, timedelta

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

import app.db.models  # noqa: F401
from app.api.dependencies import db_session
from app.db.base import Base
from app.db.models.candle_attribution import CandleAttribution
from app.db.models.intelligence_signals import (
    IntelligenceOperatorReview,
    IntelligenceSignalCandidate,
    IntelligenceSignalDeliveryLog,
)
from app.db.models.news_article import NewsArticle
from app.db.models.news_event import NewsEvent
from app.db.models.news_price_impact import NewsPriceImpact
from app.db.models.news_source import NewsSource
from app.main import app
from app.services.intelligence.evidence_metrics import (
    EVIDENCE_INTEGRITY_CHECKS_TOTAL,
    EVIDENCE_PACKETS_GENERATED_TOTAL,
    EVIDENCE_REPLAY_FAILURES_TOTAL,
    EVIDENCE_REPLAY_REQUESTS_TOTAL,
)
from app.services.intelligence.evidence_packet_builder import EvidencePacketBuilder
from app.services.intelligence.evidence_replay_service import EvidenceReplayService


def _session() -> Session:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    return Session(engine)


def _seed_chain(db: Session) -> dict[str, object]:
    now = datetime(2026, 6, 3, 12, 0, 0)
    source = NewsSource(
        name="Bastion Test Source",
        slug="bastion-test",
        base_url="https://example.test",
        provider_confidence=0.82,
    )
    db.add(source)
    db.flush()
    article = NewsArticle(
        source_id=source.id,
        title="Bitcoin ETF inflow coincided with BTC move",
        url="https://example.test/bitcoin-etf-inflow",
        content_hash="article-hash-1",
        summary="ETF inflow reporting coincided with a Bitcoin move.",
        published_at=now,
        fetched_at=now + timedelta(minutes=1),
        provider_confidence=0.82,
        btc_relevance_score=0.91,
        market_impact_score=0.74,
        credibility_score=0.79,
        confidence_score=0.81,
    )
    db.add(article)
    db.flush()
    event = NewsEvent(
        event_key="btc-etf-inflow-evidence",
        canonical_title="Bitcoin ETF inflow evidence event",
        canonical_summary="Clustered article evidence for a Bitcoin ETF inflow event.",
        event_type="institutional",
        event_category="etf",
        primary_article_id=article.id,
        first_seen_at=now + timedelta(minutes=2),
        last_seen_at=now + timedelta(minutes=4),
        source_count=1,
        article_count=1,
        cluster_confidence=0.85,
        btc_relevance_score=0.91,
        market_impact_score=0.74,
        event_confidence=0.83,
        provider_confidence=0.82,
    )
    db.add(event)
    db.flush()
    impact = NewsPriceImpact(
        article_id=article.id,
        event_id=event.id,
        impact_confidence_score=0.78,
        confidence_score=0.78,
        provider_confidence=0.82,
        source_credibility_score=0.79,
        btc_relevance_score=0.91,
        market_impact_score=0.74,
        dominant_window="4h",
        change_4h_pct=1.9,
        explanation_summary="This event coincided with BTC movement and may have contributed.",
    )
    db.add(impact)
    db.flush()
    attribution = CandleAttribution(
        candle_id=1,
        event_id=event.id,
        article_id=article.id,
        timeframe="1h",
        candle_open_time=now,
        candle_close_time=now + timedelta(hours=1),
        confidence_score=0.76,
        provider_confidence=0.8,
        source_confidence=0.79,
        btc_relevance_score=0.91,
        market_impact_score=0.74,
        price_move_pct=1.2,
        dominant_window="1h",
        summary_text="Attribution evidence for an ETF inflow event.",
    )
    db.add(attribution)
    db.flush()
    signal = IntelligenceSignalCandidate(
        signal_type="news_market_impact",
        source_entity_type="news_price_impact",
        source_entity_id=impact.id,
        article_id=article.id,
        event_id=event.id,
        impact_id=impact.id,
        attribution_id=attribution.id,
        title="Bitcoin event coincided with BTC movement",
        summary="Correlation-based attribution, not proof of causation.",
        confidence_score=0.78,
        btc_relevance_score=0.91,
        market_impact_score=0.74,
        source_confidence=0.79,
        provider_confidence=0.82,
        status="published",
        policy_decision="review_required",
        policy_reason="auto_publish_disabled",
        requires_operator_review=False,
        published_at=now + timedelta(minutes=20),
    )
    db.add(signal)
    db.flush()
    db.add(
        IntelligenceOperatorReview(
            signal_candidate_id=signal.id,
            review_status="approved",
            decision_reason="Evidence packet accepted.",
            confidence_override=0.77,
            publish_override=True,
        )
    )
    db.add(
        IntelligenceSignalDeliveryLog(
            signal_candidate_id=signal.id,
            channel="web",
            delivery_status="success",
            target="public-web",
            delivered_at=now + timedelta(minutes=21),
        )
    )
    db.commit()
    return {
        "article": article,
        "event": event,
        "impact": impact,
        "attribution": attribution,
        "signal": signal,
    }


def test_packet_creation_relationships_limitations_confidence_and_exports() -> None:
    db = _session()
    rows = _seed_chain(db)
    builder = EvidencePacketBuilder(db)

    packet = builder.build("signal", rows["signal"].id)
    payload = builder.packet_payload(packet)
    markdown = builder.export_packet(packet, fmt="markdown")

    assert packet.packet_type == "signal_evidence"
    assert payload["evidence_summary"]["correlation_not_causation"] is True
    assert payload["confidence_breakdown"]["source_contribution"] == 0.79
    assert payload["confidence_breakdown"]["provider_contribution"] == 0.82
    assert payload["confidence_breakdown"]["operator_overrides"][0]["confidence_override"] == 0.77
    assert payload["limitations"]["correlation_not_causation"] is True
    assert payload["limitations"]["low_source_diversity"] is False
    assert payload["operator_review_status"] == "approved"
    assert payload["publication_status"] == "published"
    assert {row["relationship_type"] for row in payload["relationships"]} >= {
        "article_to_news_event",
        "news_event_to_price_impact",
        "price_impact_to_attribution",
        "attribution_to_signal",
    }
    assert "Correlation-based attribution" in markdown
    assert EVIDENCE_PACKETS_GENERATED_TOTAL._labelnames == ("packet_type",)


def test_replay_article_event_attribution_signal_and_integrity_mismatch() -> None:
    db = _session()
    rows = _seed_chain(db)
    service = EvidenceReplayService(db)

    article_replay = service.replay_article(rows["article"].id)
    event_replay = service.replay_event(rows["event"].id)
    attribution_replay = service.replay_attribution(rows["attribution"].id)
    signal_replay = service.replay_signal(rows["signal"].id)
    markdown = service.export_replay("signal", rows["signal"].id, fmt="markdown")

    assert article_replay["replayable"] is True
    assert event_replay["limitations"]["correlation_not_causation"] is True
    assert attribution_replay["input_entities"]["attribution_id"] == rows["attribution"].id
    assert signal_replay["operator_reviewed"] is True
    assert signal_replay["publication_status"] == "published"
    assert "Evidence Replay" in markdown

    integrity_match = service.integrity("article", rows["article"].id)
    assert integrity_match["matches"] is True
    rows["article"].title = "Mutated article title for integrity check"
    db.commit()
    integrity_mismatch = service.integrity("article", rows["article"].id)
    assert integrity_mismatch["matches"] is False
    assert EVIDENCE_REPLAY_REQUESTS_TOTAL._labelnames == ("entity_type",)
    assert EVIDENCE_REPLAY_FAILURES_TOTAL._labelnames == ("entity_type", "reason_code")
    assert EVIDENCE_INTEGRITY_CHECKS_TOTAL._labelnames == ("entity_type", "status")


def test_evidence_api_contracts() -> None:
    db = _session()
    rows = _seed_chain(db)
    packet = EvidencePacketBuilder(db).build("signal", rows["signal"].id)
    db.commit()

    def override() -> Session:
        return db

    app.dependency_overrides[db_session] = override
    client = TestClient(app, raise_server_exceptions=False)
    try:
        assert client.get("/api/v1/evidence/packets").status_code == 200
        packet_response = client.get(f"/api/v1/evidence/packets/{packet.id}")
        assert packet_response.status_code == 200
        assert packet_response.json()["data"]["correlation_not_causation"] is True
        assert (
            client.get(f"/api/v1/evidence/packets/{packet.id}?format=markdown").json()["format"]
            == "markdown"
        )
        assert client.get(f"/api/v1/evidence/packets/{packet.id}/timeline").status_code == 200
        relationships = client.get(f"/api/v1/evidence/packets/{packet.id}/relationships")
        assert relationships.status_code == 200
        assert len(relationships.json()["data"]) >= 4
        replay = client.get(f"/api/v1/evidence/replay/signal/{rows['signal'].id}")
        assert replay.status_code == 200
        assert replay.json()["data"]["correlation_not_causation"] is True
        assert (
            client.get(
                f"/api/v1/evidence/replay/signal/{rows['signal'].id}?format=markdown"
            ).json()["format"]
            == "markdown"
        )
        assert (
            client.get(f"/api/v1/evidence/replay/signal/{rows['signal'].id}/timeline").status_code
            == 200
        )
        assert (
            client.get(f"/api/v1/evidence/replay/signal/{rows['signal'].id}/integrity").status_code
            == 200
        )
    finally:
        app.dependency_overrides.clear()
