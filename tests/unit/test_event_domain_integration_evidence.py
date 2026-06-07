import json

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db.base import Base
from app.db.models.event_outbox import EventOutbox
from app.db.models.intelligence_signals import IntelligenceSignalCandidate
from app.services.intelligence.evidence_packet_builder import EvidencePacketBuilder
from app.services.intelligence.evidence_replay_service import EvidenceReplayService


def _session() -> Session:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    return Session(engine)


def _signal(db: Session) -> IntelligenceSignalCandidate:
    candidate = IntelligenceSignalCandidate(
        signal_type="news_market_impact",
        source_entity_type="manual",
        source_entity_id=1,
        title="BTC market signal candidate",
        summary="Candidate uses informational BTC market context.",
        confidence_score=0.72,
        status="pending_review",
        requires_operator_review=True,
    )
    db.add(candidate)
    db.commit()
    db.refresh(candidate)
    return candidate


def test_evidence_packet_creation_emits_outbox_event() -> None:
    with _session() as db:
        candidate = _signal(db)
        packet = EvidencePacketBuilder(db).build("signal", candidate.id)

        event = db.query(EventOutbox).filter_by(event_type="evidence.packet.created").one()
        payload = json.loads(event.payload_json)
        assert payload["packet_id"] == packet.id
        assert payload["evidence_based"] is True
        assert payload["replayable"] is True


def test_evidence_replay_success_emits_completed_event() -> None:
    with _session() as db:
        candidate = _signal(db)
        EvidencePacketBuilder(db).build("signal", candidate.id)
        replay = EvidenceReplayService(db).replay("signal", candidate.id)

        event = db.query(EventOutbox).filter_by(event_type="evidence.replay.completed").one()
        payload = json.loads(event.payload_json)
        assert payload["replay_status"] == "completed"
        assert payload["source_entity_id"] == replay["entity_id"]
