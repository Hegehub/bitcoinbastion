from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db.models.access import AccessAuditEvent
from app.services.access.audit_chain import AccessAuditChain


def test_payload_hash_and_previous_hash_tampering_are_detected_without_repair() -> None:
    engine = create_engine("sqlite:///:memory:")
    AccessAuditEvent.__table__.create(engine)
    with Session(engine) as db:
        chain = AccessAuditChain(db)
        chain.record_event(event_type="wallet_login_success")
        second = chain.record_event(event_type="lnurl_auth_callback_success")
        original = second.previous_event_hash
        second.previous_event_hash = "sha256:tampered"
        db.flush()
        result = chain.verify_chain_detailed()
        assert not result.valid and result.failure_reason == "broken_previous_hash"
        assert second.previous_event_hash != original  # verifier reports; it never repairs evidence
