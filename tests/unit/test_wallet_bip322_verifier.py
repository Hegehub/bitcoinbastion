from __future__ import annotations

import base64
import json
from dataclasses import dataclass, replace
from pathlib import Path
from datetime import UTC, datetime, timedelta

import pytest

from app.domain.wallet_auth.actions import WalletAuthAction
from app.domain.wallet_auth.networks import WalletNetwork
from app.domain.wallet_auth.proofs import WalletProofType, WalletScriptType, WalletVerificationStrength
from app.services.wallet_auth.auth_intent import build_wallet_auth_intent, hash_intent
from app.services.wallet_auth.verifiers.base import WalletProofVerificationReason, WalletProofVerificationRequest
from app.services.wallet_auth.verifiers.bip322 import BIP322Verifier, BIP322VerifierConfig, VerificationOutcome
from app.services.wallet_auth.verifiers.bip322_backend import ScriptVerificationOutcome, ScriptVerificationResult
from app.services.wallet_auth.verifiers.bip322_codec import (
    BIP322Variant,
    bip322_message_hash,
    decode_bitcoin_address,
    encode_witness_stack,
    parse_bip322_signature,
)
from app.services.wallet_auth.verifiers.bip322_transactions import build_bip322_virtual_transactions
from app.services.wallet_auth.proof_verifier import WalletProofVerifierRegistry, build_default_placeholder_registry

P2WPKH_MAINNET = "bc1qqqqsyqcyq5rqwzqfpg9scrgwpugpzysn4v0345"
P2TR_MAINNET = "bc1pqqqsyqcyq5rqwzqfpg9scrgwpugpzysnzs23v9ccrydpk8qarc0sg5tmnz"
P2WSH_MAINNET = "bc1qqqqsyqcyq5rqwzqfpg9scrgwpugpzysnzs23v9ccrydpk8qarc0szrtjt7"


@dataclass(frozen=True)
class AcceptingBackend:
    backend_id: str = "accepting_test_backend"
    backend_version: str = "test"

    def verify_simple(self, **kwargs):
        return ScriptVerificationResult(ScriptVerificationOutcome.VALID, "valid_bip322_proof")

    def verify_full(self, **kwargs):
        return ScriptVerificationResult(ScriptVerificationOutcome.INCONCLUSIVE, "script_backend_unavailable")


@dataclass(frozen=True)
class InvalidBackend:
    backend_id: str = "invalid_test_backend"
    backend_version: str = "test"

    def verify_simple(self, **kwargs):
        return ScriptVerificationResult(ScriptVerificationOutcome.INVALID, "invalid_signature")

    def verify_full(self, **kwargs):
        return ScriptVerificationResult(ScriptVerificationOutcome.INCONCLUSIVE, "script_backend_unavailable")


def _signature(prefix: str = "smp", witness: tuple[bytes, ...] = (b"sig", b"pubkey")) -> str:
    return f"{prefix}:{base64.b64encode(encode_witness_stack(witness)).decode()}"


def _request(*, address: str = P2WPKH_MAINNET, signature: str | None = None, network=WalletNetwork.BITCOIN_MAINNET, action=WalletAuthAction.LOGIN):
    now = datetime(2026, 7, 12, 12, tzinfo=UTC)
    intent = build_wallet_auth_intent(
        domain="auth.bitcoin-bastion.com",
        action=action.value,
        purpose=action.value,
        origin="https://auth.bitcoin-bastion.com",
        network=network.value,
        challenge_id="challenge-123",
        nonce="nonce-1234567890",
        device_key_fingerprint="device:fingerprint",
        policy_hash="sha256:" + "a" * 64,
        risk_level="low",
        wallet_proof_type=WalletProofType.BIP322.value,
        issued_at=now,
        expires_at=now + timedelta(minutes=5),
    )
    payload = intent.__dict__.copy()
    return WalletProofVerificationRequest(
        intent_payload=payload,
        intent_hash=hash_intent(payload),
        proof_type=WalletProofType.BIP322,
        signature=signature or _signature(),
        wallet_identifier=address,
        network=network,
        expected_origin="https://auth.bitcoin-bastion.com",
        expected_action=action,
        expected_challenge_id="challenge-123",
        expected_nonce_hash="sha256:7704af96a26b1b1144922d8a4a79fc7321ea66f70bfd9aa576572140d3e67a77",
        device_key_fingerprint="device:fingerprint",
        requested_verification_strength=WalletVerificationStrength.STANDARD,
        verification_context={},
        current_time=now + timedelta(minutes=1),
        script_type_hint=WalletScriptType.UNKNOWN,
    )


def test_bip322_tagged_message_hash_is_deterministic_for_official_messages():
    assert bip322_message_hash(b"").hex() == "c90c269c4f8fcbe6880f72a721ddfbf1914268a794cbb21cfafee13770ae19f1"
    assert bip322_message_hash("Hello World").hex() == "f0eb03b1a75ac6d9847f55c624a99169b5dccba2a31f5b23bea77ba270de0a7a"
    assert bip322_message_hash("Bastion Ω").hex() == bip322_message_hash("Bastion Ω").hex()


def test_vendored_bip322_fixtures_match_codec_outputs():
    basic = json.loads(Path("tests/fixtures/bip322/basic-test-vectors.json").read_text())
    vectors = {item["name"]: item for item in basic["vectors"]}
    assert vectors["empty-message"]["message_hash_hex"] == bip322_message_hash("").hex()
    assert vectors["hello-world"]["message_hash_hex"] == bip322_message_hash("Hello World").hex()
    generated = json.loads(Path("tests/fixtures/bip322/generated-test-vectors.json").read_text())
    decoded = decode_bitcoin_address(generated["address"], WalletNetwork.BITCOIN_MAINNET)
    txs = build_bip322_virtual_transactions(message_hash=bip322_message_hash("Hello World"), message_challenge=decoded.script_pubkey)
    assert generated["script_pubkey_hex"] == decoded.script_pubkey.hex()
    assert generated["to_spend_txid"] == txs.to_spend_txid
    assert generated["to_sign_txid"] == txs.to_sign_txid


