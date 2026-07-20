"""Tamper-evident LNURL Receipt Packet service.

The packet links LNURL-pay discovery/callback evidence, a verified settlement,
Bastion Payment Proof, entitlement or PayRegister context, policy decision, and
audit hashes. It is not an authentication credential or bearer entitlement.
"""
from __future__ import annotations

import secrets
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Protocol

from app.schemas.lnurl_receipt import (
    LNURLReceiptAuditContext,
    LNURLReceiptIssuerSignature,
    LNURLReceiptMerchantContext,
    LNURLReceiptPacket,
    LNURLReceiptPaymentContext,
    LNURLReceiptPolicyContext,
    LNURLReceiptPrincipalContext,
    LNURLReceiptPublicView,
    LNURLReceiptSettlementEvidence,
    LNURLReceiptSubscriptionContext,
    LNURLReceiptType,
    LNURLReceiptVerificationResult,
    LNURLReceiptVisibility,
)
from app.services.access.crypto.hashing import hash_canonical_json_prefixed, sha256_prefixed
from app.services.access.crypto.signatures import Ed25519SignatureSuite, IssuerSignature, SignatureSuiteRegistry

RECEIPT_SIGNING_CONTEXT = "lnurl_receipt_packet"
RECEIPT_PACKET_TYPE = "bastion_lnurl_receipt_packet"
_FORBIDDEN_PACKET_TERMS = (
    "raw access pass",
    "access_pass_",
    "raw_session",
    "session_token",
    "wallet_seed",
    "bitcoin_seed",
    "mnemonic",
    "private_key",
    "raw k1",
    "raw_preimage",
    "payerdata_raw",
    "raw_comment",
)


class LNURLReceiptPacketError(ValueError):
    reason_code = "lnurl_receipt_packet_error"


class LNURLReceiptInvariantError(LNURLReceiptPacketError):
    reason_code = "lnurl_receipt_invariant_failed"


class LNURLReceiptSignatureError(LNURLReceiptPacketError):
    reason_code = "lnurl_receipt_signature_failed"


@dataclass(frozen=True, slots=True)
class LNURLReceiptPacketConfig:
    signing_enabled: bool = True
    issuer_key_id: str = "bastion-lnurl-receipt-v1"
    issuer_private_key: str | None = None
    issuer_public_key: str | None = None
    schema_epoch: int = 1
    crypto_epoch: int = 1
    allow_manual_test_settlement: bool = False


class LNURLReceiptPacketRepository(Protocol):
    def get_by_idempotency_key(self, key: str) -> LNURLReceiptPacket | None: ...
    def save(self, key: str, packet: LNURLReceiptPacket) -> LNURLReceiptPacket: ...


class InMemoryLNURLReceiptPacketRepository:
    def __init__(self) -> None:
        self._packets: dict[str, LNURLReceiptPacket] = {}

    def get_by_idempotency_key(self, key: str) -> LNURLReceiptPacket | None:
        return self._packets.get(key)

    def save(self, key: str, packet: LNURLReceiptPacket) -> LNURLReceiptPacket:
        existing = self._packets.get(key)
        if existing is not None:
            return existing
        self._packets[key] = packet
        return packet


class LNURLReceiptAuditSink(Protocol):
    def emit(self, event_type: str, payload: dict[str, Any]) -> str: ...


class InMemoryLNURLReceiptAuditSink:
    def __init__(self) -> None:
        self.events: list[dict[str, Any]] = []

    def emit(self, event_type: str, payload: dict[str, Any]) -> str:
        safe_payload = {k: v for k, v in payload.items() if "raw" not in k and "secret" not in k and "token" not in k}
        event_hash = hash_canonical_json_prefixed({"event_type": event_type, **safe_payload, "index": len(self.events)})
        self.events.append({"event_type": event_type, "event_hash": event_hash, **safe_payload})
        return event_hash


@dataclass(frozen=True, slots=True)
class LNURLReceiptIssuerKeyRegistry:
    public_keys_by_key_id: Mapping[str, str | bytes]
    revoked_key_ids: frozenset[str] = frozenset()

    def get_public_key(self, key_id: str) -> str | bytes | None:
        return self.public_keys_by_key_id.get(key_id)

    def is_revoked(self, key_id: str) -> bool:
        return key_id in self.revoked_key_ids


