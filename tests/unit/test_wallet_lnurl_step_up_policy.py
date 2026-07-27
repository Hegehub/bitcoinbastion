from dataclasses import replace

from app.domain.access.plans import PlanCode
from app.services.access.policy_context import PolicyActorType, PolicyAuthMethod
from app.services.wallet_auth.human_intent import WALLET_SIGNATURE_WARNING, WalletStepUpHumanIntent
from app.services.wallet_auth.step_up_policy import QuorumState, StepUpPolicyContext, StepUpProofState, WalletLNURLStepUpPolicy

POLICY_HASH = "sha256:wallet-step-up-policy-v1"
INTENT_HASH = "sha256:intent"


def ctx(**overrides):
    base = dict(
        action="read_basic_metrics",
        actor_type=PolicyActorType.LIGHTNING_WALLET_PRINCIPAL,
        principal_hash="hmac:p",
        device_key_fingerprint="sha256:d",
        session_hash="sha256:s",
        auth_method=PolicyAuthMethod.LNURL_AUTH,
        subscription_plan=PlanCode.PRO,
        requested_scopes=frozenset({"signals:standard:read"}),
        effective_scopes=frozenset({"signals:standard:read", "api:keys:manage", "treasury:policy:read"}),
        policy_hash=POLICY_HASH,
        intent_hash=INTENT_HASH,
    )
    base.update(overrides)
    return StepUpPolicyContext(**base)


def proof(method, **overrides):
    data = dict(method=method, freshness_seconds=100, intent_hash=INTENT_HASH, action="create_api_key", policy_hash=POLICY_HASH, verified=True, principal_hash="hmac:p")
    data.update(overrides)
    return StepUpProofState(**data)


def test_routine_read_requires_no_wallet_step_up_and_manifest_is_canonical_safe():
    decision = WalletLNURLStepUpPolicy().evaluate_step_up_requirement(ctx())
    assert decision.decision == "allow"
    assert decision.requirement == "none"
    intent = WalletStepUpHumanIntent(action="create_api_key", purpose="Create scoped key", actor_type="lightning_wallet_principal", principal_hash="hmac:p", device_key_fingerprint="sha256:d", session_fingerprint="sha256:s", origin="https://app.example", domain="auth.example", requested_scopes=("trace:standard:read", "market:intelligence:read"), cannot_access=("treasury", "payregister:admin"), challenge_id="sha256:challenge", nonce="sha256:nonce")
    payload = intent.with_hash()
    assert payload["requested_scopes"] == ("market:intelligence:read", "trace:standard:read")
    assert payload["warning"] == WALLET_SIGNATURE_WARNING
    assert "k1" not in payload and "signature" not in payload and "session_token" not in payload


def test_create_api_key_requires_fresh_lnurl_or_bip322_and_wrong_intent_action_policy_fail():
    policy = WalletLNURLStepUpPolicy()
    base = ctx(action="create_api_key", requested_scopes=frozenset({"api:keys:manage"}))
    assert policy.evaluate_step_up_requirement(base).reason_code == "fresh_lnurl_auth_required"
    assert policy.evaluate_step_up_requirement(replace(base, provided_proofs=(proof(PolicyAuthMethod.LNURL_AUTH),))).allowed
    assert policy.evaluate_step_up_requirement(replace(base, provided_proofs=(proof(PolicyAuthMethod.BIP322),))).allowed
    assert policy.evaluate_step_up_requirement(replace(base, provided_proofs=(proof(PolicyAuthMethod.LNURL_AUTH, intent_hash="sha256:other"),))).reason_code == "fresh_lnurl_auth_required"
    assert policy.evaluate_step_up_requirement(replace(base, provided_proofs=(proof(PolicyAuthMethod.LNURL_AUTH, action="add_device"),))).reason_code == "fresh_lnurl_auth_required"
    assert policy.evaluate_step_up_requirement(replace(base, provided_proofs=(proof(PolicyAuthMethod.LNURL_AUTH, policy_hash="sha256:other"),))).reason_code == "fresh_lnurl_auth_required"


