from __future__ import annotations

import logging

import pytest

from app.services.access.audit_chain import sanitize_audit_metadata
from app.services.access.crypto.hashing import safe_hash_for_log
from app.services.access.key_redaction import redact_child_key, redact_delegated_pass
from app.services.access.recovery_seed import (
    RecoveryPhraseStrength,
    generate_recovery_phrase,
    recovery_phrase_commitment,
)


def test_raw_recovery_phrase_not_logged(caplog: pytest.LogCaptureFixture) -> None:
    phrase = " ".join(generate_recovery_phrase(RecoveryPhraseStrength.WORDS_12).words)
    with caplog.at_level(logging.INFO):
        commitment = recovery_phrase_commitment(phrase, "pepper")
        logging.getLogger("access.recovery.test").info("stored recovery commitment %s", commitment)
    assert phrase not in caplog.text
    assert "bastion_recovery_phrase" not in caplog.text


def test_log_fingerprints_do_not_expose_raw_access_or_session_material() -> None:
    raw_pass = "bbp_live_secret_not_real"
    raw_session = "sess_live_secret_not_real"

    pass_fingerprint = safe_hash_for_log(raw_pass)
    session_fingerprint = safe_hash_for_log(raw_session)

    assert raw_pass not in pass_fingerprint
    assert raw_session not in session_fingerprint
    assert pass_fingerprint.startswith("sha256:")
    assert session_fingerprint.startswith("sha256:")


def test_audit_metadata_rejects_raw_secret_fields() -> None:
    for key in (
        "raw_access_pass",
        "session_token",
        "recovery_phrase",
        "private_key",
        "bitcoin_seed",
        "issuer_private_key",
    ):
        with pytest.raises(ValueError):
            sanitize_audit_metadata({key: "secret"})


def test_child_and_delegated_secret_redaction_helpers_mask_raw_values() -> None:
    child = "bbk_live_childid_secretsecret"
    delegated = "bbd_live_delegatedid_secretsecret"

    assert child not in redact_child_key(child)
    assert delegated not in redact_delegated_pass(delegated)
