from __future__ import annotations

import importlib

import pytest

from app.services.wallet_auth.privacy_commitments import (
    PrivacyCommitmentContext,
    WalletPrivacyCommitmentError,
    assert_no_global_user_id,
    build_safe_success_action_reference,
    canonicalize_identifier,
    compute_address_lookup_hash,
    compute_hmac_lookup_hash,
    compute_lightning_address_hash,
    compute_lightning_principal_hash,
    compute_lnurl_callback_hash,
    compute_lnurl_invoice_hash,
    compute_lnurl_k1_hash,
    compute_lnurl_key_hash,
    compute_lnurl_payment_proof_hash,
    compute_lnurl_payment_request_hash,
    compute_payerdata_hash,
    compute_product_pseudonym,
    compute_script_pubkey_commitment,
    compute_sha256_commitment,
    compute_wallet_principal_hash,
    compute_wallet_proof_hash,
    filter_allowed_payerdata_fields,
    parse_lightning_address_parts,
    redact_bolt11_invoice,
    redact_lightning_address,
    redact_lnurl_identifier,
    redact_sensitive_auth_material,
    redact_wallet_identifier,
    reject_forbidden_wallet_secret_input,
    sanitize_lnurl_comment,
)

PEPPER = "server-pepper-for-tests"
ADDRESS = "bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh"
LNURL_KEY = "03abcdef0123456789abcdef0123456789abcdef0123456789abcdef0123456789"
BOLT11 = "lnbc2500u1p3examplepp5qqqsyqcyq5rqwzqfka"


def test_hmac_lookup_hash_is_deterministic_namespaced_and_rejects_empty() -> None:
    first = compute_hmac_lookup_hash(PEPPER, "wallet", ADDRESS)
    assert first == compute_hmac_lookup_hash(PEPPER, "wallet", ADDRESS)
    assert first != compute_hmac_lookup_hash(PEPPER, "wallet-other", ADDRESS)
    assert first.startswith("hmac-sha256:")
    with pytest.raises(ValueError):
        compute_hmac_lookup_hash("", "wallet", ADDRESS)
    with pytest.raises(ValueError):
        compute_hmac_lookup_hash(PEPPER, "wallet", "")


def test_sha_commitment_and_canonical_identifier() -> None:
    assert compute_sha256_commitment("value").startswith("sha256:")
    assert canonicalize_identifier("  MixedCaseValue  ") == "MixedCaseValue"
    with pytest.raises(ValueError):
        canonicalize_identifier("   ")


def test_bitcoin_wallet_commitments_do_not_expose_address_and_are_network_bound() -> None:
    mainnet = compute_wallet_principal_hash(PEPPER, ADDRESS, "bitcoin-mainnet")
    testnet = compute_wallet_principal_hash(PEPPER, ADDRESS, "bitcoin-testnet")
    product = compute_wallet_principal_hash(PEPPER, ADDRESS, "bitcoin-mainnet", "bastion_payregister")
    address_hash = compute_address_lookup_hash(PEPPER, ADDRESS, "bitcoin-mainnet")
    assert ADDRESS not in mainnet
    assert ADDRESS not in address_hash
    assert mainnet != testnet
    assert mainnet != product
    assert compute_script_pubkey_commitment("0014abcdef").startswith("sha256:")
    assert compute_wallet_proof_hash("signature-material", "bip322") != compute_wallet_proof_hash(
        "signature-material", "legacy_message_signature"
    )


def test_lnurl_commitments_are_domain_bound_and_do_not_expose_key_or_k1() -> None:
    principal = compute_lightning_principal_hash(PEPPER, LNURL_KEY, "auth.bitcoin-bastion.com")
    other_domain = compute_lightning_principal_hash(PEPPER, LNURL_KEY, "other.bitcoin-bastion.com")
    key_hash = compute_lnurl_key_hash(PEPPER, LNURL_KEY, "auth.bitcoin-bastion.com")
    k1_hash = compute_lnurl_k1_hash("a" * 64)
    callback_hash = compute_lnurl_callback_hash("https://auth.example/cb?k1=rawsecret&sig=rawsig")
    assert LNURL_KEY not in principal
    assert LNURL_KEY not in key_hash
    assert principal != other_domain
    assert "a" * 64 not in k1_hash
    assert callback_hash.startswith("sha256:")


