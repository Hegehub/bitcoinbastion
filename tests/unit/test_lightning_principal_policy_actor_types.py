from datetime import UTC, datetime, timedelta

from app.domain.access.plans import PlanCode
from app.services.access.policy_context import AccessPolicyContext, AuthenticationAssuranceLevel, PolicyActorType, PolicyAuthMethod
from app.services.access.policy_engine import AccessPolicyEngine
import app.services.access.policy_reasons as reasons


def ctx(**overrides):
    base = dict(
        actor_type=PolicyActorType.LIGHTNING_WALLET_PRINCIPAL,
        actor_hash="hmac:actor",
        principal_hash="hmac:principal",
        auth_methods=frozenset({PolicyAuthMethod.LNURL_AUTH, PolicyAuthMethod.DEVICE_POP, PolicyAuthMethod.SESSION_POP}),
        authentication_assurance=AuthenticationAssuranceLevel.STANDARD,
        lnurl_k1_status="used",
        lnurl_auth_action="login",
        lnurl_auth_domain="auth.example",
        auth_domain="auth.example",
        session_id_hash="sha256:session",
        session_expires_at=datetime.now(UTC) + timedelta(minutes=5),
        device_id="sha256:device",
        plan_code=PlanCode.PRO,
        effective_scopes={"signals:standard:read", "api:keys:manage", "payregister:payment:create"},
        requested_scope="signals:standard:read",
        requested_metric_group="signals.standard",
        metric_entitlements={"groups": ["signals.standard"]},
        quota_state={"remaining": 10},
        requested_action="read_metric",
        resource_type="metric_query",
        resource_hash="sha256:metric",
    )
    base.update(overrides)
    return AccessPolicyContext(**base)


def decision(**overrides):
    return AccessPolicyEngine().evaluate(ctx(**overrides))


def test_actor_typing_and_unknown_denial_and_lightning_address_not_identity():
    assert decision().actor_type == PolicyActorType.LIGHTNING_WALLET_PRINCIPAL
    assert decision(actor_type=PolicyActorType.BITCOIN_WALLET_PRINCIPAL, auth_methods=frozenset({PolicyAuthMethod.BIP322, PolicyAuthMethod.DEVICE_POP, PolicyAuthMethod.SESSION_POP})).actor_type == PolicyActorType.BITCOIN_WALLET_PRINCIPAL
    assert decision(actor_type=PolicyActorType.ACCESS_CERTIFICATE, auth_methods=frozenset({PolicyAuthMethod.ACCESS_CERTIFICATE, PolicyAuthMethod.DEVICE_POP, PolicyAuthMethod.SESSION_POP}), access_certificate_fingerprint="sha256:cert").allowed
    assert decision(actor_type="lightning_address", auth_methods=frozenset()).reason_code == reasons.UNKNOWN_ACTOR_TYPE
    assert decision(auth_methods=frozenset(), lightning_address_hash="hmac:lnaddr").reason_code == reasons.LIGHTNING_ADDRESS_NOT_IDENTITY


def test_lnurl_auth_requires_device_session_entitlement_and_clean_k1():
    assert decision().allowed
    assert decision(auth_methods=frozenset({PolicyAuthMethod.LNURL_AUTH}), session_id_hash=None).reason_code == reasons.SESSION_MISSING
    assert decision(lnurl_k1_status="reused").reason_code == reasons.LNURL_K1_REUSED
    assert decision(lnurl_k1_status="expired").reason_code == reasons.LNURL_K1_EXPIRED
    assert decision(lnurl_auth_domain="other.example").reason_code == reasons.LNURL_DOMAIN_MISMATCH
    assert decision(lnurl_auth_action="withdraw").reason_code == reasons.LNURL_ACTION_MISMATCH
    assert decision(actor_status="revoked").reason_code == reasons.PRINCIPAL_REVOKED


