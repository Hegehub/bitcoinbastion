from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest

from app.services.lnurl.lightning_address_service import LightningAddressService
from app.services.lnurl.pay.errors import LNURLPayInvalidAmountError
from app.services.lnurl.pay_callback_service import (
    InMemoryLNURLPayCallbackRepository,
    LightningInvoiceResult,
    LNURLPayCallbackCommand,
    LNURLPayCallbackService,
)
from tests.unit.test_lnurl_entitlement_binding_service import make_proof, principal
from app.services.lnurl.entitlement_binding_service import AccessRequestContext, LNURLEntitlementBindingMode, LNURLEntitlementBindingService

NOW = datetime(2026, 7, 18, tzinfo=UTC)


class FakeProvider:
    provider_name = "trusted-test-provider"

    def __init__(self) -> None:
        self.calls = 0

    async def create_invoice(self, *, amount_msat: int, description_hash: str, expiry_seconds: int, idempotency_key: str, metadata: dict[str, Any]) -> LightningInvoiceResult:
        self.calls += 1
        suffix = idempotency_key[-10:]
        return LightningInvoiceResult(
            provider_invoice_id=f"inv-{suffix}",
            bolt11=f"lnbc{amount_msat}n1{suffix}",
            payment_hash=f"payment-{suffix}",
            expires_at=NOW + timedelta(seconds=expiry_seconds),
            provider_name=self.provider_name,
        )


def run(coro: Any) -> Any:
    return asyncio.run(coro)


def test_product_callback_amount_must_match_and_invoice_does_not_issue_entitlement() -> None:
    address_service = LightningAddressService(clock=lambda: NOW)
    address_service.install_product_addresses()
    resolution = address_service.resolve_address("pro@bitcoin-bastion.com")
    request = next(iter(address_service.pay_request_service.repository.records.values()))
    assert request.product_code == "pro"
    assert request.plan_code == "pro_pass"
    assert request.fixed_amount_msat == 500_000_000
    repo = InMemoryLNURLPayCallbackRepository({request.request_id: request})
    callback = LNURLPayCallbackService(repository=repo, invoice_provider=FakeProvider(), clock=lambda: NOW)
    with pytest.raises(LNURLPayInvalidAmountError):
        run(callback.create_invoice(LNURLPayCallbackCommand(request.request_id, resolution.min_sendable_msat - 1)))
    invoice = run(callback.create_invoice(LNURLPayCallbackCommand(request.request_id, resolution.min_sendable_msat)))
    assert invoice.amount_msat == 500_000_000
    assert invoice.metadata_hash == request.metadata_hash
    assert repo.count_entitlements() == 0
    assert repo.count_payment_proofs() == 0


def test_verified_settlement_entitlement_uses_server_authoritative_product_plan() -> None:
    proof_service, proof = make_proof(plan="pro_pass", amount=500_000_000)
    binding = LNURLEntitlementBindingService(payment_proof_service=proof_service)
    result = run(
        binding.bind_settled_payment_to_principal(
            payment_proof_id=proof.proof_id,
            principal_reference=principal(LNURLEntitlementBindingMode.PAYERDATA_AUTH),
            request_context=AccessRequestContext(wallet_proof_fresh=True),
        )
    )
    assert result.plan_code == "pro_pass"
    assert result.entitlement_status == "active"
    replay = run(
        binding.bind_settled_payment_to_principal(
            payment_proof_id=proof.proof_id,
            principal_reference=principal(LNURLEntitlementBindingMode.PAYERDATA_AUTH),
        )
    )
    assert replay.idempotent_replay
    assert replay.entitlement_id == result.entitlement_id
