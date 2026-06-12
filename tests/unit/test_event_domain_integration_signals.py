import json

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db.base import Base
from app.db.models.event_outbox import EventOutbox
from app.db.models.intelligence_signals import IntelligenceSignalCandidate
from app.services.intelligence.operator_review_service import OperatorReviewService
from app.services.intelligence.signal_candidate_service import SignalCandidateService


def _session() -> Session:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    return Session(engine)


def _candidate() -> IntelligenceSignalCandidate:
    return IntelligenceSignalCandidate(
        signal_type="news_market_impact",
        source_entity_type="manual",
        source_entity_id=1,
        title="BTC market signal candidate",
        summary="Candidate uses informational BTC market context.",
        confidence_score=0.82,
        btc_relevance_score=0.88,
        source_confidence=0.9,
        provider_confidence=0.9,
        evidence_packet_id="manual:1",
    )


def _event_types(db: Session) -> list[str]:
    return [row.event_type for row in db.query(EventOutbox).order_by(EventOutbox.id).all()]


def test_creating_signal_candidate_emits_created_and_review_required_events() -> None:
    with _session() as db:
        created = SignalCandidateService(db)._persist_and_apply(_candidate())

        event_types = _event_types(db)
        assert "signal.created" in event_types
        assert "signal.operator_review_required" in event_types
        payload = json.loads(
            db.query(EventOutbox).filter_by(event_type="signal.created").one().payload_json
        )
        assert payload["signal_id"] == created.id
        assert payload["operator_review_required"] is True
        assert payload["not_financial_advice"] is True
        assert payload["no_auto_execution"] is True


def test_approving_and_rejecting_signal_reviews_emit_publication_events() -> None:
    with _session() as db:
        service = SignalCandidateService(db)
        published_candidate = service._persist_and_apply(_candidate())
        OperatorReviewService(db).review(
            published_candidate.id,
            "approved",
            reviewer_id=7,
            publish_override=True,
        )
        suppressed_candidate = service._persist_and_apply(
            IntelligenceSignalCandidate(
                signal_type="news_market_impact",
                source_entity_type="manual",
                source_entity_id=2,
                title="BTC market signal candidate",
                summary="Candidate uses informational BTC market context.",
                confidence_score=0.75,
                btc_relevance_score=0.8,
                source_confidence=0.8,
                provider_confidence=0.8,
                evidence_packet_id="manual:2",
            )
        )
        OperatorReviewService(db).review(suppressed_candidate.id, "rejected", reviewer_id=8)

        event_types = _event_types(db)
        assert "signal.published" in event_types
        assert "signal.suppressed" in event_types
        assert db.query(EventOutbox).filter_by(event_type="signal.published").count() == 1
        assert db.query(EventOutbox).filter_by(event_type="signal.suppressed").count() == 1