def test_assurance_step_up_and_sovereign_rules():
    assert decision(requested_action="login", requested_scope=None, requested_metric_group=None).allowed
    assert decision(authentication_assurance=AuthenticationAssuranceLevel.COMPATIBILITY, requested_action="create_api_key", requested_scope="api:keys:manage").reason_code == reasons.WALLET_PROOF_TOO_WEAK
    assert decision(requested_action="create_api_key", requested_scope="api:keys:manage").decision == "step_up_required"
    assert decision(actor_type=PolicyActorType.BITCOIN_WALLET_PRINCIPAL, auth_methods=frozenset({PolicyAuthMethod.BIP322}), authentication_assurance=AuthenticationAssuranceLevel.STANDARD, requested_action="sovereign_policy_change", requested_scope=None, requested_metric_group=None).decision == "quorum_required"


def test_treasury_separation_and_bitcoin_legacy_limit():
    assert decision(requested_action="treasury_policy_change", requested_scope="treasury:policy:read", effective_scopes={"treasury:policy:read"}).reason_code == reasons.LIGHTNING_PRINCIPAL_NOT_TREASURY_PROOF
    legacy = decision(actor_type=PolicyActorType.BITCOIN_WALLET_PRINCIPAL, auth_methods=frozenset({PolicyAuthMethod.LEGACY_BITCOIN_MESSAGE}), authentication_assurance=AuthenticationAssuranceLevel.COMPATIBILITY, requested_action="treasury_policy_change", requested_scope="treasury:policy:read", effective_scopes={"treasury:policy:read"})
    assert legacy.reason_code == reasons.LEGACY_SIGNATURE_NOT_ALLOWED


def test_subscription_metrics_payment_and_child_delegated_bot_rules():
    assert decision().allowed
    assert decision(plan_code=PlanCode.LITE, metric_entitlements={"groups": []}).decision == "upgrade_required"
    assert decision(entitlement_status="expired").reason_code == reasons.ENTITLEMENT_EXPIRED
    assert decision(lnurl_operation="pay", lnurl_payment_status="invoice_created").decision == "payment_not_settled"
    child = decision(actor_type=PolicyActorType.CHILD_API_KEY, auth_methods=frozenset({PolicyAuthMethod.CHILD_API_KEY}), parent_actor_status="active", metadata={"parent_scopes": {"signals:standard:read"}, "delegated_scopes": {"api:keys:manage"}})
    assert child.reason_code == reasons.CHILD_SCOPE_EXCEEDS_PARENT
    assert decision(actor_type=PolicyActorType.DELEGATED_PASS, auth_methods=frozenset({PolicyAuthMethod.DELEGATED_PASS}), requested_action="create_api_key", requested_scope="api:keys:manage", metadata={"delegated_scopes": {"api:keys:manage"}, "parent_scopes": {"api:keys:manage"}}).decision == "step_up_required"
    assert decision(actor_type=PolicyActorType.BOT, auth_methods=frozenset({PolicyAuthMethod.CHILD_API_KEY}), requested_action="complete_recovery", requested_scope=None, requested_metric_group=None, metadata={"delegated_scopes": set(), "parent_scopes": set()}).reason_code == reasons.WALLET_PROOF_TOO_WEAK


def test_business_payregister_recovery_lockdown_and_privacy():
    assert decision(actor_type=PolicyActorType.PAYREGISTER_DEVICE, requested_scope="payregister:payment:create", requested_action="create_payment_intent", requested_metric_group=None, business_role="cashier").allowed
    assert decision(requested_scope="payregister:admin", effective_scopes={"payregister:admin"}, requested_metric_group=None, business_role="cashier").reason_code == reasons.BUSINESS_ROLE_DENIED
    assert decision(actor_type=PolicyActorType.PAYREGISTER_DEVICE, device_status="revoked", requested_scope="payregister:payment:create", requested_metric_group=None, business_role="cashier").reason_code == reasons.DEVICE_REVOKED
    assert decision(actor_type=PolicyActorType.RECOVERY_ACTOR, requested_action="read_metric").reason_code == reasons.RECOVERY_ONLY_ACTOR
    d = decision(metadata={"raw_k1": "secret", "signature": "secret"})
    assert "secret" not in d.human_reason
    assert "raw_k1" not in repr(d)
