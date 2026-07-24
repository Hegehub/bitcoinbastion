from datetime import UTC, datetime, timedelta
import base64

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from app.domain.access.wallet_entitlements import EntitlementSubjectType
from app.services.access.wallet_entitlement_service import EntitlementPolicyError, IssuerContext, PrincipalState, VerifiedPaymentProofRef, WalletBoundSubscriptionEntitlementService


def ctx():
    key = Ed25519PrivateKey.generate()
    private = key.private_bytes(serialization.Encoding.Raw, serialization.PrivateFormat.Raw, serialization.NoEncryption())
    return IssuerContext(base64.urlsafe_b64encode(private).decode().rstrip("="), "issuer-1")


def test_duplicate_settlement_notification_does_not_duplicate_entitlement():
    issuer_ctx = ctx()
    service = WalletBoundSubscriptionEntitlementService()
    payment = VerifiedPaymentProofRef("sha256:proof", "basic_pass", 1, "bitcoin-mainnet", True, True, None, "hmac-sha256:p")
    args = dict(principal=PrincipalState("hmac-sha256:p", EntitlementSubjectType.BITCOIN_WALLET_PRINCIPAL), verified_payment_proof=payment, plan_code="basic_pass", payment_method="lnurl_pay", valid_from=datetime.now(UTC), valid_until=datetime.now(UTC)+timedelta(days=1), issuer_context=issuer_ctx)
    first = service.issue_wallet_bound_entitlement(**args)
    second = service.issue_wallet_bound_entitlement(**args)
    assert first is second
    assert len(service.repository.by_entitlement_hash) == 1


def test_same_payment_proof_cannot_issue_incompatible_plan():
    issuer_ctx = ctx()
    service = WalletBoundSubscriptionEntitlementService()
    service.issue_wallet_bound_entitlement(principal=PrincipalState("hmac-sha256:p", EntitlementSubjectType.BITCOIN_WALLET_PRINCIPAL), verified_payment_proof=VerifiedPaymentProofRef("sha256:proof", "basic_pass", 1, "bitcoin-mainnet", True, True, None, "hmac-sha256:p"), plan_code="basic_pass", payment_method="lnurl_pay", valid_from=datetime.now(UTC), valid_until=datetime.now(UTC)+timedelta(days=1), issuer_context=issuer_ctx)
    with pytest.raises(EntitlementPolicyError, match="payment_proof_binding_conflict"):
        service.issue_wallet_bound_entitlement(principal=PrincipalState("hmac-sha256:p", EntitlementSubjectType.BITCOIN_WALLET_PRINCIPAL), verified_payment_proof=VerifiedPaymentProofRef("sha256:proof", "pro_pass", 1, "bitcoin-mainnet", True, True, None, "hmac-sha256:p"), plan_code="pro_pass", payment_method="lnurl_pay", valid_from=datetime.now(UTC), valid_until=datetime.now(UTC)+timedelta(days=1), issuer_context=issuer_ctx)
