import asyncio

import pytest
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec, utils

from app.services.lnurl.payer_data import parse_payerdata
from app.services.lnurl.payer_data_auth import LNURLPayerDataAuthService, PayerAuthConfig, PayerDataK1UsedError


class Request:
    request_id = "req"
    product_code = "pro"
    plan_code = "pro"
    policy_hash = "sha256:policy"


def sign(k1: str):
    key = ec.generate_private_key(ec.SECP256K1())
    pub = key.public_key().public_bytes(serialization.Encoding.X962, serialization.PublicFormat.CompressedPoint).hex()
    while True:
        sig = key.sign(bytes.fromhex(k1), ec.ECDSA(utils.Prehashed(hashes.SHA256())))
        _, s = utils.decode_dss_signature(sig)
        if s <= int("FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141", 16) // 2:
            return parse_payerdata({"auth": {"key": pub, "k1": k1, "sig": sig.hex()}}, require_auth=True).auth


def test_modified_replay_rejected_after_one_success() -> None:
    svc = LNURLPayerDataAuthService(config=PayerAuthConfig())
    challenge = asyncio.run(svc.create_payer_auth_challenge(payment_request_id="req", auth_domain="auth.bitcoin-bastion.com", product_context="pro", plan_code="pro", policy_hash="sha256:policy"))
    auth = sign(challenge.k1)
    asyncio.run(svc.verify_payerdata_auth(payment_request=Request(), parsed_auth=auth, expected_domain="auth.bitcoin-bastion.com", expected_policy_hash="sha256:policy", callback_fingerprint="sha256:accepted"))
    retry = asyncio.run(svc.verify_payerdata_auth(payment_request=Request(), parsed_auth=auth, expected_domain="auth.bitcoin-bastion.com", expected_policy_hash="sha256:policy", callback_fingerprint="sha256:accepted"))
    assert retry.idempotent_replay is True
    with pytest.raises(PayerDataK1UsedError):
        asyncio.run(svc.verify_payerdata_auth(payment_request=Request(), parsed_auth=auth, expected_domain="auth.bitcoin-bastion.com", expected_policy_hash="sha256:policy", callback_fingerprint="sha256:tampered"))
