from __future__ import annotations

from datetime import UTC, datetime

from app.services.lnurl.pay.subscription_request_service import (
    InMemoryLNURLPaySubscriptionRequestRepository,
    LNURLPaySubscriptionRequestConfig,
    LNURLPaySubscriptionRequestService,
)


def test_lnurl_pay_subscription_request_boundary_flow() -> None:
    repository = InMemoryLNURLPaySubscriptionRequestRepository()
    service = LNURLPaySubscriptionRequestService(
        repository=repository,
        config=LNURLPaySubscriptionRequestConfig(public_base_url="https://pay.example.com", request_ttl_seconds=300),
        clock=lambda: datetime(2026, 7, 17, 12, 0, tzinfo=UTC),
    )

    result = service.create_subscription_request(
        plan_code="pro_pass",
        principal_hash="hmac-sha256:principal",
        actor_type="lightning_wallet_principal",
        product_code="bastion_access",
        requested_amount_msat=None,
        origin="https://app.example.com",
        locale="en-US",
        idempotency_key="safe-client-key",
        payer_data_mode=None,
        comment_allowed=None,
        success_action_mode="none",
        request_context={"client_hash": "sha256:client"},
    )
    record = next(iter(repository.records.values()))

    assert result.to_lnurl_response()["tag"] == "payRequest"
    assert record.status.value == "pending_callback"
    assert repository.get_by_reference_hash(record.request_reference_hash) == record
    assert repository.count_invoices() == 0
    assert repository.count_payment_proofs() == 0
    assert repository.count_entitlements() == 0