class LNURLReceiptPacketService:
    def __init__(self, *, repository: LNURLReceiptPacketRepository | None = None, audit_sink: LNURLReceiptAuditSink | None = None, config: LNURLReceiptPacketConfig | None = None) -> None:
        self.repository = repository or InMemoryLNURLReceiptPacketRepository()
        self.audit_sink = audit_sink or InMemoryLNURLReceiptAuditSink()
        self.config = config or LNURLReceiptPacketConfig()
        self.signatures = Ed25519SignatureSuite()
        self.signature_registry = SignatureSuiteRegistry()

    def create_subscription_receipt(
        self,
        *,
        payment: LNURLReceiptSettlementEvidence,
        subscription: LNURLReceiptSubscriptionContext,
        policy: LNURLReceiptPolicyContext,
        audit: LNURLReceiptAuditContext,
        network: str,
        settled_at: datetime,
        payment_context: LNURLReceiptPaymentContext | None = None,
        principal: LNURLReceiptPrincipalContext | None = None,
    ) -> LNURLReceiptPacket:
        return self._create_receipt(
            receipt_type=LNURLReceiptType.SUBSCRIPTION_PAYMENT,
            payment=payment,
            subscription=subscription,
            merchant=None,
            policy=policy,
            audit=audit,
            network=network,
            settled_at=settled_at,
            payment_context=payment_context,
            principal=principal,
        )

    def create_payregister_receipt(
        self,
        *,
        payment: LNURLReceiptSettlementEvidence,
        merchant: LNURLReceiptMerchantContext,
        policy: LNURLReceiptPolicyContext,
        audit: LNURLReceiptAuditContext,
        network: str,
        settled_at: datetime,
        payment_context: LNURLReceiptPaymentContext | None = None,
    ) -> LNURLReceiptPacket:
        return self._create_receipt(
            receipt_type=LNURLReceiptType.PAYREGISTER_SALE,
            payment=payment,
            subscription=None,
            merchant=merchant,
            policy=policy,
            audit=audit,
            network=network,
            settled_at=settled_at,
            payment_context=payment_context,
            principal=None,
        )

    def create_lightning_address_receipt(
        self,
        *,
        payment: LNURLReceiptSettlementEvidence,
        policy: LNURLReceiptPolicyContext,
        audit: LNURLReceiptAuditContext,
        network: str,
        settled_at: datetime,
        payment_context: LNURLReceiptPaymentContext,
        merchant: LNURLReceiptMerchantContext | None = None,
    ) -> LNURLReceiptPacket:
        return self._create_receipt(
            receipt_type=LNURLReceiptType.MERCHANT_LIGHTNING_ADDRESS_PAYMENT,
            payment=payment,
            subscription=None,
            merchant=merchant,
            policy=policy,
            audit=audit,
            network=network,
            settled_at=settled_at,
            payment_context=payment_context,
            principal=None,
        )

    def create_pending_receipt(self, *, payment: LNURLReceiptSettlementEvidence, policy: LNURLReceiptPolicyContext, audit: LNURLReceiptAuditContext, network: str) -> LNURLReceiptPacket:
        if payment.settled:
            raise LNURLReceiptInvariantError("pending_receipt_requires_unsettled_payment")
        return self._assemble_packet(
            receipt_type=LNURLReceiptType.TESTNET_PAYMENT if "test" in network else LNURLReceiptType.CONTRIBUTION,
            payment=payment,
            subscription=None,
            merchant=None,
            policy=policy,
            audit=audit,
            network=network,
            settled_at=None,
            visibility=LNURLReceiptVisibility.PRIVATE,
        )

    def create_refund_reference_receipt(self, *, payment: LNURLReceiptSettlementEvidence, merchant: LNURLReceiptMerchantContext | None, policy: LNURLReceiptPolicyContext, audit: LNURLReceiptAuditContext, network: str, settled_at: datetime) -> LNURLReceiptPacket:
        return self._create_receipt(
            receipt_type=LNURLReceiptType.REFUND_REFERENCE,
            payment=payment,
            subscription=None,
            merchant=merchant,
            policy=policy,
            audit=audit,
            network=network,
            settled_at=settled_at,
            payment_context=None,
            principal=None,
        )

    def render_customer_view(self, packet: LNURLReceiptPacket) -> LNURLReceiptPublicView:
        return LNURLReceiptPublicView(
            receipt_id=packet.receipt_id,
            receipt_type=packet.receipt_type,
            visibility=LNURLReceiptVisibility.CUSTOMER,
            network=packet.network,
            amount_msat=packet.payment.amount_msat,
            amount_sats=packet.payment.amount_sats,
            currency=packet.payment.currency,
            settled=packet.payment.settled,
            settled_at=packet.settled_at,
            safe_description=packet.payment_context.safe_description if packet.payment_context else None,
            entitlement_status=packet.subscription.entitlement_status if packet.subscription else None,
            valid_until=packet.subscription.valid_until if packet.subscription else None,
            packet_hash=packet.packet_hash,
            issuer_key_id=packet.issuer.issuer_key_id,
        )

    def render_merchant_view(self, packet: LNURLReceiptPacket) -> LNURLReceiptPublicView:
        view = self.render_customer_view(packet).model_copy(update={"visibility": LNURLReceiptVisibility.MERCHANT})
        if packet.merchant is not None:
            view = view.model_copy(update={"order_reference_hash": packet.merchant.order_reference_hash, "terminal_alias": packet.merchant.terminal_alias, "shift_alias": packet.merchant.shift_alias, "policy_decision": packet.policy.decision, "audit_reference": packet.audit.receipt_created_event_hash})
        return view

    def render_public_redacted_view(self, packet: LNURLReceiptPacket) -> LNURLReceiptPublicView:
        return LNURLReceiptPublicView(
            receipt_id=packet.receipt_id,
            receipt_type=packet.receipt_type,
            visibility=LNURLReceiptVisibility.PUBLIC_REDACTED,
            network=packet.network,
            amount_msat=packet.payment.amount_msat,
            amount_sats=packet.payment.amount_sats,
            currency=packet.payment.currency,
            settled=packet.payment.settled,
            settled_at=packet.settled_at,
            safe_description=packet.payment_context.safe_description if packet.payment_context else None,
            packet_hash=packet.packet_hash,
            issuer_key_id=packet.issuer.issuer_key_id,
        )

    def verify_receipt_packet(self, packet: LNURLReceiptPacket, issuer_key_registry: LNURLReceiptIssuerKeyRegistry | None = None, expected_context: dict[str, Any] | None = None) -> LNURLReceiptVerificationResult:
        errors: list[str] = []
        warnings: list[str] = []
        packet_hash_valid = self.recompute_packet_hash(packet) == packet.packet_hash
        if not packet_hash_valid:
            errors.append("packet_hash_mismatch")
        settlement_valid = packet.payment.settled and bool(packet.payment.payment_proof_hash and packet.payment.invoice_hash and packet.payment.metadata_hash)
        if not settlement_valid:
            errors.append("settlement_evidence_invalid")
        context_consistent = True
        if expected_context:
            for key, expected in expected_context.items():
                actual = _nested_get(packet.model_dump(mode="json"), key)
                if actual != expected:
                    context_consistent = False
                    errors.append(f"context_mismatch:{key}")
        issuer_signature_valid = False
        if packet.issuer.unsigned:
            warnings.append("unsigned_packet")
            if packet.visibility == LNURLReceiptVisibility.ENTERPRISE_EVIDENCE:
                errors.append("unsigned_enterprise_evidence")
        elif issuer_key_registry is None:
            errors.append("issuer_registry_missing")
        elif issuer_key_registry.is_revoked(packet.issuer.issuer_key_id):
            errors.append("issuer_key_revoked")
        else:
            public_key = issuer_key_registry.get_public_key(packet.issuer.issuer_key_id)
            if public_key is None:
                errors.append("unknown_issuer")
            else:
                result = self.signature_registry.get(packet.issuer.signature_suite).verify(
                    self._signature_payload(packet), RECEIPT_SIGNING_CONTEXT, public_key, packet.issuer.signature or ""
                )
                issuer_signature_valid = result.valid
                if not result.valid:
                    errors.append("issuer_signature_invalid")
        valid = packet_hash_valid and settlement_valid and context_consistent and (issuer_signature_valid or packet.issuer.unsigned) and not errors
        return LNURLReceiptVerificationResult(
            valid=valid,
            packet_hash_valid=packet_hash_valid,
            issuer_signature_valid=issuer_signature_valid,
            settlement_evidence_valid=settlement_valid,
            context_consistent=context_consistent,
            warnings=warnings,
            errors=errors,
        )

    def recompute_packet_hash(self, packet: LNURLReceiptPacket) -> str:
        return hash_canonical_json_prefixed(self._unsigned_core(packet))

    def validate_receipt_invariants(self, packet: LNURLReceiptPacket) -> None:
        _reject_forbidden_packet_material(packet.model_dump(mode="json"))
        if packet.receipt_type != LNURLReceiptType.REFUND_REFERENCE and not packet.payment.settled:
            raise LNURLReceiptInvariantError("completed_receipt_requires_settlement")
        if packet.payment.amount_msat <= 0 or packet.payment.amount_sats != packet.payment.amount_msat // 1000:
            raise LNURLReceiptInvariantError("amount_mismatch")
        if not packet.payment.payment_proof_hash:
            raise LNURLReceiptInvariantError("payment_proof_required")
        if not packet.payment.invoice_hash or not packet.payment.metadata_hash:
            raise LNURLReceiptInvariantError("invoice_and_metadata_hash_required")
        if packet.receipt_type == LNURLReceiptType.SUBSCRIPTION_PAYMENT and packet.subscription is None:
            raise LNURLReceiptInvariantError("subscription_entitlement_required")
        if packet.subscription is not None and not packet.subscription.entitlement_hash:
            raise LNURLReceiptInvariantError("entitlement_hash_required")
        if packet.receipt_type in {LNURLReceiptType.PAYREGISTER_SALE, LNURLReceiptType.PAYREGISTER_INVOICE} and packet.merchant is None:
            raise LNURLReceiptInvariantError("merchant_context_required")
        if packet.payment.settlement_method == "manual_test_settlement" and not self.config.allow_manual_test_settlement:
            raise LNURLReceiptInvariantError("manual_test_settlement_disabled")
        if "test" in packet.network and packet.receipt_type != LNURLReceiptType.TESTNET_PAYMENT:
            raise LNURLReceiptInvariantError("test_network_receipt_must_be_marked")

    def _create_receipt(self, *, receipt_type: LNURLReceiptType, payment: LNURLReceiptSettlementEvidence, subscription: LNURLReceiptSubscriptionContext | None, merchant: LNURLReceiptMerchantContext | None, policy: LNURLReceiptPolicyContext, audit: LNURLReceiptAuditContext, network: str, settled_at: datetime, payment_context: LNURLReceiptPaymentContext | None, principal: LNURLReceiptPrincipalContext | None) -> LNURLReceiptPacket:
        if not payment.settled:
            raise LNURLReceiptInvariantError("completed_receipt_requires_settlement")
        _reject_forbidden_packet_material(
            {
                "payment": payment.model_dump(mode="json"),
                "subscription": subscription.model_dump(mode="json") if subscription else None,
                "merchant": merchant.model_dump(mode="json") if merchant else None,
                "payment_context": payment_context.model_dump(mode="json") if payment_context else None,
                "principal": principal.model_dump(mode="json") if principal else None,
            }
        )
        key = self._idempotency_key(receipt_type=receipt_type, payment=payment, subscription=subscription, merchant=merchant)
        existing = self.repository.get_by_idempotency_key(key)
        if existing is not None:
            return existing
        packet = self._assemble_packet(
            receipt_type=receipt_type,
            payment=payment,
            subscription=subscription,
            merchant=merchant,
            policy=policy,
            audit=audit,
            network=network,
            settled_at=settled_at,
            payment_context=payment_context,
            principal=principal,
            visibility=LNURLReceiptVisibility.PRIVATE,
        )
        self.validate_receipt_invariants(packet)
        self.audit_sink.emit("lnurl_receipt_packet_created", {"receipt_id_hash": sha256_prefixed(packet.receipt_id), "packet_hash": packet.packet_hash, "payment_proof_hash": payment.payment_proof_hash, "policy_hash": policy.policy_hash, "issuer_key_id": packet.issuer.issuer_key_id})
        return self.repository.save(key, packet)

    def _assemble_packet(self, *, receipt_type: LNURLReceiptType, payment: LNURLReceiptSettlementEvidence, subscription: LNURLReceiptSubscriptionContext | None, merchant: LNURLReceiptMerchantContext | None, policy: LNURLReceiptPolicyContext, audit: LNURLReceiptAuditContext, network: str, settled_at: datetime | None, visibility: LNURLReceiptVisibility, payment_context: LNURLReceiptPaymentContext | None = None, principal: LNURLReceiptPrincipalContext | None = None) -> LNURLReceiptPacket:
        created_at = datetime.now(UTC)
        unsigned = LNURLReceiptIssuerSignature(issuer_key_id=self.config.issuer_key_id, signature_suite="ed25519", unsigned=not self.config.signing_enabled, crypto_epoch=self.config.crypto_epoch)
        provisional = LNURLReceiptPacket(
            receipt_id=f"lnrcpt_{secrets.token_urlsafe(18)}",
            receipt_type=receipt_type,
            visibility=visibility,
            network=network,
            schema_epoch=self.config.schema_epoch,
            crypto_epoch=self.config.crypto_epoch,
            created_at=created_at,
            settled_at=settled_at,
            payment=payment,
            payment_context=payment_context,
            subscription=subscription,
            principal=principal,
            merchant=merchant,
            policy=policy,
            audit=audit,
            issuer=unsigned,
            packet_hash="sha256:pending",
        )
        packet_hash = hash_canonical_json_prefixed(self._unsigned_core(provisional))
        issuer = self._sign(provisional.model_copy(update={"packet_hash": packet_hash}))
        return provisional.model_copy(update={"packet_hash": packet_hash, "issuer": issuer})

    def _sign(self, packet: LNURLReceiptPacket) -> LNURLReceiptIssuerSignature:
        if not self.config.signing_enabled:
            return packet.issuer.model_copy(update={"unsigned": True, "signature": None})
        if self.config.issuer_private_key is None:
            raise LNURLReceiptSignatureError("issuer_private_key_required")
        sig: IssuerSignature = self.signatures.sign(self._signature_payload(packet), RECEIPT_SIGNING_CONTEXT, self.config.issuer_key_id, self.config.issuer_private_key, self.config.crypto_epoch)
        return LNURLReceiptIssuerSignature(issuer_key_id=sig.key_id, signature_suite=sig.alg, signature=sig.signature, crypto_epoch=sig.crypto_epoch, public_key_fingerprint=sig.public_key_fingerprint, unsigned=False)

    def _signature_payload(self, packet: LNURLReceiptPacket) -> dict[str, Any]:
        return {"packet_hash": packet.packet_hash, "receipt_id": packet.receipt_id, "type": packet.type, "version": packet.version}

    def _unsigned_core(self, packet: LNURLReceiptPacket) -> dict[str, Any]:
        data = packet.model_dump(mode="json", exclude_none=True)
        data.pop("packet_hash", None)
        data.pop("issuer", None)
        return data

    def _idempotency_key(self, *, receipt_type: LNURLReceiptType, payment: LNURLReceiptSettlementEvidence, subscription: LNURLReceiptSubscriptionContext | None, merchant: LNURLReceiptMerchantContext | None) -> str:
        return hash_canonical_json_prefixed({"receipt_type": receipt_type.value, "payment_proof_hash": payment.payment_proof_hash, "entitlement_hash": subscription.entitlement_hash if subscription else None, "merchant_order_hash": merchant.order_reference_hash if merchant else None, "schema_epoch": self.config.schema_epoch})


