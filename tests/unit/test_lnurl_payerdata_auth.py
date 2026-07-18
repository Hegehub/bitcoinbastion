import asyncio

import pytest
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec, utils

from app.services.lnurl.payer_data import parse_payerdata
from app.services.lnurl.payer_data_auth import LNURLPayerDataAuthService, PayerAuthConfig, PayerDataK1UsedError, PayerDataSignatureInvalidError


class Request:
    request_id = "req_1"
    product_code = "pro_pass"
    plan_code = "pro_pass"
    policy_hash = "sha256:policy"


def _signed_payload(k1: str, private_key: ec.EllipticCurvePrivateKey | None = None) -> tuple[dict[str, dict[str, str]], ec.EllipticCurvePrivateKey]:
    private_key = private_key or ec.generate_private_key(ec.SECP256K1())
    pub = private_key.public_key().public_bytes(serialization.Encoding.X962, serialization.PublicFormat.CompressedPoint).hex()
    while True:
        sig = private_key.sign(bytes.fromhex(k1), ec.ECDSA(utils.Prehashed(hashes.SHA256())))
        _, s = utils.decode_dss_signature(sig)
        if s <= int("FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141", 16) // 2:
            break
    return {"auth": {"key": pub, "k1": k1, "sig": sig.hex()}}, private_key


def test_valid_signature_creates_principal_and_consumes_k1() -> None:
    svc = LNURLPayerDataAuthService(config=PayerAuthConfig(canonical_domain="auth.bitcoin-bastion.com"))
    challenge = asyncio.run(svc.create_payer_auth_challenge(payment_request_id="req_1", auth_domain="auth.bitcoin-bastion.com", product_context="pro_pass", plan_code="pro_pass", policy_hash="sha256:policy"))
    payload, _ = _signed_payload(challenge.k1)
    parsed = parse_payerdata(payload, require_auth=True)
    verified = asyncio.run(svc.verify_payerdata_auth(payment_request=Request(), parsed_auth=parsed.auth, expected_domain="auth.bitcoin-bastion.com", expected_policy_hash="sha256:policy", callback_fingerprint="sha256:callback"))
    assert verified.verified is True
    assert verified.principal_hash.startswith("hmac-sha256:")
    assert verified.product_pseudonym.startswith("hmac-sha256:")


def test_exact_retry_is_idempotent_modified_replay_rejected() -> None:
    svc = LNURLPayerDataAuthService(config=PayerAuthConfig())
    challenge = asyncio.run(svc.create_payer_auth_challenge(payment_request_id="req_1", auth_domain="auth.bitcoin-bastion.com", product_context="pro_pass", plan_code="pro_pass", policy_hash="sha256:policy"))
    payload, _ = _signed_payload(challenge.k1)
    parsed = parse_payerdata(payload, require_auth=True)
    first = asyncio.run(svc.verify_payerdata_auth(payment_request=Request(), parsed_auth=parsed.auth, expected_domain="auth.bitcoin-bastion.com", expected_policy_hash="sha256:policy", callback_fingerprint="sha256:same"))
    second = asyncio.run(svc.verify_payerdata_auth(payment_request=Request(), parsed_auth=parsed.auth, expected_domain="auth.bitcoin-bastion.com", expected_policy_hash="sha256:policy", callback_fingerprint="sha256:same"))
    assert first.principal_hash == second.principal_hash
    assert second.idempotent_replay is True
    with pytest.raises(PayerDataK1UsedError):
        asyncio.run(svc.verify_payerdata_auth(payment_request=Request(), parsed_auth=parsed.auth, expected_domain="auth.bitcoin-bastion.com", expected_policy_hash="sha256:policy", callback_fingerprint="sha256:different"))


def test_invalid_signature_fails() -> None:
    svc = LNURLPayerDataAuthService(config=PayerAuthConfig())
    challenge = asyncio.run(svc.create_payer_auth_challenge(payment_request_id="req_1", auth_domain="auth.bitcoin-bastion.com", product_context="pro_pass", plan_code="pro_pass", policy_hash="sha256:policy"))
    payload, other = _signed_payload("bb" * 32)
    payload["auth"]["k1"] = challenge.k1
    parsed = parse_payerdata(payload, require_auth=True)
    with pytest.raises(PayerDataSignatureInvalidError):
        asyncio.run(svc.verify_payerdata_auth(payment_request=Request(), parsed_auth=parsed.auth, expected_domain="auth.bitcoin-bastion.com", expected_policy_hash="sha256:policy"))
