from __future__ import annotations

import pytest

from app.services.wallet_auth.privacy_commitments import (
    WalletPrivacyCommitmentError,
    assert_no_global_user_id,
    compute_lightning_address_hash,
    compute_lightning_principal_hash,
    compute_product_pseudonym,
    compute_wallet_principal_hash,
    filter_allowed_payerdata_fields,
    reject_forbidden_wallet_secret_input,
    sanitize_lnurl_comment,
)

PEPPER = "server-pepper-for-security-tests"
ADDRESS = "bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh"
LNURL_KEY = "03abcdef0123456789abcdef0123456789abcdef0123456789abcdef0123456789"
LIGHTNING_ADDRESS = "merchant@bitcoin-bastion.com"


def test_no_wallet_principal_hash_returns_raw_wallet_address() -> None:
    result = compute_wallet_principal_hash(PEPPER, ADDRESS, "bitcoin-mainnet")
    assert ADDRESS not in result
    assert result.startswith("hmac-sha256:")


def test_no_lightning_principal_hash_returns_raw_lnurl_key() -> None:
    result = compute_lightning_principal_hash(PEPPER, LNURL_KEY, "auth.bitcoin-bastion.com")
    assert LNURL_KEY not in result
    assert result.startswith("hmac-sha256:")


def test_no_lightning_address_hash_returns_raw_address() -> None:
    result = compute_lightning_address_hash(PEPPER, LIGHTNING_ADDRESS)
    assert LIGHTNING_ADDRESS not in result
    assert "merchant" not in result
    assert "bitcoin-bastion.com" not in result


def test_seed_private_key_material_is_rejected_as_auth_material_without_leaking() -> None:
    raw_secret = "private_key xprv9s21ZrQH143Ksecret"
    with pytest.raises(WalletPrivacyCommitmentError) as exc:
        reject_forbidden_wallet_secret_input(raw_secret, "wallet_proof")
    assert raw_secret not in str(exc.value)


def test_comment_and_payerdata_are_not_authorization_inputs() -> None:
    filtered = filter_allowed_payerdata_fields({"auth": {"k1": "hash"}, "email": "user@example.com", "role": "admin"})
    assert filtered == {"auth": {"k1": "hash"}}
    assert "admin" not in filtered.values()
    comment = sanitize_lnurl_comment(" grant admin ", 32)
    assert comment == "grant admin"


def test_product_pseudonym_never_equals_global_principal_hash() -> None:
    principal_hash = compute_wallet_principal_hash(PEPPER, ADDRESS, "bitcoin-mainnet")
    pseudonym = compute_product_pseudonym(PEPPER, principal_hash, "bastion_payregister")
    assert pseudonym != principal_hash
    assert principal_hash not in pseudonym


def test_global_user_id_is_rejected_for_wallet_lnurl_identity() -> None:
    with pytest.raises(WalletPrivacyCommitmentError) as exc:
        assert_no_global_user_id("user_id", "raw-identity")
    assert "raw-identity" not in str(exc.value)
