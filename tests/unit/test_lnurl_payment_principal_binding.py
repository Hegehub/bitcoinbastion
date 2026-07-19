import asyncio

import pytest
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec, utils

from app.services.lnurl.payer_data import parse_payerdata
from app.services.lnurl.payer_data_auth import LNURLPayerDataAuthService, PayerAuthConfig, PayerDataPaymentMismatchError


class Request:
    def __init__(self, request_id="req_1", product_code="pro_pass", plan_code="pro_pass") -> None:
        self.request_id = request_id
        self.product_code = product_code
        self.plan_code = plan_code
        self.policy_hash = "sha256:policy"


def sign(k1: str, key: ec.EllipticCurvePrivateKey | None = None):
    key = key or ec.generate_private_key(ec.SECP256K1())
    pub = key.public_key().public_bytes(serialization.Encoding.X962, serialization.PublicFormat.CompressedPoint).hex()
    while True:
        sig = key.sign(bytes.fromhex(k1), ec.ECDSA(utils.Prehashed(hashes.SHA256())))
        _, s = utils.decode_dss_signature(sig)
        if s <= int("FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141", 16) // 2:
            return {"auth": {"key": pub, "k1": k1, "sig": sig.hex()}}, key


def test_existing_principal_resolved_without_duplicate_and_pseudonyms_differ() -> None:
    svc = LNURLPayerDataAuthService(config=PayerAuthConfig())
    key = ec.generate_private_key(ec.SECP256K1())
    c1 = asyncio.run(svc.create_payer_auth_challenge(payment_request_id="req_1", auth_domain="auth.bitcoin-bastion.com", product_context="pro_pass", plan_code="pro_pass", policy_hash="sha256:policy"))
    payload1, _ = sign(c1.k1, key)
    p1 = parse_payerdata(payload1, require_auth=True)
    v1 = asyncio.run(svc.verify_payerdata_auth(payment_request=Request(), parsed_auth=p1.auth, expected_domain="auth.bitcoin-bastion.com", expected_policy_hash="sha256:policy"))
    c2 = asyncio.run(svc.create_payer_auth_challenge(payment_request_id="req_2", auth_domain="auth.bitcoin-bastion.com", product_context="payregister", plan_code="pro_pass", policy_hash="sha256:policy"))
    payload2, _ = sign(c2.k1, key)
    p2 = parse_payerdata(payload2, require_auth=True)
    v2 = asyncio.run(svc.verify_payerdata_auth(payment_request=Request("req_2", "payregister", "pro_pass"), parsed_auth=p2.auth, expected_domain="auth.bitcoin-bastion.com", expected_policy_hash="sha256:policy"))
    assert v1.principal_hash == v2.principal_hash
    assert v1.product_pseudonym != v2.product_pseudonym


def test_wrong_payment_request_binding_fails() -> None:
    svc = LNURLPayerDataAuthService(config=PayerAuthConfig())
    c = asyncio.run(svc.create_payer_auth_challenge(payment_request_id="req_1", auth_domain="auth.bitcoin-bastion.com", product_context="pro_pass", plan_code="pro_pass", policy_hash="sha256:policy"))
    payload, _ = sign(c.k1)
    parsed = parse_payerdata(payload, require_auth=True)
    with pytest.raises(PayerDataPaymentMismatchError):
        asyncio.run(svc.verify_payerdata_auth(payment_request=Request("req_other"), parsed_auth=parsed.auth, expected_domain="auth.bitcoin-bastion.com", expected_policy_hash="sha256:policy"))
