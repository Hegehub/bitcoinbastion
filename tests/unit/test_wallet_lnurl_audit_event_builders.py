from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db.models.access import AccessAuditEvent
from app.services.access.audit_chain import AccessAuditChain
from app.services.wallet_auth.audit import WalletAuditEvent, WalletAuditWriter


def test_wallet_builder_uses_canonical_access_chain() -> None:
    engine = create_engine("sqlite:///:memory:")
    AccessAuditEvent.__table__.create(engine)
    with Session(engine) as db:
        event = WalletAuditWriter(AccessAuditChain(db)).record(
            WalletAuditEvent(
                event_type="wallet_proof_verification_success",
                event_status="success",
                principal_hash="hmac-sha256:principal",
                subject_hash="sha256:proof",
                reason_code="verified",
                proof_type="bip322",
                policy_hash="sha256:policy",
                idempotency_key_hash="sha256:idem",
            )
        )
        assert event.chain_id == "access-security"
        assert event.canonical_event_json["metadata"]["proof_type"] == "bip322"
