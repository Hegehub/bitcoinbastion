from __future__ import annotations

import base64
from datetime import UTC, datetime, timedelta

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from app.schemas.lnurl_receipt import (
    LNURLReceiptAuditContext,
    LNURLReceiptMerchantContext,
    LNURLReceiptPaymentContext,
    LNURLReceiptPolicyContext,
    LNURLReceiptSettlementEvidence,
    LNURLReceiptSubscriptionContext,
    LNURLReceiptType,
    LNURLReceiptVisibility,
)
from app.services.lnurl.receipt_packet import (
    LNURLReceiptInvariantError,
    LNURLReceiptIssuerKeyRegistry,
    LNURLReceiptPacketConfig,
    LNURLReceiptPacketService,
)


def keys() -> tuple[str, str]:
    private = Ed25519PrivateKey.generate()
    raw_private = private.private_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PrivateFormat.Raw,
        encryption_algorithm=serialization.NoEncryption(),
    )
    raw_public = private.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    return base64.urlsafe_b64encode(raw_private).decode().rstrip("="), base64.urlsafe_b64encode(raw_public).decode().rstrip("=")


@pytest.fixture
def signed_service():
    priv, pub = keys()
    service = LNURLReceiptPacketService(config=LNURLReceiptPacketConfig(issuer_private_key=priv))
    return service, LNURLReceiptIssuerKeyRegistry({"bastion-lnurl-receipt-v1": pub})


def payment(*, settled: bool = True, amount_msat: int = 2_500_000, network: str = "bitcoin-mainnet") -> LNURLReceiptSettlementEvidence:
    return LNURLReceiptSettlementEvidence(
        lnurl_pay_request_hash="sha256:req",
        lnurl_callback_hash="sha256:callback",
        payment_proof_hash="sha256:proof",
        payment_hash="hmac-sha256:payment",
        invoice_hash="sha256:invoice",
        amount_msat=amount_msat,
        amount_sats=amount_msat // 1000,
        currency="BTC",
        settlement_method="lnurl_verify" if network == "bitcoin-mainnet" else "manual_test_settlement",
        settled=settled,
        preimage_hash="sha256:preimage",
        metadata_hash="sha256:metadata",
        comment_hash="sha256:comment",
        payer_data_hash="sha256:payerdata",
    )


def subscription() -> LNURLReceiptSubscriptionContext:
    now = datetime.now(UTC)
    return LNURLReceiptSubscriptionContext(plan_code="pro_pass", entitlement_hash="sha256:entitlement", entitlement_status="active", valid_from=now, valid_until=now + timedelta(days=30))


def merchant() -> LNURLReceiptMerchantContext:
    return LNURLReceiptMerchantContext(workspace_alias="hmac-sha256:workspace", store_alias="hmac-sha256:store", terminal_alias="hmac-sha256:terminal", shift_alias="hmac-sha256:shift", order_reference_hash="sha256:order", merchant_invoice_hash="sha256:merchant-invoice")


def policy() -> LNURLReceiptPolicyContext:
    return LNURLReceiptPolicyContext(decision="allow", policy_hash="sha256:policy", policy_epoch=1, decision_event_hash="sha256:policy-event")


def audit() -> LNURLReceiptAuditContext:
    return LNURLReceiptAuditContext(payment_settled_event_hash="sha256:settled-event", payment_proof_event_hash="sha256:proof-event", entitlement_event_hash="sha256:entitlement-event", receipt_created_event_hash="sha256:receipt-event")


def test_valid_settled_subscription_receipt_created_signed_and_verified(signed_service):
    service, registry = signed_service
    packet = service.create_subscription_receipt(payment=payment(), subscription=subscription(), policy=policy(), audit=audit(), network="bitcoin-mainnet", settled_at=datetime.now(UTC), payment_context=LNURLReceiptPaymentContext(product_code="pro_pass", safe_description="Bitcoin Bastion Pro Pass"))
    assert packet.receipt_type == LNURLReceiptType.SUBSCRIPTION_PAYMENT
    assert packet.packet_hash.startswith("sha256:")
    assert packet.issuer.signature
    result = service.verify_receipt_packet(packet, registry)
    assert result.valid
    assert service.recompute_packet_hash(packet) == packet.packet_hash
    assert service.repository.get_by_idempotency_key(service._idempotency_key(receipt_type=packet.receipt_type, payment=packet.payment, subscription=packet.subscription, merchant=packet.merchant)) == packet


def test_valid_payregister_receipt_created(signed_service):
    service, registry = signed_service
    packet = service.create_payregister_receipt(payment=payment(), merchant=merchant(), policy=policy(), audit=audit(), network="bitcoin-mainnet", settled_at=datetime.now(UTC), payment_context=LNURLReceiptPaymentContext(safe_description="Coffee order"))
    assert packet.receipt_type == LNURLReceiptType.PAYREGISTER_SALE
    assert service.verify_receipt_packet(packet, registry).valid


