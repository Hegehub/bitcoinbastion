from dataclasses import replace

from app.domain.access.plans import PlanCode
from app.services.access.policy_context import AccessPolicyContext, PolicyActorType, PolicyAuthMethod
from app.services.access.policy_engine import AccessPolicyEngine
from app.services.wallet_auth.step_up_policy import StepUpPolicyContext, StepUpProofState, WalletLNURLStepUpPolicy

POLICY_HASH = "sha256:wallet-step-up-policy-v1"
INTENT_HASH = "sha256:intent"


def step_ctx(**overrides):
    base = dict(action="create_api_key", actor_type=PolicyActorType.LIGHTNING_WALLET_PRINCIPAL, principal_hash="hmac:p", device_key_fingerprint="sha256:d", session_hash="sha256:s", auth_method=PolicyAuthMethod.LNURL_AUTH, subscription_plan=PlanCode.PRO, requested_scopes=frozenset({"api:keys:manage"}), effective_scopes=frozenset({"api:keys:manage"}), policy_hash=POLICY_HASH, intent_hash=INTENT_HASH)
    base.update(overrides)
    return StepUpPolicyContext(**base)


def proof(**overrides):
    base = dict(method=PolicyAuthMethod.LNURL_AUTH, freshness_seconds=100, intent_hash=INTENT_HASH, action="create_api_key", policy_hash=POLICY_HASH, verified=True, principal_hash="hmac:p", k1_status="used")
    base.update(overrides)
    return StepUpProofState(**base)


def test_direct_endpoint_style_policy_dependency_cannot_bypass_central_engine():
    decision = AccessPolicyEngine().evaluate(AccessPolicyContext(actor_type=PolicyActorType.LIGHTNING_WALLET_PRINCIPAL, actor_hash="hmac:p", principal_hash="hmac:p", auth_methods=frozenset({PolicyAuthMethod.LNURL_AUTH, PolicyAuthMethod.SESSION_POP, PolicyAuthMethod.DEVICE_POP}), plan_code=PlanCode.PRO, effective_scopes={"api:keys:manage"}, requested_scope="api:keys:manage", requested_action="create_api_key", session_id_hash="sha256:s", device_id="sha256:d", policy_hash=POLICY_HASH, metadata={"intent_hash": INTENT_HASH}))
    assert decision.decision == "step_up_required"


def test_forged_hardware_claim_reused_k1_and_stale_intent_do_not_satisfy():
    policy = WalletLNURLStepUpPolicy()
    forged_hw = proof(method=PolicyAuthMethod.HARDWARE_WALLET, hardware_evidence_verified=False)
    assert policy.evaluate_step_up_requirement(step_ctx(action="treasury_policy_change", actor_type=PolicyActorType.BITCOIN_WALLET_PRINCIPAL, requested_object="treasury", provided_proofs=(forged_hw,))).reason_code == "fresh_bip322_required"
    assert policy.evaluate_step_up_requirement(step_ctx(provided_proofs=(proof(k1_status="reused"),))).reason_code == "fresh_lnurl_auth_required"
    assert policy.evaluate_step_up_requirement(step_ctx(provided_proofs=(proof(freshness_seconds=999),))).reason_code == "fresh_lnurl_auth_required"


def test_tampering_with_scopes_expiry_amount_or_policy_invalidates_approval():
    policy = WalletLNURLStepUpPolicy()
    valid = step_ctx(provided_proofs=(proof(),))
    assert policy.evaluate_step_up_requirement(valid).allowed
    assert policy.evaluate_step_up_requirement(replace(valid, requested_scopes=frozenset({"api:keys:manage", "treasury:policy:read"}))).reason_code == "scope_not_allowed"
    assert policy.evaluate_step_up_requirement(replace(valid, requested_expiry="9999-01-01", provided_proofs=(proof(policy_hash="sha256:other"),))).reason_code == "fresh_lnurl_auth_required"
    payout = step_ctx(action="high-value_lnurl_withdraw", requested_amount_msat=20_000_000, provided_proofs=(proof(action="high-value_lnurl_withdraw", proof_class="lnurl"),))
    assert policy.evaluate_step_up_requirement(payout).reason_code == "dual_method_required"


def test_raw_withdraw_k1_legacy_bearer_or_access_pass_alone_cannot_authorize_payout():
    policy = WalletLNURLStepUpPolicy()
    assert policy.evaluate_step_up_requirement(step_ctx(action="high-value_lnurl_withdraw", requested_amount_msat=20_000_000, provided_proofs=())).reason_code == "dual_method_required"
    assert policy.evaluate_step_up_requirement(step_ctx(action="lockdown_release", auth_method=PolicyAuthMethod.LEGACY_BITCOIN_MESSAGE)).reason_code == "stronger_wallet_proof_required"
    decision = AccessPolicyEngine().evaluate(AccessPolicyContext(actor_type=PolicyActorType.ACCESS_CERTIFICATE, certificate_fingerprint="sha256:cert", pass_lookup_hash="hmac:pass", plan_code=PlanCode.PRO, requested_action="create_api_key", requested_scope="api:keys:manage", effective_scopes={"api:keys:manage"}, session_id_hash="sha256:s", device_id="sha256:d", policy_hash=POLICY_HASH, metadata={"intent_hash": INTENT_HASH}))
    assert decision.decision == "step_up_required"
