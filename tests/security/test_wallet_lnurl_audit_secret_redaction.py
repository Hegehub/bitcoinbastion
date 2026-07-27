import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db.models.access import AccessAuditEvent
from app.services.access.audit_chain import AccessAuditChain


def test_rejected_secret_is_not_persisted_or_echoed() -> None:
    engine = create_engine("sqlite:///:memory:")
    AccessAuditEvent.__table__.create(engine)
    raw = "lnbc1rawinvoice-not-real"
    with Session(engine) as db:
        with pytest.raises(ValueError) as error:
            AccessAuditChain(db).record_event(
                event_type="lnurl_invoice_issued", metadata={"invoice": raw}
            )
        assert raw not in str(error.value)
        assert db.query(AccessAuditEvent).count() == 0
