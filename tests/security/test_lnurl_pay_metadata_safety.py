from __future__ import annotations

import pytest

from app.services.lnurl.pay_metadata import (
    LNURLPayMetadataBuilder,
    LNURLPayMetadataEntry,
    TEXT_LONG_DESC,
    TEXT_PLAIN,
    UnsafeMetadataContentError,
    metadata_result_from_json,
)


@pytest.mark.parametrize(
    "value",
    [
        "access_pass=bbp_secret",
        "session_token=abc",
        "seed phrase abandon abandon abandon",
        "private_key=secret",
        "xprv9s21ZrQH143K",
        "issuer_private_key=pem",
        "server_pepper=pepper",
        "k1=aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        "principal_hash hmac-sha256:abc",
    ],
)
def test_secret_like_values_are_rejected(value: str) -> None:
    with pytest.raises(UnsafeMetadataContentError):
        LNURLPayMetadataBuilder().build_custom_metadata(plain_text=value)


def test_wallet_principal_hash_and_email_not_generated_by_default() -> None:
    result = LNURLPayMetadataBuilder().build_subscription_metadata(plan_code="basic_pass", duration_label="1 month")

    assert "principal_hash" not in result.canonical_json
    assert "@" not in result.canonical_json
    assert "email" not in result.canonical_json.lower()


@pytest.mark.parametrize("claim", ["entitlement active", "payment settled", "access activated", "grants access"])
def test_metadata_cannot_declare_authorization_or_settlement(claim: str) -> None:
    with pytest.raises(UnsafeMetadataContentError):
        LNURLPayMetadataBuilder().build_custom_metadata(plain_text="Payment", long_description=claim)


def test_untrusted_nested_json_is_rejected() -> None:
    with pytest.raises(Exception):
        metadata_result_from_json('{"metadata":[["text/plain","Pay"]]}')
    with pytest.raises(Exception):
        metadata_result_from_json('[["text/plain",{"nested":"Pay"}]]')


def test_metadata_is_not_policy_input_or_authorization_source() -> None:
    result = LNURLPayMetadataBuilder().canonicalize(
        [
            LNURLPayMetadataEntry(TEXT_PLAIN, "Bitcoin Bastion Pro Pass — 1 month"),
            LNURLPayMetadataEntry(TEXT_LONG_DESC, "Advanced signals within Pro plan limits."),
        ]
    )

    assert result.metadata_hash.startswith("sha256:")
    assert not hasattr(result, "allowed_scopes")
    assert not hasattr(result, "entitlement_status")
    assert not hasattr(result, "policy_decision")
