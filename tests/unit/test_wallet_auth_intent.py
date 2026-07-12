from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from app.services.wallet_auth.auth_intent import (
    HIGH_RISK_APPROVAL_WARNING,
    LNURL_AUTH_WARNING,
    BastionAuthIntent,
    canonical_intent_json,
    hash_intent,
    render_wallet_message,
    render_lnurl_policy_context,
    build_wallet_auth_intent,
    build_human_intent,
    build_lnurl_policy_intent,
    validate_intent,
    is_expired,
    assert_not_expired,
    is_critical_action,
    requires_human_intent,
    redact_intent_for_logs,
)

NOW = datetime(2026, 7, 10, 12, 0, tzinfo=UTC)
EXP = NOW + timedelta(minutes=5)
POLICY_HASH = "sha256:" + "a" * 64
K1_HASH = "sha256:" + "b" * 64


def _wallet_intent(**overrides):
    data = dict(
        domain="auth.bitcoin-bastion.com",
        action="login",
        purpose="Authenticate to Bastion using wallet proof; not full authorization.",
        network="bitcoin-mainnet",
        challenge_id="chal_123",
        nonce="nonce_abc",
        device_key_fingerprint="dev_fp_123",
        policy_hash=POLICY_HASH,
        risk_level="medium",
        wallet_proof_type="bip322",
        issued_at=NOW,
        expires_at=EXP,
    )
    data.update(overrides)
    return build_wallet_auth_intent(**data)


def test_canonicalization_and_hash_are_stable_and_sensitive_to_changes():
    intent = _wallet_intent()
    left = canonical_intent_json({"b": 2, "a": 1})
    right = canonical_intent_json({"a": 1, "b": 2})
    assert left == right
    assert canonical_intent_json(intent.__dict__) == canonical_intent_json(intent.__dict__)
    assert hash_intent({"action": "login", "scopes": ["a"]}) == hash_intent({"scopes": ["a"], "action": "login"})
    assert hash_intent({"action": "login"}) != hash_intent({"action": "register"})
    assert hash_intent({"action": "login", "scopes": ["a"]}) != hash_intent({"action": "login", "scopes": ["b"]})


def test_wallet_message_rendering_is_structured_and_safe():
    message = render_wallet_message(_wallet_intent())
    assert "Bastion Wallet Proof Auth" in message
    assert "Domain: auth.bitcoin-bastion.com" in message
    assert "Action: login" in message
    assert "Nonce: nonce_abc" in message
    assert "Device key fingerprint: dev_fp_123" in message
    assert f"Policy hash: {POLICY_HASH}" in message
    assert "Expires at:" in message
    assert "This signature does not authorize a Bitcoin transaction." in message
    assert message.strip().lower() != "login"
    assert "xprv" not in message.lower()
    assert "mnemonic" not in message.lower()


def test_human_intent_renders_high_risk_fields():
    intent = build_human_intent(
        domain="auth.bitcoin-bastion.com",
        action="create_api_key",
        purpose="Approve scoped API key creation.",
        challenge_id="chal_critical",
        nonce="nonce_critical",
        device_key_fingerprint="dev_fp_123",
        policy_hash=POLICY_HASH,
        risk_level="high",
        requested_scopes=["quotes:read"],
        requested_metric_groups=["market"],
        cannot_access=["admin:all"],
        issued_at=NOW,
        expires_at=EXP,
        network="bitcoin-mainnet",
        object_reference_hash="sha256:" + "c" * 64,
        business_role="operator",
        payregister_context_hash="sha256:" + "d" * 64,
        recovery_context_hash="sha256:" + "e" * 64,
    )
    message = render_wallet_message(intent)
    assert "Requested scopes: quotes:read" in message
    assert "Requested metric groups: market" in message
    assert "Cannot access: admin:all" in message
    assert "Object reference hash:" in message
    assert "Business role: operator" in message
    assert "PayRegister context hash:" in message
    assert "Recovery context hash:" in message
    assert HIGH_RISK_APPROVAL_WARNING in message


