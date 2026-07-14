from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime, timedelta

import pytest

from app.domain.wallet_auth.actions import WalletAuthAction
from app.domain.wallet_auth.networks import WalletNetwork
from app.domain.wallet_auth.proofs import WalletProofType, WalletScriptType, WalletVerificationStrength
from app.services.access.crypto.hashing import sha256_prefixed
from app.services.wallet_auth.auth_intent import build_wallet_auth_intent, hash_intent
from app.services.wallet_auth.proof_verifier import (
    BIP322VerifierStub,
    LegacyMessageVerifierStub,
    WalletProofVerifierRegistry,
    WalletProofVerifierRegistryError,
    build_default_placeholder_registry,
)
from app.services.wallet_auth.verifiers.base import (
    WalletProofRevocationUnavailable,
    WalletProofVerificationError,
    WalletProofVerificationReason,
    WalletProofVerificationRequest,
    WalletProofVerificationResult,
    wallet_identifier_hash_for_request,
)

NOW = datetime(2026, 7, 12, 15, 0, tzinfo=UTC)
EXP = NOW + timedelta(minutes=5)
NONCE = "abc123nonce"
NONCE_HASH = sha256_prefixed(NONCE)
POLICY_HASH = "sha256:" + "a" * 64
ADDRESS = "bc1qw508d6qejxtdg4y5r3zarvary0c5xw7kygt080"


def intent(**overrides):
    data = dict(
        domain="auth.bitcoin-bastion.com",
        origin="https://auth.bitcoin-bastion.com",
        action="login",
        purpose="login",
        network="bitcoin-mainnet",
        challenge_id="wch_test",
        nonce=NONCE,
        device_key_fingerprint="dev_fp_verify",
        policy_hash=POLICY_HASH,
        risk_level="medium",
        wallet_proof_type="bip322",
        requested_scopes=[],
        issued_at=NOW,
        expires_at=EXP,
    )
    data.update(overrides)
    return build_wallet_auth_intent(**data).__dict__


def request(**overrides) -> WalletProofVerificationRequest:
    payload = overrides.pop("intent_payload", intent())
    data = dict(
        intent_payload=payload,
        intent_hash=hash_intent(payload),
        proof_type=WalletProofType.BIP322,
        signature="sensitive_signature_material",
        wallet_identifier=ADDRESS,
        network=WalletNetwork.BITCOIN_MAINNET,
        expected_origin="https://auth.bitcoin-bastion.com",
        expected_action=WalletAuthAction.LOGIN,
        expected_challenge_id="wch_test",
        expected_nonce_hash=NONCE_HASH,
        device_key_fingerprint="dev_fp_verify",
        requested_verification_strength=WalletVerificationStrength.STANDARD,
        verification_context={"risk_level": "medium"},
        current_time=NOW,
        script_type_hint=WalletScriptType.P2WPKH,
    )
    data.update(overrides)
    return WalletProofVerificationRequest(**data)


class SuccessVerifier:
    proof_type = WalletProofType.BIP322
    verifier_id = "success_bip322"
    verifier_version = "1"
    supported_networks = (WalletNetwork.BITCOIN_MAINNET,)
    supported_script_types = (WalletScriptType.P2WPKH, WalletScriptType.UNKNOWN)
    maximum_verification_strength = WalletVerificationStrength.STANDARD

    def verify(self, req: WalletProofVerificationRequest) -> WalletProofVerificationResult:
        return WalletProofVerificationResult(
            verified=True,
            proof_type=req.proof_type,
            verifier_id=self.verifier_id,
            verifier_version=self.verifier_version,
            verification_strength=WalletVerificationStrength.STANDARD,
            wallet_network=req.network,
            script_type=req.script_type_hint,
            wallet_identifier_hash=wallet_identifier_hash_for_request(req),
            proof_fingerprint="sha256:" + "b" * 64,
            intent_hash=req.intent_hash,
            verified_at=req.current_time,
            reason_code=WalletProofVerificationReason.VERIFIED,
            limitations=("wallet proof is not API authorization",),
            policy_hints=("policy_engine_required", "no_session_issued", "subscription_entitlement_required"),
            evidence={"address_hash": wallet_identifier_hash_for_request(req)},
        )


class RevokedChecker:
    def __init__(self, fail: bool = False) -> None:
        self.fail = fail
        self.calls = 0

    def is_revoked(self, *, target_type: str, target_hash: str, high_risk: bool = False) -> bool:
        self.calls += 1
        if self.fail:
            raise WalletProofRevocationUnavailable("offline")
        return target_type == "wallet_proof"


