from datetime import UTC, datetime, timedelta

from dataclasses import replace

from app.domain.access.plans import PlanCode
from app.services.access.policy_context import AccessPolicyContext, AuthenticationAssuranceLevel, PolicyActorType, PolicyAuthMethod
from app.services.access.policy_engine import AccessPolicyEngine


def test_lightning_principal_policy_flow_with_step_up_and_revocation():
    engine = AccessPolicyEngine()
    ctx = AccessPolicyContext(
        actor_type=PolicyActorType.LIGHTNING_WALLET_PRINCIPAL,
        actor_hash="hmac:ln-principal",
        principal_hash="hmac:principal",
        auth_methods=frozenset({PolicyAuthMethod.LNURL_AUTH, PolicyAuthMethod.DEVICE_POP, PolicyAuthMethod.SESSION_POP}),
        authentication_assurance=AuthenticationAssuranceLevel.STANDARD,
        lnurl_k1_status="used",
        lnurl_auth_action="login",
        lnurl_auth_domain="auth.example",
        auth_domain="auth.example",
        device_id="sha256:device",
        session_id_hash="sha256:session",
        session_expires_at=datetime.now(UTC) + timedelta(minutes=10),
        plan_code=PlanCode.PRO,
        entitlement_status="active",
        effective_scopes={"signals:standard:read", "api:keys:manage"},
        metric_entitlements={"groups": ["signals.standard"]},
        quota_state={"remaining": 5},
        requested_scope="signals:standard:read",
        requested_metric_group="signals.standard",
        requested_action="read_metric",
        policy_hash="sha256:test-policy",
    )
    allowed = engine.evaluate(ctx)
    assert allowed.allowed
    high = engine.evaluate(replace(ctx, requested_action="create_api_key", requested_scope="api:keys:manage", requested_metric_group=None))
    assert high.decision == "step_up_required"
    stepped = engine.evaluate(replace(ctx, requested_action="create_api_key", requested_scope="api:keys:manage", requested_metric_group=None, authentication_assurance=AuthenticationAssuranceLevel.HIGH_ASSURANCE, step_up_present=True, human_intent_verified=True))
    assert stepped.allowed
    revoked = engine.evaluate(replace(ctx, actor_status="revoked"))
    assert revoked.decision == "revoked"
    assert allowed.audit_required and high.audit_required and revoked.audit_required
