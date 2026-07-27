from datetime import UTC, datetime, timedelta

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
import base64

from app.domain.access.wallet_entitlements import EntitlementSubjectType
from app.services.access.wallet_entitlement_service import EntitlementPolicyError, IssuerContext, PrincipalState, VerifiedPaymentProofRef, WalletBoundSubscriptionEntitlementService


def ctx():
    key = Ed25519PrivateKey.generate()
    private = key.private_bytes(serialization.Encoding.Raw, serialization.PrivateFormat.Raw, serialization.NoEncryption())
    return IssuerContext(base64.urlsafe_b64encode(private).decode().rstrip("="), "issuer-1")


def test_settled_lnurl_payment_binds_idempotently_to_lightning_principal():
    service = WalletBoundSubscriptionEntitlementService()
    payment = VerifiedPaymentProofRef("sha256:proof", "pro_pass", 1000, "bitcoin-mainnet", True, True, datetime.now(UTC)+timedelta(days=1), "hmac-sha256:ln")
    principal = PrincipalState("hmac-sha256:ln", EntitlementSubjectType.LIGHTNING_WALLET_PRINCIPAL)
    first = service.issue_wallet_bound_entitlement(principal=principal, verified_payment_proof=payment, plan_code="pro_pass", payment_method="lnurl_pay", valid_from=datetime.now(UTC), valid_until=datetime.now(UTC)+timedelta(days=30), issuer_context=ctx())
    second = service.issue_wallet_bound_entitlement(principal=principal, verified_payment_proof=payment, plan_code="pro_pass", payment_method="lnurl_pay", valid_from=datetime.now(UTC), valid_until=datetime.now(UTC)+timedelta(days=30), issuer_context=ctx())
    assert first.entitlement_id_hash == second.entitlement_id_hash


def test_payerdata_auth_mismatch_rejects_automatic_binding_and_email_is_ignored():
    service = WalletBoundSubscriptionEntitlementService()
    payment = VerifiedPaymentProofRef("sha256:proof", "pro_pass", 1000, "bitcoin-mainnet", True, True, datetime.now(UTC)+timedelta(days=1), "hmac-sha256:other", payerdata_auth_hash="sha256:auth")
    with pytest.raises(EntitlementPolicyError, match="payerdata_auth_binding_mismatch"):
        service.issue_wallet_bound_entitlement(principal=PrincipalState("hmac-sha256:ln", EntitlementSubjectType.LIGHTNING_WALLET_PRINCIPAL), verified_payment_proof=payment, plan_code="pro_pass", payment_method="lnurl_pay", valid_from=datetime.now(UTC), valid_until=datetime.now(UTC)+timedelta(days=30), issuer_context=ctx())


def test_payment_proof_cannot_be_reused_for_unrelated_principal():
    service = WalletBoundSubscriptionEntitlementService()
    payment = VerifiedPaymentProofRef("sha256:proof", "pro_pass", 1000, "bitcoin-mainnet", True, True, None, "hmac-sha256:a")
    service.issue_wallet_bound_entitlement(principal=PrincipalState("hmac-sha256:a", EntitlementSubjectType.LIGHTNING_WALLET_PRINCIPAL), verified_payment_proof=payment, plan_code="pro_pass", payment_method="lnurl_pay", valid_from=datetime.now(UTC), valid_until=datetime.now(UTC)+timedelta(days=30), issuer_context=ctx())
    with pytest.raises(EntitlementPolicyError, match="payment_proof_binding_conflict"):
        service.issue_wallet_bound_entitlement(principal=PrincipalState("hmac-sha256:b", EntitlementSubjectType.LIGHTNING_WALLET_PRINCIPAL), verified_payment_proof=payment, plan_code="pro_pass", payment_method="lnurl_pay", valid_from=datetime.now(UTC), valid_until=datetime.now(UTC)+timedelta(days=30), issuer_context=ctx())
