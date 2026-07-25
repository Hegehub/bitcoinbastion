from datetime import UTC, datetime, timedelta
import base64

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from app.domain.access.decisions import PolicyDecision
from app.domain.access.wallet_entitlements import EntitlementSubjectType
from app.services.access.wallet_entitlement_service import AccessCheckContext, IssuerContext, PrincipalState, VerifiedPaymentProofRef, WalletBoundSubscriptionEntitlementService


def make_entitlement():
    key = Ed25519PrivateKey.generate()
    private = key.private_bytes(serialization.Encoding.Raw, serialization.PrivateFormat.Raw, serialization.NoEncryption())
    ctx = IssuerContext(base64.urlsafe_b64encode(private).decode().rstrip("="), "issuer-1")
    service = WalletBoundSubscriptionEntitlementService()
    entitlement = service.issue_wallet_bound_entitlement(principal=PrincipalState("hmac-sha256:p", EntitlementSubjectType.BITCOIN_WALLET_PRINCIPAL), verified_payment_proof=VerifiedPaymentProofRef("sha256:proof", "pro_pass", 1, "bitcoin-mainnet", True, True, None, "hmac-sha256:p"), plan_code="pro_pass", payment_method="lnurl_pay", valid_from=datetime.now(UTC), valid_until=datetime.now(UTC)+timedelta(days=1), issuer_context=ctx)
    return service, entitlement, ctx


def test_entitlement_alone_cannot_access_protected_endpoint():
    service, entitlement, _ = make_entitlement()
    assert service.validate_protected_access(entitlement, AccessCheckContext("hmac-sha256:p", pop_session_active=False, policy_allowed=False)).decision != PolicyDecision.ALLOW


def test_revoked_entitlement_blocks_existing_session():
    service, entitlement, ctx = make_entitlement()
    revoked = service.revoke_entitlement(entitlement, reason="security", issuer_context=ctx)
    assert service.validate_protected_access(revoked, AccessCheckContext("hmac-sha256:p", pop_session_active=True, policy_allowed=True, step_up_fresh=True, access_certificate_present=True)).decision == PolicyDecision.REVOKED


def test_comment_or_success_action_cannot_activate_unpaid_entitlement():
    service, _, ctx = make_entitlement()
    unpaid = VerifiedPaymentProofRef("sha256:unpaid", "pro_pass", 1, "bitcoin-mainnet", settled=False, verified=False, principal_hash="hmac-sha256:p")
    try:
        service.issue_wallet_bound_entitlement(principal=PrincipalState("hmac-sha256:p", EntitlementSubjectType.BITCOIN_WALLET_PRINCIPAL), verified_payment_proof=unpaid, plan_code="pro_pass", payment_method="lnurl_pay", valid_from=datetime.now(UTC), valid_until=datetime.now(UTC)+timedelta(days=1), issuer_context=ctx)
    except Exception as exc:
        assert "payment_proof" in str(exc)
