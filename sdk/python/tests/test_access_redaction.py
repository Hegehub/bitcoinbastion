from __future__ import annotations

import pytest

from bitcoin_bastion_sdk.access_auth import import_access_pass
from bitcoin_bastion_sdk.redaction import assert_no_unredacted_secret, redact_mapping, redact_secret


def test_raw_pass_is_redacted() -> None:
    material = import_access_pass("bap_raw_pass_secret")
    assert "bap_raw_pass_secret" not in repr(material)
    assert redact_secret("bap_raw_pass_secret") == "bap_…redacted"


def test_session_token_signature_and_authorization_are_redacted() -> None:
    payload = redact_mapping(
        {
            "Authorization": "Bearer secret",
            "X-Bastion-Session": "bap_session",
            "X-Bastion-Signature": "sig",
        }
    )
    assert payload == {
        "Authorization": "<redacted>",
        "X-Bastion-Session": "<redacted>",
        "X-Bastion-Signature": "<redacted>",
    }


def test_private_key_is_redacted() -> None:
    assert redact_mapping({"private_key": "not-allowed"})["private_key"] == "<redacted>"


def test_assert_no_unredacted_secret_detects_debug_leak() -> None:
    with pytest.raises(ValueError):
        assert_no_unredacted_secret("debug bap_raw_pass_secret")