def test_lightning_address_parse_and_hash_is_not_identity() -> None:
    assert parse_lightning_address_parts("lite@bitcoin-bastion.com") == ("lite", "bitcoin-bastion.com")
    with pytest.raises(ValueError):
        parse_lightning_address_parts("lite@@bitcoin-bastion.com")
    with pytest.raises(ValueError):
        parse_lightning_address_parts("@bitcoin-bastion.com")
    address_hash = compute_lightning_address_hash(PEPPER, "lite@bitcoin-bastion.com")
    assert "lite" not in address_hash
    assert "bitcoin-bastion.com" not in address_hash


def test_payment_commitments_do_not_expose_invoice_and_settlement_is_explicit() -> None:
    invoice_hash = compute_lnurl_invoice_hash(BOLT11)
    request_hash = compute_lnurl_payment_request_hash("payment-123", "pro")
    proof_unsettled = compute_lnurl_payment_proof_hash("payment-hash", invoice_hash)
    proof_settled = compute_lnurl_payment_proof_hash("payment-hash", invoice_hash, "2026-07-09T00:00:00Z")
    assert BOLT11 not in invoice_hash
    assert request_hash.startswith("sha256:")
    assert proof_unsettled != proof_settled


def test_payerdata_filtering_and_hashing_are_privacy_first() -> None:
    payerdata = {"auth": {"k1": "hash-only"}, "email": "user@example.com", "name": "Alice", "identifier": "id"}
    filtered = filter_allowed_payerdata_fields(payerdata)
    assert filtered == {"auth": {"k1": "hash-only"}}
    personal = filter_allowed_payerdata_fields(payerdata, allow_personal_fields=True)
    assert {"email", "name", "identifier", "auth"}.issubset(personal)
    assert compute_payerdata_hash(PEPPER, filtered) == compute_payerdata_hash(PEPPER, filtered)


def test_comment_allowed_sanitization_treats_comment_as_untrusted_metadata() -> None:
    assert sanitize_lnurl_comment("  hello\x00world\n  ", 20) == "helloworld"
    assert sanitize_lnurl_comment("abcdef", 3) == "abc"
    with pytest.raises(ValueError):
        sanitize_lnurl_comment("comment", -1)


def test_success_action_reference_is_opaque_and_deterministic() -> None:
    reference = build_safe_success_action_reference(PEPPER, "payment-id-raw", "activation")
    assert reference == build_safe_success_action_reference(PEPPER, "payment-id-raw", "activation")
    assert reference.startswith("act_")
    assert "payment-id-raw" not in reference
    assert "session" not in reference.lower()
    assert "access_pass" not in reference.lower()


def test_product_pseudonym_is_product_scoped_and_not_global_principal_hash() -> None:
    principal = compute_wallet_principal_hash(PEPPER, ADDRESS, "bitcoin-mainnet")
    api = compute_product_pseudonym(PEPPER, principal, "bitcoin_bastion_api")
    payregister = compute_product_pseudonym(PEPPER, principal, "bastion_payregister")
    assert api != payregister
    assert api != principal
    assert principal not in api


def test_redaction_helpers_preserve_type_context_without_full_value() -> None:
    assert ADDRESS not in redact_wallet_identifier(ADDRESS)
    assert "bc1" in redact_wallet_identifier(ADDRESS)
    assert "alice@example.com" not in redact_lightning_address("alice@example.com")
    assert "lnurl" in redact_lnurl_identifier("lnurl1dp68gurn8ghj7mrww4exct")
    assert BOLT11 not in redact_bolt11_invoice(BOLT11)
    assert "session-secret-token" not in redact_sensitive_auth_material("session-secret-token")
    assert "xprv" not in redact_sensitive_auth_material("xprv9s21ZrQH143Ksecret")


def test_forbidden_secret_input_and_global_user_id_errors_are_safe() -> None:
    secret = "xprv9s21ZrQH143Ksecret"
    with pytest.raises(WalletPrivacyCommitmentError) as exc:
        reject_forbidden_wallet_secret_input(secret, "wallet_material")
    assert secret not in str(exc.value)
    with pytest.raises(WalletPrivacyCommitmentError) as user_id_exc:
        assert_no_global_user_id("user_id", "abc123")
    assert "abc123" not in str(user_id_exc.value)


def test_privacy_context_repr_redacts_pepper_and_imports_safely() -> None:
    context = PrivacyCommitmentContext(server_pepper=PEPPER, product_context="bitcoin_bastion_api")
    assert PEPPER not in repr(context)
    assert "<redacted>" in repr(context)
    assert importlib.import_module("app.services.wallet_auth.privacy_commitments")
