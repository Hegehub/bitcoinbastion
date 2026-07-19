from __future__ import annotations

import asyncio
import base64
import hashlib
from datetime import UTC, datetime, timedelta

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from app.domain.lnurl.payment_proofs import LNURLPaymentContext, LNURLSettlementMethod
from app.schemas.lnurl_receipt import LNURLReceiptAuditContext, LNURLReceiptPaymentContext, LNURLReceiptPolicyContext, LNURLReceiptSettlementEvidence, LNURLReceiptSubscriptionContext
from app.services.lnurl.payment_proof import InMemoryLNURLPaymentProofRepository, LNURLPaymentProofConfig, LNURLPaymentProofService
from app.services.lnurl.receipt_packet import LNURLReceiptIssuerKeyRegistry, LNURLReceiptPacketConfig, LNURLReceiptPacketService
from app.services.lnurl.verification_sources import LNURLSettlementState, LNURLVerificationSourceType, SettlementSourceResult, test_bolt11 as make_test_bolt11
from app.services.lnurl.verify import InMemoryLNURLVerifyRepository, LNURLPaymentForVerification, LNURLVerifyService


class Source:
    source_type = LNURLVerificationSourceType.INTERNAL_LIGHTNING_NODE

    async def verify(self, payment):
        return SettlementSourceResult(self.source_type, True, LNURLSettlementState.SETTLED, invoice=payment.bolt11, preimage=("78" * 32))


def keys() -> tuple[str, str]:
    private = Ed25519PrivateKey.generate()
    raw_private = private.private_bytes(encoding=serialization.Encoding.Raw, format=serialization.PrivateFormat.Raw, encryption_algorithm=serialization.NoEncryption())
    raw_public = private.public_key().public_bytes(encoding=serialization.Encoding.Raw, format=serialization.PublicFormat.Raw)
    return base64.urlsafe_b64encode(raw_private).decode().rstrip("="), base64.urlsafe_b64encode(raw_public).decode().rstrip("=")


def test_lnurl_receipt_packet_end_to_end_flow():
    priv, pub = keys()
    amount_msat = 2_500_000
    invoice = make_test_bolt11(payment_hash=hashlib.sha256(b"x" * 32).hexdigest(), amount_msat=amount_msat, network="lightning-mainnet", timestamp=datetime.now(UTC), description_hash="sha256:metadata")
    payment = LNURLPaymentForVerification("payment-1", "lpay_request_1", invoice, amount_msat, hashlib.sha256(b"x" * 32).hexdigest(), "lightning-mainnet", metadata_hash="sha256:metadata", plan_code="pro_pass")
    verify_repo = InMemoryLNURLVerifyRepository({"payment-1": payment})
    verify_service = LNURLVerifyService(repository=verify_repo, sources=[Source()])
    asyncio.run(verify_service.verify_payment("payment-1"))
    proof_service = LNURLPaymentProofService(verification_service=verify_service, repository=InMemoryLNURLPaymentProofRepository(), config=LNURLPaymentProofConfig(issuer_private_key=priv, issuer_public_key=pub))
    proof = asyncio.run(proof_service.issue_payment_proof("payment-1", payment_context=LNURLPaymentContext.SUBSCRIPTION, product_code="pro_pass"))

    receipt_service = LNURLReceiptPacketService(config=LNURLReceiptPacketConfig(issuer_private_key=priv))
    settled_at = datetime.now(UTC)
    receipt = receipt_service.create_subscription_receipt(
        payment=LNURLReceiptSettlementEvidence(
            lnurl_pay_request_hash="sha256:req",
            lnurl_callback_hash=proof.lnurl_callback_hash,
            payment_proof_hash=proof.proof_fingerprint,
            payment_hash=proof.payment_hash,
            invoice_hash=proof.invoice_hash,
            amount_msat=proof.amount_msat,
            amount_sats=proof.amount_msat // 1000,
            currency=proof.currency,
            settlement_method=LNURLSettlementMethod.LNURL_VERIFY.value,
            settled=proof.settled,
            preimage_hash=proof.preimage_commitment,
            metadata_hash=proof.payment_metadata_hash,
        ),
        subscription=LNURLReceiptSubscriptionContext(plan_code="pro_pass", entitlement_hash="sha256:entitlement", entitlement_status="active", valid_from=settled_at, valid_until=settled_at + timedelta(days=30)),
        policy=LNURLReceiptPolicyContext(decision="allow", policy_hash="sha256:policy", policy_epoch=1, decision_event_hash="sha256:policy-event"),
        audit=LNURLReceiptAuditContext(payment_settled_event_hash="sha256:settled-event", payment_proof_event_hash=proof.audit_event_hash or "sha256:proof-event", entitlement_event_hash="sha256:entitlement-event", receipt_created_event_hash="sha256:receipt-event"),
        network="bitcoin-mainnet",
        settled_at=settled_at,
        payment_context=LNURLReceiptPaymentContext(product_code="pro_pass", safe_description="Bitcoin Bastion Pro Pass"),
    )
    verified = receipt_service.verify_receipt_packet(receipt, LNURLReceiptIssuerKeyRegistry({"bastion-lnurl-receipt-v1": pub}), expected_context={"subscription.plan_code": "pro_pass", "payment.amount_msat": amount_msat})
    assert verified.valid
    customer_view = receipt_service.render_customer_view(receipt).model_dump_json()
    assert "private_key" not in customer_view.lower()
    assert "preimage" not in customer_view.lower()
    assert receipt_service.create_subscription_receipt(payment=receipt.payment, subscription=receipt.subscription, policy=receipt.policy, audit=receipt.audit, network=receipt.network, settled_at=settled_at) == receipt
    tampered = receipt.model_copy(update={"subscription": receipt.subscription.model_copy(update={"entitlement_hash": "sha256:other"})})
    assert not receipt_service.verify_receipt_packet(tampered, LNURLReceiptIssuerKeyRegistry({"bastion-lnurl-receipt-v1": pub})).valid
