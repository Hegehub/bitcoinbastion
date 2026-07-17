from __future__ import annotations

from pathlib import Path

import pytest

from app.services.lnurl.audit import LNURLAuditService, sanitize_lnurl_audit_metadata


@pytest.mark.parametrize(
    "key",
    [
        "k1",
        "raw_k1",
        "nonce",
        "raw_nonce",
        "sig",
        "signature",
        "raw_signature",
        "linking_key",
        "raw_key",
        "private_key",
        "seed",
        "mnemonic",
        "xprv",
        "session_token",
        "access_pass",
        "bearer_token",
        "preimage",
        "invoice_preimage",
        "recovery_phrase",
        "recovery_secret",
    ],
)
def test_raw_secret_fields_rejected(key: str) -> None:
    with pytest.raises(ValueError):
        sanitize_lnurl_audit_metadata({key: "secret-material"})


def test_nested_raw_secret_fields_rejected() -> None:
    with pytest.raises(ValueError):
        sanitize_lnurl_audit_metadata({"nested": {"raw_signature": "3045..."}})


def test_safe_hashes_and_fingerprints_accepted() -> None:
    sanitized = sanitize_lnurl_audit_metadata(
        {
            "k1_hash": "hmac-sha256:abc",
            "linking_key_hash": "hmac-sha256:def",
            "session_hash": "hmac-sha256:session",
            "device_key_fingerprint": "sha256:device",
        }
    )

    assert sanitized["k1_hash"] == "hmac-sha256:abc"


def test_audit_event_payload_does_not_store_raw_material() -> None:
    audit = LNURLAuditService()
    with pytest.raises(ValueError):
        audit.record_lnurl_auth_event(
            event_type="lnurl_auth_callback_failed",
            outcome="failure",
            challenge_hash="sha256:challenge",
            auth_domain_hash="sha256:domain",
            metadata={"signature": "3045022100"},
        )


def test_lnurl_audit_builder_source_uses_denylist_not_payload_raw_fields() -> None:
    source = Path("app/services/lnurl/audit.py").read_text()
    forbidden_payload_patterns = [
        '"raw_k1":',
        '"raw_signature":',
        '"session_token":',
        '"private_key":',
        '"mnemonic":',
        '"recovery_phrase":',
        '"access_pass":',
    ]

    for pattern in forbidden_payload_patterns:
        assert pattern not in source
