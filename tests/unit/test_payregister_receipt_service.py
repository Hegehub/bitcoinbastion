from datetime import UTC, datetime

from app.domain.payregister_lnurl.statuses import PayRegisterReceiptStatus
from app.services.access.crypto.hashing import sha256_prefixed
from app.services.payregister.context_integrity import compute_context_hash
from app.services.payregister.receipt_service import PayRegisterReceiptInput, PayRegisterReceiptService
from tests.unit.test_payregister_context_builder import role_context
from app.services.payregister.lnurl_context import PayRegisterContextBuildRequest, PayRegisterContextBuilder


def test_receipt_issued_only_with_hashed_references_and_idempotent():
    context = PayRegisterContextBuilder().build_context(PayRegisterContextBuildRequest(role_context=role_context(), terminal_device_fingerprint="sha256:device", amount_msat=2500))
    service = PayRegisterReceiptService()
    request = PayRegisterReceiptInput(context=context, payment_proof_hash=sha256_prefixed("proof"), lnurl_payment_request_hash=sha256_prefixed(context.context_id), settled_at=datetime.now(UTC), audit_event_hash=sha256_prefixed("audit"))
    receipt = service.issue_receipt(request)
    receipt_again = service.issue_receipt(request)
    assert receipt.receipt_id == receipt_again.receipt_id
    assert receipt.status == PayRegisterReceiptStatus.ISSUED
    assert receipt.shift_hash == context.shift_hash
    assert receipt.metadata_hash == context.metadata_hash
    assert compute_context_hash(context).startswith("sha256:")
