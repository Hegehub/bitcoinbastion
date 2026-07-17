from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from urllib.parse import parse_qs, urlsplit

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec, utils

from app.services.lnurl.auth_callback_verifier import SECP256K1_ORDER, LNURLAuthCallbackConfig, LNURLAuthCallbackVerifier
from app.services.lnurl.auth_challenge_service import LNURLAuthChallengeConfig, LNURLAuthChallengeService
from app.services.lnurl.k1_registry import InMemoryK1Repository, LNURLK1Config, LNURLK1RegistryService

NOW = datetime(2026, 7, 15, tzinfo=UTC)


def _sign(k1: str) -> tuple[str, str]:
    private_key = ec.generate_private_key(ec.SECP256K1())
    public_hex = private_key.public_key().public_bytes(serialization.Encoding.X962, serialization.PublicFormat.CompressedPoint).hex()
    while True:
        signature_bytes = private_key.sign(bytes.fromhex(k1), ec.ECDSA(utils.Prehashed(hashes.SHA256())))
        _r, s_value = utils.decode_dss_signature(signature_bytes)
        if s_value <= SECP256K1_ORDER // 2:
            return public_hex, signature_bytes.hex()


def _build(events=None):
    registry = LNURLK1RegistryService(
        config=LNURLK1Config(server_pepper="test-k1-pepper", allow_test_pepper=True),
        repository=InMemoryK1Repository(),
        clock=lambda: NOW,
    )
    challenge_service = LNURLAuthChallengeService(config=LNURLAuthChallengeConfig(), k1_registry=registry, clock=lambda: NOW)
    verifier = LNURLAuthCallbackVerifier(
        config=LNURLAuthCallbackConfig(principal_server_pepper="test-principal-pepper", allow_test_pepper=True),
        k1_registry=registry,
        challenge_repository=challenge_service.repository,
        clock=lambda: NOW,
        audit_emitter=(lambda event, payload: events.append((event, payload))) if events is not None else None,
    )
    challenge = challenge_service.create_challenge(action="login", origin="https://bitcoin-bastion.com", policy_hash="sha256:policy", risk_level="medium")
    k1 = parse_qs(urlsplit(challenge.callback_url).query)["k1"][0]
    key, sig = _sign(k1)
    return verifier, k1, key, sig


def test_raw_k1_signature_and_key_are_not_logged_or_returned() -> None:
    events = []
    verifier, k1, key, sig = _build(events)
    result = verifier.verify_callback(k1=k1, key=key, sig=sig, action="login")
    rendered = repr(events) + repr(result) + repr(result.response.as_lnurl_json())
    assert k1 not in rendered
    assert sig not in rendered
    assert key not in rendered
    assert "session_token" not in rendered
    assert "access_certificate" not in rendered


def test_unknown_and_reused_k1_have_same_public_error_shape() -> None:
    verifier, k1, key, sig = _build()
    ok = verifier.verify_callback(k1=k1, key=key, sig=sig, action="login")
    assert ok.verified is True
    reused = verifier.verify_callback(k1=k1, key=key, sig=sig, action="login")
    unknown = verifier.verify_callback(k1="11" * 32, key=key, sig=sig, action="login")
    assert reused.response.as_lnurl_json() == unknown.response.as_lnurl_json()
    assert reused.verified is False and unknown.verified is False


def test_concurrent_double_callback_allows_exactly_one_success() -> None:
    verifier, k1, key, sig = _build()
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: verifier.verify_callback(k1=k1, key=key, sig=sig, action="login").verified, range(2)))
    assert results.count(True) == 1
    assert results.count(False) == 1


def test_malformed_der_oversized_values_domain_action_and_seed_inputs_fail_safely() -> None:
    verifier, k1, key, sig = _build()
    assert verifier.verify_callback(k1=k1, key=key, sig="30", action="login").verified is False
    assert verifier.verify_callback(k1=k1, key=key, sig="30" * 200, action="login").reason_code == "malformed_signature"
    assert verifier.verify_callback(k1=k1, key=key, sig=sig, action="auth").reason_code == "action_mismatch"
    assert verifier.verify_callback(k1=k1, key=key, sig=sig, action="login", callback_host="evil.example").reason_code == "domain_mismatch"
    assert verifier.verify_callback(k1=k1 + "seed", key=key, sig=sig, action="login").verified is False


def test_callback_cannot_issue_session_entitlement_or_access_certificate() -> None:
    verifier, k1, key, sig = _build()
    result = verifier.verify_callback(k1=k1, key=key, sig=sig, action="login")
    assert result.verified is True
    assert not hasattr(result, "session_token")
    assert not hasattr(result, "entitlement_id")
    assert not hasattr(result, "access_certificate")
