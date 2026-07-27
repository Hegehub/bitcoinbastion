from datetime import UTC, datetime, timedelta
import base64

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from app.domain.access.wallet_entitlements import EntitlementLimits, EntitlementRestriction, EntitlementSubjectType
from app.services.access.wallet_entitlement_service import IssuerContext, PrincipalState, VerifiedPaymentProofRef, WalletBoundSubscriptionEntitlementService


def make_service_entitlement():
    key = Ed25519PrivateKey.generate()
    private = key.private_bytes(serialization.Encoding.Raw, serialization.PrivateFormat.Raw, serialization.NoEncryption())
    ctx = IssuerContext(base64.urlsafe_b64encode(private).decode().rstrip("="), "issuer-1")
    service = WalletBoundSubscriptionEntitlementService()
    entitlement = service.issue_wallet_bound_entitlement(
        principal=PrincipalState("hmac-sha256:p", EntitlementSubjectType.BITCOIN_WALLET_PRINCIPAL),
        verified_payment_proof=VerifiedPaymentProofRef("sha256:p", "pro_pass", 1, "bitcoin-mainnet", True, True, None, "hmac-sha256:p"),
        plan_code="pro_pass",
        payment_method="lnurl_pay",
        valid_from=datetime.now(UTC),
        valid_until=datetime.now(UTC)+timedelta(days=1),
        issuer_context=ctx,
    )
    return service, entitlement


def test_effective_entitlement_is_intersection_of_child_and_role_restrictions():
    service, entitlement = make_service_entitlement()
    child = EntitlementRestriction(scopes=frozenset({"market:intelligence:read"}), metric_groups=frozenset({"market.intelligence"}), limits=EntitlementLimits(10, 100, 50, 1000, 30, 3600, 0, 0))
    effective = service.resolve_effective_entitlement(entitlement=entitlement, child_api_key=child)
    assert effective.scopes == frozenset({"market:intelligence:read"})
    assert effective.metric_groups == frozenset({"market.intelligence"})
    assert effective.limits.requests_per_minute == 10
    assert effective.limits.minimum_interval_seconds == 3600


def test_revocation_override_and_recovery_lock_narrow_access():
    service, entitlement = make_service_entitlement()
    revoked = service.resolve_effective_entitlement(entitlement=entitlement, delegated_pass=EntitlementRestriction(revoked=True, reason="delegated_pass_revoked"))
    assert revoked.policy_decision == "deny"
    recovery = service.resolve_effective_entitlement(entitlement=entitlement, policy_context={"recovery_locked": True})
    assert recovery.scopes == frozenset()
    assert recovery.metric_groups == frozenset()
