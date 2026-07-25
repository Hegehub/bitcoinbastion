from app.domain.access.plans import PlanCode
from app.services.access.policy_context import AuthenticationAssuranceLevel
from app.services.lnurl.policy_hooks import InMemoryLNURLPolicyAuditSink, LNURLPolicyHooks


def auth_data(**overrides):
    data = dict(principal_hash="hmac:ln", actor_hash="hmac:ln", k1_hash="sha256:k1", k1_status="used", signature_verified=True, domain_matches=True, challenge_domain="auth.example", callback_domain="auth.example", auth_domain="auth.example", subscription_plan=PlanCode.PRO, effective_scopes={"api:keys:manage"})
    data.update(overrides)
    return data


def test_lnurl_auth_policy_flow_allows_then_requires_step_up_then_allows_then_revokes():
    audit = InMemoryLNURLPolicyAuditSink()
    hooks = LNURLPolicyHooks(audit_sink=audit)
    assert hooks.authorize_auth_login(**auth_data(challenge_action="lnurl_auth_login")).allowed
    step = hooks.authorize_auth_step_up(**auth_data(challenge_action="lnurl_auth_step_up", requested_internal_action="create_api_key", session_hash="sha256:s", device_key_fingerprint="sha256:d"))
    assert step.decision == "step_up_required"
    done = hooks.authorize_auth_step_up(**auth_data(challenge_action="lnurl_auth_step_up", requested_internal_action="create_api_key", session_hash="sha256:s", device_key_fingerprint="sha256:d", authentication_assurance=AuthenticationAssuranceLevel.HIGH_ASSURANCE, step_up_present=True, human_intent_verified=True))
    assert done.allowed
    assert hooks.authorize_auth_login(**auth_data(actor_status="revoked", challenge_action="lnurl_auth_login")).reason_code == "principal_revoked"
    assert [event["event_type"] for event in audit.events].count("lnurl_auth_policy_evaluated") == 4


def test_settled_verified_lnurl_pay_issues_one_entitlement_only():
    hooks = LNURLPolicyHooks()
    base = dict(principal_hash="hmac:ln", session_hash="sha256:s", device_key_fingerprint="sha256:d", subscription_plan=PlanCode.PRO, payment_request_hash="sha256:req", invoice_hash="sha256:invoice", amount_msat=1000, expected_amount_msat=1000, payment_status="settled", settlement_verified=True, payment_proof_hash="sha256:proof")
    assert hooks.authorize_entitlement_issuance(**base).allowed
    assert hooks.authorize_entitlement_issuance(**base, previous_state="entitlement_issued").reason_code == "duplicate_entitlement"
