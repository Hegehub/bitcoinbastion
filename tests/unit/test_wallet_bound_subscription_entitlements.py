from datetime import UTC, datetime, timedelta

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from app.domain.access.plans import PlanCode
from app.domain.access.wallet_entitlements import EntitlementPaymentMethod, EntitlementSubjectType
from app.services.access.wallet_entitlement_service import (
    EntitlementPolicyError,
    IssuerContext,
    PrincipalState,
    VerifiedPaymentProofRef,
    WalletBoundSubscriptionEntitlementService,
)


def issuer() -> tuple[IssuerContext, str]:
    key = Ed25519PrivateKey.generate()
    private = key.private_bytes(serialization.Encoding.Raw, serialization.PrivateFormat.Raw, serialization.NoEncryption())
    public = key.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    import base64

    return IssuerContext(base64.urlsafe_b64encode(private).decode().rstrip("="), "issuer-1", base64.urlsafe_b64encode(public).decode().rstrip("=")), base64.urlsafe_b64encode(public).decode().rstrip("=")


def proof(plan="pro_pass", principal="hmac-sha256:principal", settled=True, verified=True):
    return VerifiedPaymentProofRef("sha256:proof" + plan, plan, 1000, "bitcoin-mainnet", settled, verified, datetime.now(UTC) + timedelta(days=1), principal)


def principal(kind=EntitlementSubjectType.BITCOIN_WALLET_PRINCIPAL, value="hmac-sha256:principal"):
    return PrincipalState(value, kind)


def test_verified_bitcoin_and_lightning_principal_issue_signed_wallet_entitlements():
    ctx, public = issuer()
    service = WalletBoundSubscriptionEntitlementService()
    btc = service.issue_wallet_bound_entitlement(principal=principal(), verified_payment_proof=proof(), plan_code=PlanCode.PRO, payment_method=EntitlementPaymentMethod.LNURL_PAY, valid_from=datetime.now(UTC), valid_until=datetime.now(UTC)+timedelta(days=365), issuer_context=ctx)
    assert btc.wallet_bound and btc.subject_type == EntitlementSubjectType.BITCOIN_WALLET_PRINCIPAL
    assert service.verify_entitlement(btc, public)
    lightning = service.issue_wallet_bound_entitlement(principal=principal(EntitlementSubjectType.LIGHTNING_WALLET_PRINCIPAL, "hmac-sha256:ln"), verified_payment_proof=proof("plus_pass", "hmac-sha256:ln"), plan_code=PlanCode.PLUS, payment_method="lnurl_pay", valid_from=datetime.now(UTC), valid_until=datetime.now(UTC)+timedelta(days=365), issuer_context=ctx)
    assert lightning.subject_type == EntitlementSubjectType.LIGHTNING_WALLET_PRINCIPAL


def test_unpaid_unverified_or_revoked_principal_cannot_issue_entitlement():
    ctx, _ = issuer()
    service = WalletBoundSubscriptionEntitlementService()
    with pytest.raises(EntitlementPolicyError, match="payment_proof_not_settled_or_verified"):
        service.issue_wallet_bound_entitlement(principal=principal(), verified_payment_proof=proof(settled=False), plan_code="pro_pass", payment_method="lnurl_pay", valid_from=datetime.now(UTC), valid_until=datetime.now(UTC)+timedelta(days=1), issuer_context=ctx)
    with pytest.raises(EntitlementPolicyError, match="principal_revoked_or_inactive"):
        service.issue_wallet_bound_entitlement(principal=PrincipalState("hmac-sha256:principal", EntitlementSubjectType.BITCOIN_WALLET_PRINCIPAL, revoked=True), verified_payment_proof=proof(), plan_code="pro_pass", payment_method="lnurl_pay", valid_from=datetime.now(UTC), valid_until=datetime.now(UTC)+timedelta(days=1), issuer_context=ctx)


def test_raw_subjects_and_manual_grants_are_rejected():
    ctx, _ = issuer()
    service = WalletBoundSubscriptionEntitlementService()
    with pytest.raises(EntitlementPolicyError, match="principal_hash_required"):
        service.issue_wallet_bound_entitlement(principal=principal(value="bc1qrawaddress"), verified_payment_proof=proof(principal="bc1qrawaddress"), plan_code="pro_pass", payment_method="lnurl_pay", valid_from=datetime.now(UTC), valid_until=datetime.now(UTC)+timedelta(days=1), issuer_context=ctx)
    with pytest.raises(EntitlementPolicyError, match="manual_grant_disabled"):
        service.issue_wallet_bound_entitlement(principal=principal(), verified_payment_proof=proof(), plan_code="pro_pass", payment_method="manual_grant", valid_from=datetime.now(UTC), valid_until=datetime.now(UTC)+timedelta(days=1), issuer_context=ctx)


def test_entitlement_contains_scopes_metrics_limits_assurance_and_epochs():
    ctx, _ = issuer()
    entitlement = WalletBoundSubscriptionEntitlementService().issue_wallet_bound_entitlement(principal=principal(), verified_payment_proof=proof(), plan_code="pro_pass", payment_method="lnurl_pay", valid_from=datetime.now(UTC), valid_until=datetime.now(UTC)+timedelta(days=1), issuer_context=ctx)
    assert "signals.advanced" in entitlement.metric_groups
    assert "signals:advanced:read" in entitlement.scopes
    assert entitlement.limits.daily_metric_credits == 250_000
    assert entitlement.assurance.access_certificate_required
    assert entitlement.schema_epoch == 2 and entitlement.policy_epoch == 1 and entitlement.crypto_epoch == 1
    assert entitlement.issuer_signatures[0].alg == "ed25519"
