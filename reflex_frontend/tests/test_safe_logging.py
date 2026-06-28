from __future__ import annotations

from bastion_ui.security.safe_logging import (
    REDACTED,
    redact_payload,
    redact_sensitive_text,
    safe_error_message,
)
from bastion_ui.services.errors import BastionApiError

TWELVE_WORDS = "alpha bravo cactus delta eagle forest galaxy harbor island jungle kitten lemon"
TWENTY_FOUR_WORDS = (
    f"{TWELVE_WORDS} mango nectar orange planet quantum river silver "
    "tiger uncle velvet winter xenon"
)


def test_redacts_sensitive_wording_and_extended_keys() -> None:
    assert REDACTED in redact_sensitive_text("contains seed phrase here")
    assert REDACTED in redact_sensitive_text("contains private key here")
    assert redact_sensitive_text("xprv9s21ZrQH143Kexample") == REDACTED
    assert redact_sensitive_text("yprv9s21ZrQH143Kexample") == REDACTED
    assert redact_sensitive_text("zprv9s21ZrQH143Kexample") == REDACTED


def test_redacts_authorization_headers_and_webhook_secrets() -> None:
    payload = {
        "Authorization": "Bearer token-value",
        "webhook_secret": "hook-secret",
        "nested": {"api_key": "abc"},
        "safe": "public address text",
    }
    redacted = redact_payload(payload)
    assert redacted["Authorization"] == REDACTED
    assert redacted["webhook_secret"] == REDACTED
    assert redacted["nested"]["api_key"] == REDACTED
    assert redacted["safe"] == "public address text"


def test_redacts_mnemonic_like_text() -> None:
    assert redact_sensitive_text(TWELVE_WORDS) == REDACTED
    assert redact_sensitive_text(TWENTY_FOUR_WORDS) == REDACTED


def test_safe_error_message_uses_public_message_and_redacts() -> None:
    error = BastionApiError("internal private key", public_message="Unable to reach backend")
    assert safe_error_message(error) == "Unable to reach backend"
    assert safe_error_message(Exception("private key leaked")) == f"{REDACTED} leaked"
