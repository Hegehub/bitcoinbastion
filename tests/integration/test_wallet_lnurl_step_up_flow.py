from dataclasses import replace

from app.domain.access.plans import PlanCode
from app.services.access.policy_context import AuthenticationAssuranceLevel, PolicyActorType, PolicyAuthMethod
from app.services.lnurl.policy_hooks import InMemoryLNURLPolicyAuditSink, LNURLPolicyHooks
from app.services.wallet_auth.human_intent import WalletStepUpHumanIntent
from app.services.wallet_auth.step_up_policy import StepUpPolicyContext, StepUpProofState, WalletLNURLStepUpPolicy

POLICY_HASH = "sha256:wallet-step-up-policy-v1"


def test_wallet_lnurl_step_up_flow_create_api_key_and_replay_tampering():
    principal = "hmac:principal"
    device = "sha256:device"
    session = "sha256:session"
    policy = WalletLNURLStepUpPolicy()
    routine = StepUpPolicyContext(action="read_basic_metrics", actor_type=PolicyActorType.LIGHTNING_WALLET_PRINCIPAL, principal_hash=principal, device_key_fingerprint=device, session_hash=session, requested_scopes=frozenset({"signals:standard:read"}), effective_scopes=frozenset({"signals:standard:read", "api:keys:manage"}), policy_hash=POLICY_HASH)
    assert policy.evaluate_step_up_requirement(routine).allowed
    high = StepUpPolicyContext(action="create_api_key", actor_type=PolicyActorType.LIGHTNING_WALLET_PRINCIPAL, principal_hash=principal, device_key_fingerprint=device, session_hash=session, requested_scopes=frozenset({"api:keys:manage"}), effective_scopes=frozenset({"signals:standard:read", "api:keys:manage"}), policy_hash=POLICY_HASH)
    assert policy.evaluate_step_up_requirement(high).decision == "step_up_required"
    intent = WalletStepUpHumanIntent(action="create_api_key", purpose="Create scoped API key", actor_type="lightning_wallet_principal", principal_hash=principal, device_key_fingerprint=device, session_fingerprint=session, origin="https://app.example", domain="auth.example", requested_scopes=("api:keys:manage",), policy_hash=POLICY_HASH, challenge_id="sha256:challenge", nonce="sha256:nonce", lnurl_internal_action_description="LNURL action auth maps to Bastion create_api_key")
    audit = InMemoryLNURLPolicyAuditSink()
    hooks = LNURLPolicyHooks(audit_sink=audit)
    callback = hooks.authorize_auth_step_up(principal_hash=principal, actor_hash=principal, session_hash=session, device_key_fingerprint=device, k1_hash="sha256:k1", k1_status="used", signature_verified=True, domain_matches=True, challenge_domain="auth.example", callback_domain="auth.example", auth_domain="auth.example", challenge_action="lnurl_auth_step_up", requested_internal_action="create_api_key", subscription_plan=PlanCode.PRO, effective_scopes={"api:keys:manage"}, authentication_assurance=AuthenticationAssuranceLevel.HIGH_ASSURANCE, step_up_present=True, human_intent_verified=True, policy_hash=POLICY_HASH)
    assert callback.allowed
    proof = StepUpProofState(method=PolicyAuthMethod.LNURL_AUTH, freshness_seconds=100, intent_hash=intent.intent_hash, action="create_api_key", policy_hash=POLICY_HASH, verified=True, principal_hash=principal, k1_status="used")
    assert policy.evaluate_step_up_requirement(replace(high, intent_hash=intent.intent_hash, provided_proofs=(proof,))).allowed
    replay = StepUpProofState(method=PolicyAuthMethod.LNURL_AUTH, freshness_seconds=100, intent_hash=intent.intent_hash, action="create_api_key", policy_hash=POLICY_HASH, verified=True, principal_hash=principal, k1_status="reused")
    assert policy.evaluate_step_up_requirement(replace(high, intent_hash=intent.intent_hash, provided_proofs=(replay,))).decision == "step_up_required"
    tampered = WalletStepUpHumanIntent(action="create_api_key", purpose="Create scoped API key", actor_type="lightning_wallet_principal", principal_hash=principal, device_key_fingerprint=device, session_fingerprint=session, origin="https://app.example", domain="auth.example", requested_scopes=("api:keys:manage", "treasury:policy:read"), policy_hash=POLICY_HASH, challenge_id="sha256:challenge", nonce="sha256:nonce")
    assert tampered.intent_hash != intent.intent_hash
    assert audit.events
