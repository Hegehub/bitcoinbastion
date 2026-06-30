from fastapi import APIRouter, Depends
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from app.api.dependencies import db_session
from app.repositories.evidence_repository import EvidenceRepository
from app.services.intelligence.evidence_packet_builder import EvidencePacketBuilder
from app.services.intelligence.evidence_replay_service import EvidenceReplayService
from app.services.intelligence.market_memory.evidence import MarketMemoryEvidenceBuilder
from app.services.intelligence.market_memory.safety import MARKET_MEMORY_SAFETY_LIMITATIONS

router = APIRouter(prefix="/evidence", tags=["evidence"])

EVIDENCE_SAFETY_LIMITATIONS = [
    "Correlation-based attribution is not proof of causation.",
    "Evidence packets are replayable records, not financial advice.",
    "Replay failures and degraded providers must remain visible.",
]


@router.get("/packets")
def list_evidence_packets(limit: int = 50, db: Session = Depends(db_session)) -> dict[str, object]:
    rows = EvidenceRepository(db).list_packets(limit=min(max(limit, 1), 100))
    builder = EvidencePacketBuilder(db)
    return {
        "data": [builder.packet_payload(row) for row in rows],
        "limitations": EVIDENCE_SAFETY_LIMITATIONS,
    }


@router.get("/packets/{packet_id}")
def get_evidence_packet(
    packet_id: int, format: str = "json", db: Session = Depends(db_session)
) -> dict[str, object]:
    packet = EvidenceRepository(db).get_packet(packet_id)
    if packet is None:
        return {
            "data": None,
            "limitations": EVIDENCE_SAFETY_LIMITATIONS + ["Evidence packet was not found."],
        }
    builder = EvidencePacketBuilder(db)
    if format == "markdown":
        return {
            "format": "markdown",
            "content": builder.export_packet(packet, fmt="markdown"),
            "limitations": EVIDENCE_SAFETY_LIMITATIONS,
        }
    return {"data": builder.packet_payload(packet), "limitations": EVIDENCE_SAFETY_LIMITATIONS}


@router.get("/packets/{packet_id}/timeline")
def get_evidence_packet_timeline(
    packet_id: int, db: Session = Depends(db_session)
) -> dict[str, object]:
    packet = EvidenceRepository(db).get_packet(packet_id)
    if packet is None:
        return {
            "data": [],
            "limitations": EVIDENCE_SAFETY_LIMITATIONS + ["Evidence packet was not found."],
        }
    return {
        "data": EvidencePacketBuilder(db).timeline_for(
            packet.source_entity_type, packet.source_entity_id
        ),
        "limitations": EVIDENCE_SAFETY_LIMITATIONS,
    }


@router.get("/packets/{packet_id}/relationships")
def get_evidence_packet_relationships(
    packet_id: int, db: Session = Depends(db_session)
) -> dict[str, object]:
    packet = EvidenceRepository(db).get_packet(packet_id)
    if packet is None:
        return {
            "data": [],
            "limitations": EVIDENCE_SAFETY_LIMITATIONS + ["Evidence packet was not found."],
        }
    builder = EvidencePacketBuilder(db)
    rows = builder.relationship_chain(packet.source_entity_type, packet.source_entity_id)
    return {
        "data": [builder.relationship_payload(row) for row in rows],
        "limitations": EVIDENCE_SAFETY_LIMITATIONS,
    }


@router.get("/replay/{entity_type}/{entity_id}")
def replay_evidence(
    entity_type: str, entity_id: int, format: str = "json", db: Session = Depends(db_session)
) -> dict[str, object]:
    service = EvidenceReplayService(db)
    if format == "markdown":
        content = service.export_replay(entity_type, entity_id, fmt="markdown")
        db.commit()
        return {
            "format": "markdown",
            "content": content,
            "limitations": EVIDENCE_SAFETY_LIMITATIONS,
        }
    payload = service.replay(entity_type, entity_id)
    db.commit()
    return {"data": payload, "limitations": EVIDENCE_SAFETY_LIMITATIONS}


@router.get("/replay/{entity_type}/{entity_id}/timeline")
def replay_evidence_timeline(
    entity_type: str, entity_id: int, db: Session = Depends(db_session)
) -> dict[str, object]:
    return {
        "data": EvidenceReplayService(db).replay_timeline(entity_type, entity_id),
        "limitations": EVIDENCE_SAFETY_LIMITATIONS,
    }


@router.get("/replay/{entity_type}/{entity_id}/integrity")
def replay_evidence_integrity(
    entity_type: str, entity_id: int, db: Session = Depends(db_session)
) -> dict[str, object]:
    payload = EvidenceReplayService(db).integrity(entity_type, entity_id)
    db.commit()
    return {"data": payload, "limitations": EVIDENCE_SAFETY_LIMITATIONS}


@router.get("/market-memory/{event_id}")
def get_market_memory_evidence(
    event_id: int, limit: int = 10, db: Session = Depends(db_session)
) -> dict[str, object]:
    try:
        payload = MarketMemoryEvidenceBuilder(db).payload(event_id, limit=limit)
        db.commit()
        return {"data": payload, "limitations": payload["limitations"]}
    except OperationalError:
        return {
            "data": None,
            "limitations": MARKET_MEMORY_SAFETY_LIMITATIONS
            + ["Market memory evidence storage is unavailable."],
        }
