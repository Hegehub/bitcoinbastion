from app.domain.access.plans import PlanCode
from app.services.access.policy_context import AuthenticationAssuranceLevel
from app.services.lnurl.policy_hooks import LNURLPolicyHooks


def base(**overrides):
    data = dict(principal_hash="hmac:p", actor_hash="hmac:p", subscription_plan=PlanCode.PRO, effective_scopes={"lnurl:withdraw:create", "lnurl:withdraw:approve", "payouts:execute"}, session_hash="sha256:s", device_key_fingerprint="sha256:d", amount_msat=1000, maximum_allowed_msat=2000, business_role="admin")
    data.update(overrides)
    return data


def test_lnurl_withdraw_stages_require_auth_step_up_quorum_limits_and_invoice():
    hooks = LNURLPolicyHooks()
    assert hooks.authorize_withdraw_request_creation(**base(session_hash=None)).reason_code == "session_missing"
    assert hooks.authorize_withdraw_request_creation(**base()).decision == "step_up_required"
    assert hooks.authorize_withdraw_payment(**base(step_up_present=True, human_intent_verified=True, quorum_satisfied=False)).decision == "quorum_required"
    assert hooks.authorize_withdraw_request_creation(**base(amount_msat=3000, step_up_present=True, human_intent_verified=True)).reason_code == "amount_limit_exceeded"
    assert hooks.authorize_withdraw_invoice_acceptance(**base(invoice_valid=False)).reason_code == "invoice_invalid"
    assert hooks.authorize_withdraw_payment(**base(step_up_present=True, human_intent_verified=True, authentication_assurance=AuthenticationAssuranceLevel.HIGH_ASSURANCE)).allowed