def test_unsettled_payment_rejected_and_pending_explicitly_marked():
    service = LNURLReceiptPacketService(config=LNURLReceiptPacketConfig(signing_enabled=False))
    with pytest.raises(LNURLReceiptInvariantError):
        service.create_subscription_receipt(payment=payment(settled=False), subscription=subscription(), policy=policy(), audit=audit(), network="bitcoin-mainnet", settled_at=datetime.now(UTC))
    pending = service.create_pending_receipt(payment=payment(settled=False), policy=policy(), audit=audit(), network="bitcoin-mainnet")
    assert pending.issuer.unsigned
    assert not pending.payment.settled


def test_missing_payment_proof_subscription_entitlement_amount_and_network_rejected(signed_service):
    service, _registry = signed_service
    bad = payment().model_copy(update={"payment_proof_hash": ""})
    with pytest.raises(LNURLReceiptInvariantError):
        service.create_subscription_receipt(payment=bad, subscription=subscription(), policy=policy(), audit=audit(), network="bitcoin-mainnet", settled_at=datetime.now(UTC))
    with pytest.raises(LNURLReceiptInvariantError):
        service.create_subscription_receipt(payment=payment(), subscription=None, policy=policy(), audit=audit(), network="bitcoin-mainnet", settled_at=datetime.now(UTC))  # type: ignore[arg-type]
    mismatched_amount = payment().model_copy(update={"amount_sats": 1})
    with pytest.raises(LNURLReceiptInvariantError):
        service.create_subscription_receipt(payment=mismatched_amount, subscription=subscription(), policy=policy(), audit=audit(), network="bitcoin-mainnet", settled_at=datetime.now(UTC))
    with pytest.raises(LNURLReceiptInvariantError):
        service.create_subscription_receipt(payment=payment(network="bitcoin-testnet"), subscription=subscription(), policy=policy(), audit=audit(), network="bitcoin-testnet", settled_at=datetime.now(UTC))


def test_packet_tampering_invalid_signature_and_unknown_issuer_detected(signed_service):
    service, registry = signed_service
    packet = service.create_subscription_receipt(payment=payment(), subscription=subscription(), policy=policy(), audit=audit(), network="bitcoin-mainnet", settled_at=datetime.now(UTC))
    tampered = packet.model_copy(update={"payment": packet.payment.model_copy(update={"amount_msat": packet.payment.amount_msat + 1})})
    result = service.verify_receipt_packet(tampered, registry)
    assert not result.valid
    assert "packet_hash_mismatch" in result.errors
    bad_sig = packet.model_copy(update={"issuer": packet.issuer.model_copy(update={"signature": "bad"})})
    assert "issuer_signature_invalid" in service.verify_receipt_packet(bad_sig, registry).errors
    assert "unknown_issuer" in service.verify_receipt_packet(packet, LNURLReceiptIssuerKeyRegistry({})).errors


def test_duplicate_creation_is_idempotent(signed_service):
    service, _registry = signed_service
    kwargs = dict(payment=payment(), subscription=subscription(), policy=policy(), audit=audit(), network="bitcoin-mainnet", settled_at=datetime.now(UTC))
    first = service.create_subscription_receipt(**kwargs)
    second = service.create_subscription_receipt(**kwargs)
    assert first == second


def test_raw_secrets_excluded_and_forbidden_material_rejected(signed_service):
    service, _registry = signed_service
    packet = service.create_subscription_receipt(payment=payment(), subscription=subscription(), policy=policy(), audit=audit(), network="bitcoin-mainnet", settled_at=datetime.now(UTC), payment_context=LNURLReceiptPaymentContext(safe_description="Customer receipt"))
    customer = service.render_customer_view(packet).model_dump_json()
    public = service.render_public_redacted_view(packet).model_dump_json()
    for forbidden in ("raw", "access_pass", "session_token", "private_key", "payerdata_raw", "raw_comment", "principal_alias", "workspace_alias", "preimage_hash"):
        assert forbidden not in customer.lower()
        assert forbidden not in public.lower()
    with pytest.raises(LNURLReceiptInvariantError):
        service.create_subscription_receipt(payment=payment(), subscription=subscription(), policy=policy(), audit=audit(), network="bitcoin-mainnet", settled_at=datetime.now(UTC), payment_context=LNURLReceiptPaymentContext(safe_description="raw access pass leaked"))


def test_merchant_view_allows_operational_hashes_without_payer_data(signed_service):
    service, _registry = signed_service
    packet = service.create_payregister_receipt(payment=payment(), merchant=merchant(), policy=policy(), audit=audit(), network="bitcoin-mainnet", settled_at=datetime.now(UTC))
    view = service.render_merchant_view(packet)
    assert view.visibility == LNURLReceiptVisibility.MERCHANT
    assert view.terminal_alias == "hmac-sha256:terminal"
    assert "payer" not in view.model_dump_json().lower()


def test_testnet_receipt_visibly_separated_when_pending_manual_test_enabled():
    service = LNURLReceiptPacketService(config=LNURLReceiptPacketConfig(signing_enabled=False, allow_manual_test_settlement=True))
    pending = service.create_pending_receipt(payment=payment(settled=False, network="bitcoin-testnet"), policy=policy(), audit=audit(), network="bitcoin-testnet")
    assert pending.receipt_type == LNURLReceiptType.TESTNET_PAYMENT
