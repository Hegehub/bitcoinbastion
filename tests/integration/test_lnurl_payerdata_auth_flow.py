from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta
from typing import Any

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec, utils

from app.services.lnurl.pay.subscription_request_service import InMemoryLNURLPaySubscriptionRequestRepository, LNURLPaySubscriptionRequestConfig, LNURLPaySubscriptionRequestService
from app.services.lnurl.pay_callback_service import InMemoryLNURLPayCallbackRepository, LightningInvoiceResult, LNURLPayCallbackCommand, LNURLPayCallbackService
from app.services.lnurl.payer_data_auth import LNURLPayerDataAuthService, PayerAuthConfig

NOW = datetime(2026, 7, 18, tzinfo=UTC)


class Provider:
    provider_name = "trusted-test-provider"
    def __init__(self) -> None:
        self.calls = 0
    async def create_invoice(self, *, amount_msat: int, description_hash: str, expiry_seconds: int, idempotency_key: str, metadata: dict[str, Any]) -> LightningInvoiceResult:
        self.calls += 1
        return LightningInvoiceResult("inv", f"lnbc{amount_msat}n1auth", "paymenthash", NOW + timedelta(seconds=expiry_seconds), self.provider_name)


def sign(k1: str) -> dict[str, dict[str, str]]:
    key = ec.generate_private_key(ec.SECP256K1())
    pub = key.public_key().public_bytes(serialization.Encoding.X962, serialization.PublicFormat.CompressedPoint).hex()
    while True:
        sig = key.sign(bytes.fromhex(k1), ec.ECDSA(utils.Prehashed(hashes.SHA256())))
        _, s = utils.decode_dss_signature(sig)
        if s <= int("FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141", 16) // 2:
            return {"auth": {"key": pub, "k1": k1, "sig": sig.hex()}}


def test_payerdata_auth_binds_request_but_does_not_settle_or_entitle() -> None:
    auth = LNURLPayerDataAuthService(config=PayerAuthConfig(canonical_domain="auth.bitcoin-bastion.com"), clock=lambda: NOW)
    request_repo = InMemoryLNURLPaySubscriptionRequestRepository()
    request_service = LNURLPaySubscriptionRequestService(repository=request_repo, payer_auth_service=auth, config=LNURLPaySubscriptionRequestConfig(public_base_url="https://auth.bitcoin-bastion.com", payerdata_auth_enabled=True), clock=lambda: NOW)
    pay = request_service.create_subscription_request(plan_code="pro_pass", principal_hash=None, actor_type=None, product_code="pro_pass", payer_data_mode="auth_mandatory")
    response = pay.to_lnurl_response()
    k1 = response["payerData"]["auth"]["k1"]
    assert len(k1) == 64
    record = next(iter(request_repo.records.values()))
    callback_repo = InMemoryLNURLPayCallbackRepository({record.request_id: record})
    provider = Provider()
    callback = LNURLPayCallbackService(repository=callback_repo, invoice_provider=provider, payer_auth_service=auth, clock=lambda: NOW)
    payload = sign(k1)
    invoice = asyncio.run(callback.create_invoice(LNURLPayCallbackCommand(record.request_id, record.min_amount_msat, payer_data=payload)))
    persisted = callback_repo.get_invoice_by_request_id(record.request_id)
    assert invoice.payment_status == "invoice_issued"
    assert persisted is not None and persisted.lightning_principal_hash
    assert persisted.payer_auth_proof_hash
    assert callback_repo.count_payment_proofs() == 0
    assert callback_repo.count_entitlements() == 0
    again = asyncio.run(callback.create_invoice(LNURLPayCallbackCommand(record.request_id, record.min_amount_msat, payer_data=payload)))
    assert again.pr == invoice.pr
    assert provider.calls == 1
