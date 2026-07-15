from __future__ import annotations

from bastion_ui.access_redaction import (
    BITCOIN_SEED_WARNING,
    looks_like_forbidden_wallet_material,
    redact_access_pass,
    redact_recovery_phrase,
    redact_sensitive_object,
    redact_session_token,
    redact_signature,
)
from bastion_ui.access_storage import (
    PRIVATE_KEY_LOCAL_STORAGE_ALLOWED,
    RAW_ACCESS_PASS_LOCAL_STORAGE_ALLOWED,
    RECOVERY_PHRASE_LOCAL_STORAGE_ALLOWED,
    dev_signer_allowed,
)


def test_access_redaction_masks_sensitive_values() -> None:
    raw_pass = "bbp_live_abcdef1234567890"
    session = "sess_live_abcdef1234567890"
    signature = "sig_live_abcdef1234567890"
    assert raw_pass not in redact_access_pass(raw_pass)
    assert session not in redact_session_token(session)
    assert signature not in redact_signature(signature)
    assert "correct horse battery staple" not in redact_recovery_phrase(
        "correct horse battery staple"
    )


def test_nested_redaction_masks_access_payloads() -> None:
    payload = {
        "bastion_access_pass": "bbp_live_secret123456",
        "headers": {"X-Bastion-Session": "sess_live_secret123456"},
        "items": [{"signature": "sig_live_secret123456"}],
    }
    redacted = redact_sensitive_object(payload)
    text = repr(redacted)
    assert "bbp_live_secret123456" not in text
    assert "sess_live_secret123456" not in text
    assert "sig_live_secret123456" not in text


def test_forbidden_wallet_material_is_rejected_client_side() -> None:
    assert looks_like_forbidden_wallet_material(
        "abandon ability able about above absent absorb abstract absurd abuse access accident"
    )
    assert looks_like_forbidden_wallet_material("xprv9s21ZrQH143K3example")
    assert "Bitcoin wallet seed" in BITCOIN_SEED_WARNING


def test_browser_storage_policy_rejects_persistent_secrets() -> None:
    assert RAW_ACCESS_PASS_LOCAL_STORAGE_ALLOWED is False
    assert RECOVERY_PHRASE_LOCAL_STORAGE_ALLOWED is False
    assert PRIVATE_KEY_LOCAL_STORAGE_ALLOWED is False
    assert dev_signer_allowed("production", enabled=True) is False
    assert dev_signer_allowed("development", enabled=True) is True