def test_lnurl_policy_context_is_audit_safe_and_never_contains_raw_k1():
    intent = build_lnurl_policy_intent(
        domain="bitcoin-bastion.com",
        lnurl_auth_domain="auth.bitcoin-bastion.com",
        action="step_up",
        lnurl_action="auth",
        k1_hash=K1_HASH,
        purpose="Bind LNURL-auth k1 to step-up policy intent.",
        challenge_id="chal_lnurl",
        policy_hash=POLICY_HASH,
        risk_level="high",
        issued_at=NOW,
        expires_at=EXP,
        allowed_callback_host="auth.bitcoin-bastion.com",
        required_policy_decision="step_up_required",
        device_key_fingerprint="dev_fp_123",
    )
    context = render_lnurl_policy_context(intent)
    assert context["k1_hash"] == K1_HASH
    assert "raw-k1-value" not in str(context)
    assert context["lnurl_action"] == "auth"
    assert context["domain"] == "bitcoin-bastion.com"
    assert context["lnurl_auth_domain"] == "auth.bitcoin-bastion.com"
    assert LNURL_AUTH_WARNING in context["warnings"]
    assert "sig" not in context
    assert "key" not in context


def test_validation_rejects_missing_required_bindings_and_bad_time():
    assert not validate_intent(BastionAuthIntent(expires_at=EXP, issued_at=NOW)).valid
    assert "missing policy_hash" in validate_intent({**_wallet_intent().__dict__, "policy_hash": ""}).errors
    assert "missing nonce" in validate_intent({**_wallet_intent().__dict__, "nonce": ""}).errors
    assert "missing expires_at" in validate_intent({**_wallet_intent().__dict__, "expires_at": None}).errors
    assert "issued_at must be before expires_at" in validate_intent({**_wallet_intent().__dict__, "issued_at": EXP, "expires_at": NOW}).errors
    assert "unknown intent type" in validate_intent({**_wallet_intent().__dict__, "type": "unknown"}).errors
    assert "missing action" in validate_intent({**_wallet_intent().__dict__, "action": ""}).errors
    assert not validate_intent({**_wallet_intent().__dict__, "action": "create_api_key", "risk_level": "high"}).valid
    bad_lnurl = {
        "type": "bastion_lnurl_policy_intent",
        "version": 1,
        "domain": "example.com",
        "lnurl_auth_domain": "auth.example.com",
        "action": "login",
        "lnurl_action": "login",
        "k1_hash": "",
        "purpose": "test",
        "challenge_id": "chal",
        "policy_hash": POLICY_HASH,
        "risk_level": "medium",
        "issued_at": NOW,
        "expires_at": EXP,
        "allowed_callback_host": "auth.example.com",
        "required_policy_decision": "allow",
        "warnings": (LNURL_AUTH_WARNING,),
    }
    assert "missing k1_hash" in validate_intent(bad_lnurl).errors


def test_expiry_helpers_fail_closed():
    intent = _wallet_intent()
    assert not is_expired(intent, NOW)
    assert is_expired(intent, EXP)
    assert_not_expired(intent, NOW)
    with pytest.raises(ValueError, match="intent expired"):
        assert_not_expired(intent, EXP)


def test_critical_action_helpers():
    assert is_critical_action("create_api_key")
    assert is_critical_action("treasury_policy_change")
    assert is_critical_action("recovery_complete")
    assert is_critical_action("lockdown_release")
    assert requires_human_intent("create_api_key", "high")
    assert requires_human_intent("login", "critical")
    assert not requires_human_intent("login", "medium")
    assert not requires_human_intent("register", "medium")


def test_redaction_removes_accidental_sensitive_values_but_keeps_policy_context():
    intent = {
        **_wallet_intent().__dict__,
        "session_token": "sess_super_secret_token",
        "raw_k1": "0123456789abcdef" * 4,
        "access_pass": "access_pass_secret",
    }
    redacted = redact_intent_for_logs(intent)
    assert redacted["session_token"] == "<redacted>"
    assert redacted["raw_k1"] == "<redacted>"
    assert redacted["access_pass"] == "<redacted>"
    assert redacted["policy_hash"] == POLICY_HASH
    assert redacted["challenge_id"] == "chal_123"
    assert redacted["action"] == "login"
    assert redacted["risk_level"] == "medium"
    assert redacted["expires_at"] == "2026-07-10T12:05:00Z"


def test_import_safety():
    import app.services.wallet_auth.auth_intent as module

    assert module.WALLET_HUMAN_INTENT_TYPE == "bastion_wallet_human_intent"