def test_treasury_requires_bip322_and_lnurl_auth_is_not_treasury_proof():
    policy = WalletLNURLStepUpPolicy()
    base = ctx(action="treasury_policy_change", requested_object="treasury")
    assert policy.evaluate_step_up_requirement(replace(base, provided_proofs=(proof(PolicyAuthMethod.LNURL_AUTH, action="treasury_policy_change"),))).reason_code == "fresh_bip322_required"
    bip = proof(PolicyAuthMethod.BIP322, action="treasury_policy_change")
    assert policy.evaluate_step_up_requirement(replace(base, actor_type=PolicyActorType.BITCOIN_WALLET_PRINCIPAL, provided_proofs=(bip,))).allowed


def test_legacy_signature_cannot_approve_high_or_critical_actions_and_expired_proofs_rejected():
    policy = WalletLNURLStepUpPolicy()
    legacy = ctx(action="lockdown_release", auth_method=PolicyAuthMethod.LEGACY_BITCOIN_MESSAGE)
    assert policy.evaluate_step_up_requirement(legacy).reason_code == "stronger_wallet_proof_required"
    stale_ln = proof(PolicyAuthMethod.LNURL_AUTH, freshness_seconds=301)
    assert policy.evaluate_step_up_requirement(ctx(action="create_api_key", requested_scopes=frozenset({"api:keys:manage"}), provided_proofs=(stale_ln,))).reason_code == "fresh_lnurl_auth_required"
    stale_bip = proof(PolicyAuthMethod.BIP322, action="treasury_policy_change", freshness_seconds=301)
    assert policy.evaluate_step_up_requirement(ctx(action="treasury_policy_change", actor_type=PolicyActorType.BITCOIN_WALLET_PRINCIPAL, requested_object="treasury", provided_proofs=(stale_bip,))).reason_code == "fresh_bip322_required"


def test_revocation_entitlement_scope_plan_and_lockdown_controls():
    policy = WalletLNURLStepUpPolicy()
    assert policy.evaluate_step_up_requirement(ctx(action="create_api_key", revocation_state={"principal_revoked": True})).reason_code == "principal_revoked"
    assert policy.evaluate_step_up_requirement(ctx(action="create_api_key", revocation_state={"device_revoked": True})).reason_code == "device_revoked"
    assert policy.evaluate_step_up_requirement(ctx(action="create_api_key", revocation_state={"session_revoked": True})).reason_code == "session_revoked"
    assert policy.evaluate_step_up_requirement(ctx(action="create_api_key", revocation_state={"entitlement_expired": True})).reason_code == "entitlement_expired"
    assert policy.evaluate_step_up_requirement(ctx(action="create_api_key", requested_scopes=frozenset({"enterprise:policy:custom"}))).reason_code == "scope_not_allowed"
    assert policy.evaluate_step_up_requirement(ctx(action="create_api_key", recovery_state="recovery_locked")).reason_code == "recovery_locked"
    assert policy.evaluate_step_up_requirement(ctx(action="create_api_key", lockdown_state="active")).reason_code == "lockdown_active"


def test_dual_method_quorum_recovery_lockdown_and_high_value_withdraw():
    policy = WalletLNURLStepUpPolicy()
    dual_base = ctx(action="high-value_lnurl_withdraw", requested_amount_msat=15_000_000)
    assert policy.evaluate_step_up_requirement(dual_base).reason_code == "dual_method_required"
    p1 = proof(PolicyAuthMethod.LNURL_AUTH, action="high-value_lnurl_withdraw", proof_class="lnurl")
    p2 = proof(PolicyAuthMethod.BIP322, action="high-value_lnurl_withdraw", proof_class="bitcoin")
    assert policy.evaluate_step_up_requirement(replace(dual_base, provided_proofs=(p1, p2))).allowed
    dup_quorum = QuorumState(2, 3, ("hmac:a", "hmac:a"), INTENT_HASH, 100, ("owner", "admin"))
    assert policy.evaluate_step_up_requirement(ctx(action="business_owner_change", existing_quorum_state=dup_quorum)).decision == "quorum_required"
    quorum = QuorumState(2, 3, ("hmac:a", "hmac:b"), INTENT_HASH, 100, ("owner", "admin"))
    assert policy.evaluate_step_up_requirement(ctx(action="business_owner_change", existing_quorum_state=quorum)).allowed
    assert policy.evaluate_step_up_requirement(ctx(action="lockdown_release", actor_type=PolicyActorType.LIGHTNING_WALLET_PRINCIPAL)).reason_code == "fresh_bip322_required"
