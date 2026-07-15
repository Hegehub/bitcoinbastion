from __future__ import annotations

from datetime import UTC, datetime, timedelta
from urllib.parse import parse_qs, urlsplit

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec, utils

from app.domain.lnurl.auth import LNURLAuthAction
from app.domain.wallet_auth.proofs import WalletVerificationStrength
from app.services.lnurl.auth_callback_verifier import (
    SECP256K1_ORDER,
    LNURLAuthCallbackConfig,
    LNURLAuthCallbackStatus,
    LNURLAuthCallbackVerifier,
)
from app.services.lnurl.auth_challenge_service import LNURLAuthChallengeConfig, LNURLAuthChallengeService
from app.services.lnurl.k1_registry import InMemoryK1Repository, LNURLK1Config, LNURLK1RegistryService

NOW = datetime(2026, 7, 15, tzinfo=UTC)


def _signing_material(k1: str) -> tuple[str, str]:
    private_key = ec.generate_private_key(ec.SECP256K1())
    public_hex = private_key.public_key().public_bytes(
        serialization.Encoding.X962,
        serialization.PublicFormat.CompressedPoint,
    ).hex()
    while True:
        signature_bytes = private_key.sign(bytes.fromhex(k1), ec.ECDSA(utils.Prehashed(hashes.SHA256())))
        _r, s_value = utils.decode_dss_signature(signature_bytes)
        if s_value <= SECP256K1_ORDER // 2:
            return public_hex, signature_bytes.hex()


def _services(*, clock=lambda: NOW, events=None):
    repo = InMemoryK1Repository()
    registry = LNURLK1RegistryService(
        config=LNURLK1Config(server_pepper="test-k1-pepper", allow_test_pepper=True),
        repository=repo,
        clock=clock,
    )
    challenge_service = LNURLAuthChallengeService(
        config=LNURLAuthChallengeConfig(),
        k1_registry=registry,
        clock=clock,
    )
    verifier = LNURLAuthCallbackVerifier(
        config=LNURLAuthCallbackConfig(principal_server_pepper="test-principal-pepper", allow_test_pepper=True),
        k1_registry=registry,
        challenge_repository=challenge_service.repository,
        clock=clock,
        audit_emitter=(lambda event, payload: events.append((event, payload))) if events is not None else None,
    )
    return challenge_service, verifier


def _challenge_and_signed_callback(action: str = "login", *, device: str | None = None):
    service, verifier = _services()
    challenge = service.create_challenge(
        action=action,
        origin="https://bitcoin-bastion.com",
        device_key_fingerprint=device,
        policy_hash="sha256:policy",
        risk_level="medium",
    )
    k1 = parse_qs(urlsplit(challenge.callback_url).query)["k1"][0]
    key, sig = _signing_material(k1)
    return challenge, verifier, k1, key, sig


def test_valid_lnurl_auth_callback_verifies_and_consumes_once() -> None:
    challenge, verifier, k1, key, sig = _challenge_and_signed_callback()
    result = verifier.verify_callback(k1=k1, key=key, sig=sig, action="login", callback_host="auth.bitcoin-bastion.com")
    assert result.verified is True
    assert result.response.as_lnurl_json() == {"status": "OK"}
    assert result.challenge_id == challenge.challenge_id
    assert result.lnurl_action is LNURLAuthAction.LOGIN
    assert result.bastion_action == "wallet_principal_authenticate"
    assert result.key_fingerprint and result.key_fingerprint.startswith("sha256:")
    assert result.lnurl_key_hash and result.lnurl_key_hash.startswith("hmac-sha256:")
    assert result.verification_strength is WalletVerificationStrength.STANDARD
    assert result.proof is not None
    assert result.proof.device_key_fingerprint is None
    replay = verifier.verify_callback(k1=k1, key=key, sig=sig, action="login", callback_host="auth.bitcoin-bastion.com")
    assert replay.verified is False
    assert replay.response.status is LNURLAuthCallbackStatus.ERROR
    assert replay.response.as_lnurl_json()["reason"] == "Authentication request could not be verified."


def test_strict_validation_rejects_malformed_inputs_before_crypto() -> None:
    _challenge, verifier, k1, key, sig = _challenge_and_signed_callback()
    assert verifier.verify_callback(k1="abc", key=key, sig=sig).reason_code == "malformed_k1"
    assert verifier.verify_callback(k1=k1, key="04" + key[2:], sig=sig).reason_code == "invalid_public_key"
    assert verifier.verify_callback(k1=k1, key=key, sig="zz").reason_code == "malformed_signature"
    assert verifier.verify_callback(k1=k1, key=key, sig=sig, query_params={"k1": [k1, k1], "key": key, "sig": sig}).verified is False


def test_action_domain_policy_and_signature_mismatches_are_rejected() -> None:
    _challenge, verifier, k1, key, sig = _challenge_and_signed_callback()
    assert verifier.verify_callback(k1=k1, key=key, sig=sig, action="auth").reason_code == "action_mismatch"
    assert verifier.verify_callback(k1=k1, key=key, sig=sig, action="login", callback_host="evil.example").reason_code == "domain_mismatch"
    wrong_k1 = "00" * 32
    _wrong_key, wrong_sig = _signing_material(wrong_k1)
    assert verifier.verify_callback(k1=k1, key=key, sig=wrong_sig, action="login").reason_code in {"invalid_signature", "malformed_signature"}


def test_expired_challenge_and_device_bound_result() -> None:
    now = {"value": NOW}
    service, verifier = _services(clock=lambda: now["value"])
    challenge = service.create_challenge(
        action="auth",
        origin="https://bitcoin-bastion.com",
        device_key_fingerprint="sha256:device",
        policy_hash="sha256:policy",
        risk_level="high",
    )
    k1 = parse_qs(urlsplit(challenge.callback_url).query)["k1"][0]
    key, sig = _signing_material(k1)
    now["value"] = NOW + timedelta(seconds=301)
    assert verifier.verify_callback(k1=k1, key=key, sig=sig, action="auth").reason_code == "expired_k1"
    now["value"] = NOW
    challenge2 = service.create_challenge(
        action="auth",
        origin="https://bitcoin-bastion.com",
        device_key_fingerprint="sha256:device",
        policy_hash="sha256:policy2",
        risk_level="high",
    )
    k12 = parse_qs(urlsplit(challenge2.callback_url).query)["k1"][0]
    key2, sig2 = _signing_material(k12)
    result = verifier.verify_callback(k1=k12, key=key2, sig=sig2, action="auth")
    assert result.verified is True
    assert result.device_key_fingerprint == "sha256:device"


def test_audit_events_are_safe_and_use_generic_public_error() -> None:
    events = []
    service, verifier = _services(events=events)
    challenge = service.create_challenge(action="login", origin="https://bitcoin-bastion.com", policy_hash="sha256:policy", risk_level="medium")
    k1 = parse_qs(urlsplit(challenge.callback_url).query)["k1"][0]
    key, sig = _signing_material(k1)
    result = verifier.verify_callback(k1=k1, key=key, sig=sig, action="login")
    assert result.verified is True
    rendered = repr(events)
    assert k1 not in rendered
    assert key not in rendered
    assert sig not in rendered
    assert events and events[0][0] == "lnurl_auth_callback_success"
