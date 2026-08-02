from app.services.lnurl.policy_hooks import InMemoryLNURLPolicyAuditSink, LNURLPolicyHooks


def test_payerdata_comment_success_action_are_not_authorization_and_are_audit_safe():
    audit = InMemoryLNURLPolicyAuditSink()
    hooks = LNURLPolicyHooks(audit_sink=audit)
    assert hooks.authorize_payer_data_binding(principal_hash="hmac:p", session_hash="sha256:s", device_key_fingerprint="sha256:d", payer_data_present=True, payer_data_auth_verified=False).reason_code == "payer_data_auth_invalid"
    assert hooks.authorize_entitlement_issuance(principal_hash="hmac:p", session_hash="sha256:s", device_key_fingerprint="sha256:d", comment_present=True, payment_status="settled", settlement_verified=True, payment_proof_hash="sha256:proof").reason_code == "payer_data_not_authorization"
    assert hooks.authorize_entitlement_issuance(principal_hash="hmac:p", session_hash="sha256:s", device_key_fingerprint="sha256:d", success_action_type="url", payment_status="settled", settlement_verified=True, payment_proof_hash="sha256:proof").reason_code == "success_action_type_not_allowed"
    assert "raw_k1" not in repr(audit.events)
    assert "payer@example.com" not in repr(audit.events)