def test_registry_register_get_duplicate_and_no_fallback():
    registry = WalletProofVerifierRegistry()
    verifier = SuccessVerifier()
    registry.register(verifier)
    assert registry.get(WalletProofType.BIP322) is verifier
    with pytest.raises(WalletProofVerifierRegistryError):
        registry.register(BIP322VerifierStub())
    result = registry.verify(request(proof_type=WalletProofType.LEGACY_MESSAGE_SIGNATURE))
    assert not result.verified
    assert result.reason_code == WalletProofVerificationReason.UNSUPPORTED_PROOF_TYPE


def test_bip322_request_is_not_silently_sent_to_legacy_verifier():
    registry = WalletProofVerifierRegistry()
    registry.register(LegacyMessageVerifierStub())
    result = registry.verify(request(proof_type=WalletProofType.BIP322))
    assert not result.verified
    assert result.verifier_id == "registry"
    assert result.reason_code == WalletProofVerificationReason.UNSUPPORTED_PROOF_TYPE


def test_request_safe_repr_and_secret_rejection():
    req = request()
    assert "sensitive_signature_material" not in repr(req)
    assert ADDRESS not in repr(req)
    assert req.safe_summary()["signature"] == "<redacted>"
    assert "password" not in WalletProofVerificationRequest.__dataclass_fields__
    assert "private_key" not in WalletProofVerificationRequest.__dataclass_fields__
    assert "seed" not in WalletProofVerificationRequest.__dataclass_fields__
    with pytest.raises(WalletProofVerificationError) as excinfo:
        request(wallet_identifier="xprv-secret-wallet")
    assert "xprv-secret-wallet" not in str(excinfo.value)
    with pytest.raises(WalletProofVerificationError):
        request(verification_context={"seed": "nope"})


def test_result_metadata_and_invariants():
    req = request()
    registry = WalletProofVerifierRegistry()
    registry.register(SuccessVerifier())
    result = registry.verify(req)
    assert result.verified
    assert result.reason_code == WalletProofVerificationReason.VERIFIED
    assert result.wallet_identifier_hash.startswith("hmac-sha256:")
    assert ADDRESS not in str(result.safe_summary())
    assert "policy_engine_required" in result.policy_hints
    assert "no_session_issued" in result.policy_hints
    assert "subscription_entitlement_required" in result.policy_hints
    assert result.verification_strength == WalletVerificationStrength.STANDARD


def test_intent_prevalidation_failures():
    registry = WalletProofVerifierRegistry()
    registry.register(SuccessVerifier())
    assert registry.verify(request(intent_payload={})).reason_code == WalletProofVerificationReason.MALFORMED_PROOF
    tampered = intent(action="register")
    assert registry.verify(request(intent_payload=tampered, expected_action=WalletAuthAction.LOGIN)).reason_code == WalletProofVerificationReason.ACTION_MISMATCH
    wrong_hash = request(intent_hash="sha256:" + "0" * 64)
    assert registry.verify(wrong_hash).reason_code == WalletProofVerificationReason.INTENT_HASH_MISMATCH
    wrong_origin = intent(origin="https://evil.example")
    assert registry.verify(request(intent_payload=wrong_origin)).reason_code == WalletProofVerificationReason.ORIGIN_MISMATCH
    wrong_network = intent(network="bitcoin-testnet")
    assert registry.verify(request(intent_payload=wrong_network)).reason_code == WalletProofVerificationReason.UNSUPPORTED_NETWORK
    expired = intent()
    expired["expires_at"] = NOW - timedelta(seconds=1)
    assert registry.verify(request(intent_payload=expired, current_time=NOW, intent_hash=hash_intent(expired))).reason_code == WalletProofVerificationReason.INTENT_EXPIRED
    future = intent()
    future["issued_at"] = NOW + timedelta(minutes=10)
    future["expires_at"] = NOW + timedelta(minutes=20)
    assert registry.verify(request(intent_payload=future, intent_hash=hash_intent(future))).reason_code == WalletProofVerificationReason.INTENT_NOT_YET_VALID
    tampered_device = intent(device_key_fingerprint="dev_fp_other")
    assert registry.verify(request(intent_payload=tampered_device)).reason_code == WalletProofVerificationReason.DEVICE_MISMATCH
    no_warning = intent()
    no_warning["warnings"] = ()
    assert registry.verify(request(intent_payload=no_warning)).reason_code == WalletProofVerificationReason.MALFORMED_PROOF


