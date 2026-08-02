from datetime import UTC, datetime, timedelta
import base64

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from app.domain.access.decisions import PolicyDecision
from app.domain.access.wallet_entitlements import EntitlementSubjectType
from app.services.access.wallet_entitlement_service import AccessCheckContext, IssuerContext, PrincipalState, VerifiedPaymentProofRef, WalletBoundSubscriptionEntitlementService


def issuer():
    key = Ed25519PrivateKey.generate()
    private = key.private_bytes(serialization.Encoding.Raw, serialization.PrivateFormat.Raw, serialization.NoEncryption())
    public = key.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    return IssuerContext(base64.urlsafe_b64encode(private).decode().rstrip("="), "issuer-1", base64.urlsafe_b64encode(public).decode().rstrip("=")), base64.urlsafe_b64encode(public).decode().rstrip("=")


def test_wallet_entitlement_policy_flow_requires_pop_policy_scope_metric_and_quota():
    ctx, public = issuer()
    service = WalletBoundSubscriptionEntitlementService()
    entitlement = service.issue_wallet_bound_entitlement(principal=PrincipalState("hmac-sha256:p", EntitlementSubjectType.BITCOIN_WALLET_PRINCIPAL), verified_payment_proof=VerifiedPaymentProofRef("sha256:proof", "pro_pass", 1, "bitcoin-mainnet", True, True, None, "hmac-sha256:p"), plan_code="pro_pass", payment_method="lnurl_pay", valid_from=datetime.now(UTC), valid_until=datetime.now(UTC)+timedelta(days=30), issuer_context=ctx)
    assert service.verify_entitlement(entitlement, public)
    denied = service.validate_protected_access(entitlement, AccessCheckContext("hmac-sha256:p", pop_session_active=False, policy_allowed=True))
    assert denied.decision == PolicyDecision.INVALID_SESSION
    allowed = service.validate_protected_access(entitlement, AccessCheckContext("hmac-sha256:p", pop_session_active=True, policy_allowed=True, requested_scope="signals:advanced:read", requested_metric_group="signals.advanced", step_up_fresh=True, access_certificate_present=True, quota_remaining=10, quota_cost=1))
    assert allowed.decision == PolicyDecision.ALLOW
    quota = service.validate_protected_access(entitlement, AccessCheckContext("hmac-sha256:p", pop_session_active=True, policy_allowed=True, requested_scope="signals:advanced:read", requested_metric_group="signals.advanced", step_up_fresh=True, access_certificate_present=True, quota_remaining=0, quota_cost=1))
    assert quota.decision == PolicyDecision.QUOTA_EXCEEDED
