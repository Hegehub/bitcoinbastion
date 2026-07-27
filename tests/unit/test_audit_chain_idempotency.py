from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.db.models.access import AccessAuditEvent
from app.services.access.audit_chain import AccessAuditChain


def test_duplicate_callback_returns_existing_semantic_event() -> None:
    engine = create_engine("sqlite:///:memory:")
    AccessAuditEvent.__table__.create(engine)
    with Session(engine) as db:
        chain = AccessAuditChain(db)
        first = chain.record_event(
            event_type="lnurl_payment_settled",
            object_hash="sha256:payment",
            idempotency_key_hash="sha256:callback",
        )
        second = chain.record_event(
            event_type="lnurl_payment_settled",
            object_hash="sha256:payment",
            idempotency_key_hash="sha256:callback",
        )
        assert first.id == second.id
        assert len(db.execute(select(AccessAuditEvent)).scalars().all()) == 1
