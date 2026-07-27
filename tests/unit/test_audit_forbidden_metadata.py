import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db.models.access import AccessAuditEvent
from app.services.access.audit_chain import AccessAuditChain


@pytest.mark.parametrize(
    "metadata",
    [
        {"raw_k1": "ab" * 32},
        {"wallet_address": "bc1q-not-real"},
        {"raw_signature": "3044"},
        {"bolt11": "lnbc1notreal"},
        {"preimage": "11" * 32},
        {"payer_data": {"email": "person@example.invalid"}},
        {"comment": "<script>unsafe</script>"},
        {"note": "abandon " * 11 + "about"},
        {"key": "xprv-not-real"},
    ],
)
def test_forbidden_wallet_lnurl_material_is_rejected(metadata: dict[str, object]) -> None:
    engine = create_engine("sqlite:///:memory:")
    AccessAuditEvent.__table__.create(engine)
    with Session(engine) as db, pytest.raises(ValueError, match="forbidden_audit_secret"):
        AccessAuditChain(db).record_event(event_type="wallet_login_failed", metadata=metadata)
