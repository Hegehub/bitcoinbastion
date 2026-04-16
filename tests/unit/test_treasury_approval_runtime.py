from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db.base import Base
from app.db.repositories.audit_repository import AuditRepository
from app.db.repositories.treasury_repository import TreasuryRepository
from app.schemas.treasury import TreasuryApprovalActionIn, TreasuryRejectActionIn, TreasuryRequestIn
from app.services.treasury.treasury_service import TreasuryService


def test_treasury_approval_runtime_tracks_quorum_and_status() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(bind=engine)

    with Session(engine) as db:
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

        # Force quorum scenario for runtime approval checks.
        created.required_approvals = 2
        TreasuryRepository(db).update(created)

        step_one = service.approve_request(
            request_id=created.id,
            approver_user_id=10,
            payload=TreasuryApprovalActionIn(wallet_health_score=85),
        )
        step_two = service.approve_request(
            request_id=created.id,
            approver_user_id=11,
            payload=TreasuryApprovalActionIn(wallet_health_score=85),
        )

    assert step_one.status == "awaiting_approval"
    assert step_one.approved_count == 1
    assert step_two.status == "approved"
    assert step_two.approved_count == 2

    with Session(engine) as db:
        logs = AuditRepository(db).list_recent(limit=10)
    actions = {item.action for item in logs}
    assert "treasury.request.create" in actions
    assert "treasury.request.approve" in actions


def test_treasury_reject_runtime_sets_rejected_and_audits() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(bind=engine)

    with Session(engine) as db:
        service = TreasuryService(TreasuryRepository(db))
        created = service.create_request(
            TreasuryRequestIn(
                title="Reject me",
                amount_sats=300_000,
                destination_reference="vault-reject-1",
                wallet_health_score=80,
            ),
            requested_by=1,
        )
        rejected = service.reject_request(
            request_id=created.id,
            actor_user_id=99,
            payload=TreasuryRejectActionIn(note="policy override"),
        )

    assert rejected.status == "rejected"

    with Session(engine) as db:
        logs = AuditRepository(db).list_recent(limit=10)
    assert any(item.action == "treasury.request.reject" for item in logs)
