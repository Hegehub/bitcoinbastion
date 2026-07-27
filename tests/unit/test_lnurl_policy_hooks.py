from app.domain.access.plans import PlanCode
from app.services.access.policy_context import AuthenticationAssuranceLevel, PolicyActorType
from app.services.lnurl.policy_hooks import InMemoryLNURLPolicyAuditSink, InMemoryLNURLPolicyMetricsSink, LNURLPolicyAction, LNURLPolicyHooks


def hooks(**kwargs):
    audit = kwargs.pop("audit_sink", InMemoryLNURLPolicyAuditSink())
    metrics = kwargs.pop("metrics_sink", InMemoryLNURLPolicyMetricsSink())
    return LNURLPolicyHooks(audit_sink=audit, metrics_sink=metrics, **kwargs), audit, metrics


def valid_auth_kwargs(**overrides):
    data = dict(
        principal_hash="hmac:principal",
        actor_hash="hmac:principal",
        k1_hash="sha256:k1",
        k1_status="used",
        signature_verified=True,
        challenge_domain="auth.example",
        callback_domain="auth.example",
        domain_matches=True,
        challenge_action="lnurl_auth_login",
        auth_domain="auth.example",
        subscription_plan=PlanCode.PRO,
        effective_scopes={"signals:standard:read", "api:keys:manage", "lnurl:withdraw:create", "lnurl:withdraw:approve", "payouts:execute"},
    )
    data.update(overrides)
    return data


def test_valid_lnurl_auth_plus_allowed_policy_can_proceed_and_audits_safely():
    hook, audit, metrics = hooks()
    decision = hook.authorize_auth_login(**valid_auth_kwargs())
    assert decision.allowed
    assert audit.events[-1]["event_type"] == "lnurl_auth_policy_evaluated"
    assert "k1_hash" not in metrics.events[-1].labels
    assert "raw_k1" not in repr(audit.events[-1])


def test_valid_signature_with_denied_policy_cannot_create_session_and_protocol_errors_map():
    hook, _, _ = hooks()
    assert hook.authorize_auth_login(**valid_auth_kwargs(k1_status="reused")).reason_code == "lnurl_k1_reused"
    assert hook.authorize_auth_login(**valid_auth_kwargs(k1_status="expired")).reason_code == "lnurl_k1_expired"
    assert hook.authorize_auth_login(**valid_auth_kwargs(domain_matches=False)).reason_code == "lnurl_domain_mismatch"
    assert hook.authorize_auth_login(**valid_auth_kwargs(signature_verified=False)).reason_code == "lnurl_signature_invalid"
    assert hook.authorize_auth_login(**valid_auth_kwargs(actor_status="revoked")).reason_code == "principal_revoked"


def test_unknown_internal_action_and_compatibility_critical_auth_fail_closed():
    hook, _, _ = hooks()
    assert hook.authorize_auth_login(**valid_auth_kwargs(challenge_action="lnurl_auth_login", requested_internal_action="opaque_authorize")).reason_code == "lnurl_action_mismatch"
    critical = hook.authorize_auth_step_up(**valid_auth_kwargs(authentication_assurance=AuthenticationAssuranceLevel.COMPATIBILITY, session_hash="sha256:s", device_key_fingerprint="sha256:d", challenge_action="lnurl_auth_step_up", requested_internal_action="create_api_key"))
    assert critical.reason_code == "wallet_proof_too_weak"


def test_missing_pop_session_denied_where_required_and_policy_engine_unavailable_fails_closed():
    hook, _, _ = hooks()
    denied = hook.authorize_auth_step_up(**valid_auth_kwargs(challenge_action="lnurl_auth_step_up", requested_internal_action="create_api_key"))
    assert denied.reason_code == "session_missing"

    def broken():
        raise RuntimeError("boom")

    hook2, _, _ = hooks(policy_engine_factory=broken)
    assert hook2.authorize_auth_login(**valid_auth_kwargs()).reason_code == "policy_engine_unavailable"