def test_nonce_challenge_and_strength_failures():
    registry = WalletProofVerifierRegistry()
    registry.register(SuccessVerifier())
    assert registry.verify(request(expected_nonce_hash="sha256:" + "1" * 64)).reason_code == WalletProofVerificationReason.NONCE_MISMATCH
    assert registry.verify(request(expected_challenge_id="other")).reason_code == WalletProofVerificationReason.CHALLENGE_MISMATCH
    too_strong = request(requested_verification_strength=WalletVerificationStrength.HIGH_ASSURANCE)
    assert registry.verify(too_strong).reason_code == WalletProofVerificationReason.VERIFICATION_STRENGTH_INSUFFICIENT
    legacy_critical_payload = intent(action="treasury_policy_change")
    legacy_critical = request(
        intent_payload=legacy_critical_payload,
        proof_type=WalletProofType.LEGACY_MESSAGE_SIGNATURE,
        expected_action=WalletAuthAction.TREASURY_POLICY_CHANGE,
        requested_verification_strength=WalletVerificationStrength.COMPATIBILITY,
    )
    registry.register(LegacyMessageVerifierStub())
    assert registry.verify(legacy_critical).reason_code == WalletProofVerificationReason.VERIFICATION_STRENGTH_INSUFFICIENT


def test_revocation_boundary_fails_closed_for_revoked_and_high_risk_unavailable():
    registry = WalletProofVerifierRegistry(revocation_checker=RevokedChecker())
    registry.register(SuccessVerifier())
    result = registry.verify(request())
    assert not result.verified
    assert result.reason_code == WalletProofVerificationReason.PROOF_REVOKED

    unavailable = WalletProofVerifierRegistry(revocation_checker=RevokedChecker(fail=True))
    unavailable.register(SuccessVerifier())
    result = unavailable.verify(request(requested_verification_strength=WalletVerificationStrength.HIGH_ASSURANCE))
    assert not result.verified
    assert result.reason_code == WalletProofVerificationReason.VERIFIER_UNAVAILABLE


def test_placeholder_adapters_never_return_success_and_document_future_prompts():
    registry = build_default_placeholder_registry()
    assert set(registry.supported_proof_types()) >= {
        WalletProofType.BIP322,
        WalletProofType.LEGACY_MESSAGE_SIGNATURE,
        WalletProofType.HARDWARE_WALLET,
        WalletProofType.AIR_GAPPED,
        WalletProofType.MULTISIG_QUORUM,
        WalletProofType.LNURL_AUTH,
        WalletProofType.ACCESS_CERTIFICATE_BRIDGE,
    }
    for proof_type in registry.supported_proof_types():
        result = registry.verify(request(proof_type=proof_type))
        assert not result.verified
        assert result.reason_code in {
            WalletProofVerificationReason.NOT_IMPLEMENTED,
            WalletProofVerificationReason.UNSUPPORTED_NETWORK,
            WalletProofVerificationReason.PREFIX_REQUIRED,
            WalletProofVerificationReason.SCRIPT_BACKEND_UNAVAILABLE,
            WalletProofVerificationReason.LEGACY_SIGNATURE_DISABLED,
        }
        assert any("Prompt" in limitation for limitation in result.limitations) or result.reason_code in {WalletProofVerificationReason.UNSUPPORTED_NETWORK, WalletProofVerificationReason.PREFIX_REQUIRED, WalletProofVerificationReason.SCRIPT_BACKEND_UNAVAILABLE, WalletProofVerificationReason.LEGACY_SIGNATURE_DISABLED}


def test_hardware_and_sovereign_are_not_granted_by_claims_or_single_verifier():
    registry = WalletProofVerifierRegistry()
    registry.register(SuccessVerifier())
    hardware_claim = request(hardware_wallet_claim={"claimed": True}, requested_verification_strength=WalletVerificationStrength.HIGH_ASSURANCE)
    assert registry.verify(hardware_claim).reason_code == WalletProofVerificationReason.VERIFICATION_STRENGTH_INSUFFICIENT
    sovereign_claim = replace(hardware_claim, requested_verification_strength=WalletVerificationStrength.SOVEREIGN, quorum_claim={"claimed": True})
    assert registry.verify(sovereign_claim).reason_code == WalletProofVerificationReason.VERIFICATION_STRENGTH_INSUFFICIENT


def test_import_safety():
    import app.services.wallet_auth.proof_verifier as proof_verifier
    import app.services.wallet_auth.verifiers.base as base

    assert proof_verifier.WalletProofVerifierRegistry is not None
    assert base.WalletProofVerificationRequest is not None