def _reject_forbidden_packet_material(value: Any) -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            lowered_key = str(key).lower()
            if any(term in lowered_key for term in ("raw_access_pass", "raw_session_token", "wallet_seed", "bitcoin_seed", "private_key", "raw_k1", "raw_preimage", "raw_payerdata", "raw_comment")):
                raise LNURLReceiptInvariantError("forbidden_secret_field")
            _reject_forbidden_packet_material(item)
    elif isinstance(value, list | tuple):
        for item in value:
            _reject_forbidden_packet_material(item)
    elif isinstance(value, str):
        lowered = value.lower()
        if any(term in lowered for term in _FORBIDDEN_PACKET_TERMS):
            raise LNURLReceiptInvariantError("forbidden_secret_value")


def _nested_get(data: dict[str, Any], dotted_key: str) -> Any:
    cursor: Any = data
    for part in dotted_key.split("."):
        if not isinstance(cursor, dict):
            return None
        cursor = cursor.get(part)
    return cursor


__all__ = [
    "InMemoryLNURLReceiptAuditSink",
    "InMemoryLNURLReceiptPacketRepository",
    "LNURLReceiptInvariantError",
    "LNURLReceiptIssuerKeyRegistry",
    "LNURLReceiptPacketConfig",
    "LNURLReceiptPacketError",
    "LNURLReceiptPacketService",
    "LNURLReceiptSignatureError",
]
