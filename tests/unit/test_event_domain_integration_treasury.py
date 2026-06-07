import json

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db.base import Base
from app.db.models.event_outbox import EventOutbox
from app.db.repositories.treasury_repository import TreasuryRepository
from app.schemas.treasury import TreasuryApprovalActionIn, TreasuryRejectActionIn, TreasuryRequestIn
from app.services.treasury.treasury_service import TreasuryService


def _session() -> Session:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    return Session(engine)


def test_treasury_request_and_approval_emit_workflow_events() -> None:
    with _session() as db:
        service = TreasuryService(TreasuryRepository(db))
        created = service.create_request(
            TreasuryRequestIn(
                title="Ops transfer",
                amount_sats=500_000,
                destination_reference="vault-ops-1",
                wallet_health_score=85,
            ),
            requested_by=1,
        )
        created.required_approvals = 1
        TreasuryRepository(db).update(created)
        service.approve_request(
            created.id,
            10,
            TreasuryApprovalActionIn(wallet_health_score=85),
        )

        event_types = {row.event_type for row in db.query(EventOutbox).all()}
        assert "treasury.request.created" in event_types
        assert "treasury.approval.required" in event_types
        assert "treasury.request.approved" in event_types
        payload = json.loads(
            db.query(EventOutbox)
            .filter_by(event_type="treasury.request.approved")
            .one()
            .payload_json
        )
        assert payload["no_custody"] is True
        assert payload["no_auto_execution"] is True
        assert "workflow events" in payload["limitations"][0]


def test_treasury_rejection_emits_rejected_event() -> None:
    with _session() as db:
        service = TreasuryService(TreasuryRepository(db))
        created = service.create_request(
            TreasuryRequestIn(
                title="Reject transfer",
                amount_sats=300_000,
                destination_reference="vault-reject-1",
                wallet_health_score=80,
            ),
            requested_by=1,
        )
        service.reject_request(created.id, 11, TreasuryRejectActionIn(note="manual hold"))

        assert db.query(EventOutbox).filter_by(event_type="treasury.request.rejected").count() == 1