def test_lnurl_pay_entitlement_requires_settlement_verification_and_idempotency():
    hook, _, _ = hooks()
    base = dict(
        actor_type=PolicyActorType.LIGHTNING_WALLET_PRINCIPAL,
        principal_hash="hmac:principal",
        session_hash="sha256:s",
        device_key_fingerprint="sha256:d",
        subscription_plan=PlanCode.PRO,
        payment_request_hash="sha256:req",
        invoice_hash="sha256:invoice",
        amount_msat=1000,
        expected_amount_msat=1000,
        effective_scopes=set(),
    )
    assert hook.authorize_entitlement_issuance(**base, invoice_status="issued").reason_code == "payment_not_settled"
    assert hook.authorize_entitlement_issuance(**base, payment_status="settled", settlement_verified=False).reason_code == "settlement_not_verified"
    assert hook.authorize_entitlement_issuance(**base, payment_status="settled", settlement_verified=True, payment_proof_hash="sha256:proof").allowed
    assert hook.authorize_entitlement_issuance(**base, payment_status="settled", settlement_verified=True, payment_proof_hash="sha256:proof", previous_state="entitlement_issued").reason_code == "duplicate_entitlement"
    mismatch = {**base, "amount_msat": 999}
    assert hook.authorize_entitlement_issuance(**mismatch, payment_status="settled", settlement_verified=True, payment_proof_hash="sha256:proof").reason_code == "amount_mismatch"


def test_lightning_address_policy_and_not_authentication():
    hook, _, _ = hooks()
    assert hook.authorize_lightning_address_resolution(lightning_address_hash="hmac:addr", address_status="active", subscription_plan=PlanCode.LITE).allowed
    assert hook.authorize_lightning_address_resolution(lightning_address_hash="hmac:addr", address_status="disabled").reason_code == "address_disabled"
    assert hook.authorize_lightning_address_resolution(lightning_address_hash="hmac:addr", payregister_terminal_hash="hmac:terminal", revocation_state={"terminal_revoked": True}).reason_code == "terminal_revoked"


def test_withdraw_stages_enforce_amount_invoice_quorum_cooldown_and_duplicates():
    hook, _, _ = hooks()
    base = valid_auth_kwargs(session_hash="sha256:s", device_key_fingerprint="sha256:d", challenge_action="lnurl_auth_step_up", amount_msat=1000, maximum_allowed_msat=2000, business_role="admin")
    assert hook.authorize_withdraw_request_creation(**base).decision == "step_up_required"
    assert hook.authorize_withdraw_request_creation(**base, step_up_present=True, human_intent_verified=True).allowed
    too_much = {**base, "amount_msat": 3000}
    assert hook.authorize_withdraw_request_creation(**too_much, step_up_present=True, human_intent_verified=True).reason_code == "amount_limit_exceeded"
    assert hook.authorize_withdraw_invoice_acceptance(**base, invoice_valid=False).reason_code == "invoice_invalid"
    assert hook.authorize_withdraw_payment(**base, step_up_present=True, human_intent_verified=True, withdraw_status="paid", requested_state="payment_execution").reason_code == "withdraw_already_paid"
    assert hook.authorize_withdraw_payment(**base, step_up_present=True, human_intent_verified=True, quorum_satisfied=False).decision == "quorum_required"


def test_payerdata_comment_and_success_action_cannot_authorize():
    hook, _, _ = hooks()
    assert hook.authorize_payer_data_binding(**valid_auth_kwargs(session_hash="sha256:s", device_key_fingerprint="sha256:d", payer_data_present=True, payer_data_auth_verified=False)).reason_code == "payer_data_auth_invalid"
    assert hook.authorize_entitlement_issuance(**valid_auth_kwargs(session_hash="sha256:s", device_key_fingerprint="sha256:d", comment_present=True, payment_status="settled", settlement_verified=True, payment_proof_hash="sha256:proof")).reason_code == "payer_data_not_authorization"
    assert hook.authorize_entitlement_issuance(**valid_auth_kwargs(session_hash="sha256:s", device_key_fingerprint="sha256:d", success_action_type="url", payment_status="settled", settlement_verified=True, payment_proof_hash="sha256:proof")).reason_code == "success_action_type_not_allowed"


def test_action_contract_contains_required_values():
    assert {"lnurl_auth_register", "lnurl_pay_issue_entitlement", "lightning_address_resolve", "lnurl_withdraw_pay", "payregister_lnurl_refund", "lnurl_payerdata_bind_auth", "lnurl_success_action_create"} <= {a.value for a in LNURLPolicyAction}
