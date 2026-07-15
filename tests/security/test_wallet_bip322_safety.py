from __future__ import annotations

import base64
from dataclasses import dataclass, replace
from datetime import UTC, datetime, timedelta

import pytest

from app.domain.wallet_auth.actions import WalletAuthAction
from app.domain.wallet_auth.networks import WalletNetwork
from app.domain.wallet_auth.proofs import WalletProofType, WalletVerificationStrength
from app.services.wallet_auth.auth_intent import build_wallet_auth_intent, hash_intent
from app.services.wallet_auth.verifiers.base import WalletProofVerificationError, WalletProofVerificationReason, WalletProofVerificationRequest
from app.services.wallet_auth.verifiers.bip322 import BIP322Verifier
from app.services.wallet_auth.verifiers.bip322_codec import encode_witness_stack

ADDRESS = "bc1qqqqsyqcyq5rqwzqfpg9scrgwpugpzysn4v0345"


@dataclass(frozen=True)
class ExplodingBackend:
    backend_id: str = "exploding"
    backend_version: str = "test"

    def verify_simple(self, **kwargs):
        raise RuntimeError("raw internal signature parser failure with secret-like data")

    def verify_full(self, **kwargs):
        raise RuntimeError("raw internal full parser failure")


def _sig(prefix="smp"):
    return f"{prefix}:{base64.b64encode(encode_witness_stack((b'signature-bytes', b'pubkey'))).decode()}"


def _request(**overrides):
    now = datetime(2026, 7, 12, 12, tzinfo=UTC)
    intent = build_wallet_auth_intent(
        domain="auth.bitcoin-bastion.com",
        action=WalletAuthAction.LOGIN.value,
        purpose=WalletAuthAction.LOGIN.value,
        origin="https://auth.bitcoin-bastion.com",
        network=WalletNetwork.BITCOIN_MAINNET.value,
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
    values = dict(
        intent_payload=payload,
        intent_hash=hash_intent(payload),
        proof_type=WalletProofType.BIP322,
        signature=_sig(),
        wallet_identifier=ADDRESS,
        network=WalletNetwork.BITCOIN_MAINNET,
        expected_origin="https://auth.bitcoin-bastion.com",
        expected_action=WalletAuthAction.LOGIN,
        expected_challenge_id="challenge-123",
        expected_nonce_hash="sha256:7704af96a26b1b1144922d8a4a79fc7321ea66f70bfd9aa576572140d3e67a77",
        device_key_fingerprint="device:fingerprint",
        requested_verification_strength=WalletVerificationStrength.STANDARD,
        verification_context={},
        current_time=now + timedelta(minutes=1),
    )
    values.update(overrides)
    return WalletProofVerificationRequest(**values)


def test_bip322_result_does_not_create_session_principal_or_authorization():
    result = BIP322Verifier().verify(_request())
    assert result.verified is False
    assert "no_session_issued" in result.limitations
    assert "policy_engine_required" in result.policy_hints
    assert "principal" not in result.evidence
    assert "session" not in result.evidence


def test_seed_private_key_and_xprv_inputs_are_rejected_safely():
    with pytest.raises(WalletProofVerificationError) as exc:
        _request(wallet_identifier="xprv9s21ZrQH143K forbidden private material")
    assert "xprv9s21" not in str(exc.value)
    with pytest.raises(WalletProofVerificationError):
        _request(verification_context={"seed": "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about"})


def test_logs_do_not_include_raw_signature_or_wallet_address(caplog):
    req = _request()
    with caplog.at_level("INFO"):
        BIP322Verifier().verify(req)
    text = caplog.text
    assert req.signature not in text
    assert ADDRESS not in text
    assert "<redacted" in text or "wallet_bip322_verification_result" in text


def test_mainnet_testnet_mismatch_and_prefixless_are_rejected():
    mismatch = BIP322Verifier().verify(_request(network=WalletNetwork.BITCOIN_TESTNET))
    assert mismatch.reason_code == WalletProofVerificationReason.WRONG_NETWORK
    prefixless = BIP322Verifier().verify(_request(signature=base64.b64encode(encode_witness_stack((b"sig",))).decode()))
    assert prefixless.reason_code == WalletProofVerificationReason.PREFIX_REQUIRED


def test_pof_unsupported_scripts_and_backend_exceptions_fail_closed():
    pof = BIP322Verifier().verify(_request(signature=_sig("pof")))
    assert pof.verified is False
    assert pof.verification_strength != WalletVerificationStrength.HIGH_ASSURANCE
    unsupported = BIP322Verifier().verify(_request(wallet_identifier="bc1pqqqsyqcyq5rqwzqfpg9scrgwpugpzysnzs23v9ccrydpk8qarc0sg5tmnz", signature=_sig()))
    assert unsupported.verified is False
    assert unsupported.evidence["outcome"] == "inconclusive"
    exploded = BIP322Verifier(backend=ExplodingBackend()).verify(_request())
    assert exploded.verified is False
    assert exploded.reason_code == WalletProofVerificationReason.INTERNAL_VERIFICATION_ERROR


def test_no_network_or_broadcast_dependency(monkeypatch):
    import socket

    def fail(*args, **kwargs):
        raise AssertionError("network use forbidden")

    monkeypatch.setattr(socket, "socket", fail)
    result = BIP322Verifier().verify(_request())
    assert result.verified is False


def test_legacy_message_and_tampered_intent_are_not_accepted():
    legacy = BIP322Verifier().verify(_request(signature="legacy-message-signature"))
    assert legacy.verified is False
    req = _request()
    payload = dict(req.intent_payload)
    payload["device_key_fingerprint"] = "other-device"
    tampered = replace(req, intent_payload=payload)
    # Direct verifier does not perform registry prevalidation; malformed witness still cannot produce success.
    result = BIP322Verifier().verify(tampered)
    assert result.verified is False
