from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.db.models.access import AccessAuditEvent
from app.services.access.audit_chain import AccessAuditChain
from app.services.wallet_auth.audit import WalletAuditEvent, WalletAuditWriter


def test_wallet_lnurl_payment_entitlement_and_revocation_share_one_chain() -> None:
    engine = create_engine("sqlite:///:memory:")
    AccessAuditEvent.__table__.create(engine)
    with Session(engine) as db:
        chain = AccessAuditChain(db)
        WalletAuditWriter(chain).record(
            WalletAuditEvent(
                event_type="wallet_login_success",
                event_status="success",
                principal_hash="hmac:principal",
            )
        )
        chain.record_event(
            event_type="lnurl_invoice_issued",
            object_hash="sha256:invoice",
            event_category="payment",
        )
        chain.record_event(
            event_type="lnurl_payment_settled",
            object_hash="sha256:payment",
            event_category="payment",
        )
        chain.record_event(
            event_type="lnurl_entitlement_issued",
            object_hash="sha256:entitlement",
            event_category="entitlement",
        )
        chain.record_event(
            event_type="wallet_principal_revoked",
            actor_hash="hmac:principal",
            event_status="revoked",
        )
        rows = list(
            db.execute(
                select(AccessAuditEvent).order_by(AccessAuditEvent.sequence_number)
            ).scalars()
        )
        assert [row.event_type for row in rows][1:4] == [
            "lnurl_invoice_issued",
            "lnurl_payment_settled",
            "lnurl_entitlement_issued",
        ]
        assert len({row.chain_id for row in rows}) == 1
        assert chain.verify_chain_detailed().valid
