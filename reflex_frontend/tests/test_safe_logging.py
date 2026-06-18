from __future__ import annotations

from bastion_ui.security.safe_logging import (
    REDACTED,
    redact_payload,
    redact_sensitive_text,
    safe_error_message,
)

TWELVE_WORDS = "alpha bravo cactus delta ember forest galaxy harbor island jungle kernel lemon"
TWENTY_FOUR_WORDS = (
    "alpha bravo cactus delta ember forest galaxy harbor island jungle kernel lemon "
    "marble nectar orbit pencil quantum river silver tunnel uncle velvet winter yellow"
)


def test_safe_logging_redacts_sensitive_text() -> None:
    assert redact_sensitive_text("seed phrase: do not log") == REDACTED
    assert redact_sensitive_text("private key: do not log") == REDACTED
    assert redact_sensitive_text("xprv123456789ABCDEFGH") == REDACTED
    assert redact_sensitive_text("yprv123456789ABCDEFGH") == REDACTED
    assert redact_sensitive_text("zprv123456789ABCDEFGH") == REDACTED
    assert redact_sensitive_text("wallet.dat") == REDACTED
    assert redact_sensitive_text("keystore payload") == REDACTED


def test_safe_logging_redacts_auth_and_webhook_payloads() -> None:
    payload = {
        "headers": {"Authorization": "Bearer abc.def.ghi"},
        "webhook_secret": "super-secret",
        "safe": "public-address-only",
    }
    assert redact_payload(payload) == {
        "headers": {"Authorization": REDACTED},
        "webhook_secret": REDACTED,
        "safe": "public-address-only",
    }


def test_safe_logging_redacts_mnemonic_like_text() -> None:
    assert redact_sensitive_text(TWELVE_WORDS) == REDACTED
    assert redact_sensitive_text(TWENTY_FOUR_WORDS) == REDACTED


def test_safe_error_message_is_redacted() -> None:
    assert safe_error_message(RuntimeError("api key leaked")) == REDACTED
