from datetime import UTC, datetime, timedelta
import base64

import pytest
from dataclasses import replace
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from app.domain.access.wallet_entitlements import EntitlementSubjectType
from app.services.access.wallet_entitlement_service import EntitlementPolicyError, EntitlementSignatureVerificationError, IssuerContext, PrincipalState, VerifiedPaymentProofRef, WalletBoundSubscriptionEntitlementService


def issuer():
    key = Ed25519PrivateKey.generate()
    private = key.private_bytes(serialization.Encoding.Raw, serialization.PrivateFormat.Raw, serialization.NoEncryption())
    public = key.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    return IssuerContext(base64.urlsafe_b64encode(private).decode().rstrip("="), "issuer-1"), base64.urlsafe_b64encode(public).decode().rstrip("=")


def test_raw_lnurl_key_and_lightning_address_are_not_subject_identity():
    ctx, _ = issuer()
    service = WalletBoundSubscriptionEntitlementService()
    for raw in ["03abcdef", "merchant@example.com"]:
        with pytest.raises(EntitlementPolicyError, match="principal_hash_required"):
            service.issue_wallet_bound_entitlement(principal=PrincipalState(raw, EntitlementSubjectType.LIGHTNING_WALLET_PRINCIPAL), verified_payment_proof=VerifiedPaymentProofRef("sha256:p"+raw, "basic_pass", 1, "bitcoin-mainnet", True, True, None, raw), plan_code="basic_pass", payment_method="lnurl_pay", valid_from=datetime.now(UTC), valid_until=datetime.now(UTC)+timedelta(days=1), issuer_context=ctx)


def test_unsigned_tampered_and_fake_pq_entitlements_are_rejected():
    ctx, public = issuer()
    service = WalletBoundSubscriptionEntitlementService()
    entitlement = service.issue_wallet_bound_entitlement(principal=PrincipalState("hmac-sha256:p", EntitlementSubjectType.BITCOIN_WALLET_PRINCIPAL), verified_payment_proof=VerifiedPaymentProofRef("sha256:p", "basic_pass", 1, "bitcoin-mainnet", True, True, None, "hmac-sha256:p"), plan_code="basic_pass", payment_method="lnurl_pay", valid_from=datetime.now(UTC), valid_until=datetime.now(UTC)+timedelta(days=1), issuer_context=ctx)
    unsigned = replace(entitlement, issuer_signatures=())
    assert not service.verify_entitlement(unsigned, public)
    tampered = replace(entitlement, plan_code="enterprise_pass")
    assert not service.verify_entitlement(tampered, public)
    fake_pq_signature = type(entitlement.issuer_signatures[0])("ml_dsa_65", "issuer-1", entitlement.issuer_signatures[0].sig, 1)
    fake = replace(entitlement, issuer_signatures=(fake_pq_signature,))
    with pytest.raises(EntitlementSignatureVerificationError, match="unsupported_signature_suite"):
        service.verify_entitlement(fake, public)