def test_virtual_transactions_are_deterministic():
    decoded = decode_bitcoin_address(P2WPKH_MAINNET, WalletNetwork.BITCOIN_MAINNET)
    txs = build_bip322_virtual_transactions(message_hash=bip322_message_hash("Hello World"), message_challenge=decoded.script_pubkey)
    assert txs.to_spend == build_bip322_virtual_transactions(message_hash=bip322_message_hash("Hello World"), message_challenge=decoded.script_pubkey).to_spend
    assert len(txs.to_spend_txid) == 64
    assert len(txs.to_sign_txid) == 64


def test_strict_variant_parsing_and_prefixless_policy():
    parsed = parse_bip322_signature(_signature())
    assert parsed.variant == BIP322Variant.SIMPLE
    with pytest.raises(Exception, match="prefix_required"):
        parse_bip322_signature(base64.b64encode(b"abc").decode())
    assert parse_bip322_signature(base64.b64encode(b"abc").decode(), allow_prefixless_simple=True).prefixless is True
    with pytest.raises(Exception, match="unknown_variant"):
        parse_bip322_signature("bad:" + base64.b64encode(b"abc").decode())


def test_p2wpkh_simple_valid_with_trusted_backend():
    result = BIP322Verifier(backend=AcceptingBackend()).verify(_request())
    assert result.verified is True
    assert result.evidence["outcome"] == VerificationOutcome.VALID.value
    assert result.evidence["variant"] == BIP322Variant.SIMPLE.value
    assert result.verification_strength == WalletVerificationStrength.STANDARD
    assert "policy_engine_required" in result.policy_hints


def test_p2tr_simple_valid_with_trusted_backend():
    result = BIP322Verifier(backend=AcceptingBackend()).verify(_request(address=P2TR_MAINNET))
    assert result.verified is True
    assert result.script_type == WalletScriptType.P2TR


def test_default_backend_returns_inconclusive_not_valid_for_p2wsh():
    result = BIP322Verifier().verify(_request(address=P2WSH_MAINNET))
    assert result.verified is False
    assert result.evidence["outcome"] == VerificationOutcome.INCONCLUSIVE.value
    assert result.reason_code == WalletProofVerificationReason.SCRIPT_BACKEND_UNAVAILABLE


def test_wrong_network_and_malformed_base64_are_invalid():
    wrong_network = BIP322Verifier().verify(_request(network=WalletNetwork.BITCOIN_TESTNET))
    assert wrong_network.reason_code == WalletProofVerificationReason.WRONG_NETWORK
    malformed = BIP322Verifier().verify(_request(signature="smp:not base64!"))
    assert malformed.reason_code == WalletProofVerificationReason.INVALID_BASE64


def test_pof_rejected_for_auth_by_default_and_full_is_inconclusive():
    pof = BIP322Verifier().verify(_request(signature=_signature("pof")))
    assert pof.verified is False
    assert pof.reason_code == WalletProofVerificationReason.PROOF_OF_FUNDS_NOT_ALLOWED_FOR_AUTH
    assert pof.evidence["outcome"] == VerificationOutcome.INCONCLUSIVE.value
    full = BIP322Verifier().verify(_request(signature=_signature("ful")))
    assert full.verified is False
    assert full.evidence["outcome"] == VerificationOutcome.INCONCLUSIVE.value


def test_prefixless_rejected_by_default_and_limited_when_enabled():
    raw = base64.b64encode(encode_witness_stack((b"sig",))).decode()
    result = BIP322Verifier().verify(_request(signature=raw))
    assert result.reason_code == WalletProofVerificationReason.PREFIX_REQUIRED
    accepted = BIP322Verifier(backend=AcceptingBackend(), config=BIP322VerifierConfig(allow_prefixless_simple=True)).verify(_request(signature=raw))
    assert accepted.verified is True
    assert "prefixless_compatibility_mode" in accepted.limitations


def test_structured_intent_tampering_fails_registry_prevalidation():
    registry = WalletProofVerifierRegistry()
    registry.register(BIP322Verifier(backend=AcceptingBackend()))
    req = _request()
    payload = dict(req.intent_payload)
    payload["domain"] = "evil.example"
    tampered = replace(req, intent_payload=payload)
    result = registry.verify(tampered)
    assert result.verified is False
    assert result.reason_code == WalletProofVerificationReason.INTENT_HASH_MISMATCH


def test_default_registry_uses_bip322_verifier_not_legacy_fallback():
    registry = build_default_placeholder_registry()
    result = registry.verify(_request())
    assert result.verifier_id == "bip322"
    assert result.verified is False
    assert result.reason_code in {WalletProofVerificationReason.SCRIPT_BACKEND_UNAVAILABLE, WalletProofVerificationReason.MALFORMED_PROOF, WalletProofVerificationReason.NONCE_MISMATCH}


def test_oversized_inputs_rejected_before_backend_success():
    req = _request()
    huge_sig = "smp:" + base64.b64encode(b"x" * 131073).decode()
    result = BIP322Verifier(backend=AcceptingBackend()).verify(replace(req, signature=huge_sig))
    assert result.verified is False
    assert result.reason_code == WalletProofVerificationReason.MALFORMED_PROOF
