"""LNURL Payment Proof issuance service.

This service transforms verified LNURL settlement evidence into immutable,
privacy-preserving Bastion Payment Proofs. It never issues Subscription
Entitlements, PoP sessions, Access Certificates, or protected access.
"""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from dataclasses import dataclass, replace
from datetime import UTC, datetime, timedelta
from typing import Any, Protocol

from app.domain.lnurl.payment_proofs import (
    LNURLIssuerSignature,
    LNURLPaymentContext,
    LNURLPaymentProof,
    LNURLPaymentProofStatus,
    LNURLPrincipalBindingMethod,
    LNURLSettlementMethod,
)
from app.services.access.audit_chain import AccessAuditChain
from app.services.access.crypto.hashing import canonical_json, hmac_sha256_prefixed, sha256_prefixed
from app.services.access.crypto.issuer_envelope import (
    BastionIssuedObjectType,
    build_classical_issuer_envelope,
)
from app.services.access.crypto.migration_policy import SignatureRequirementPolicy
from app.services.access.crypto.signatures import (
    Ed25519SignatureSuite,
    verify_lnurl_payment_proof_signature,
)
from app.services.lnurl.errors import (
    LNURLPaymentProofError,
    PaymentAmountMismatchError,
    PaymentBindingInvalidError,
    PaymentInvoiceMismatchError,
    PaymentProductMismatchError,
    PaymentProofIntegrityError,
    PaymentProofRevokedError,
    PaymentProofSigningError,
    SettlementEvidenceExpiredError,
    SettlementNotVerifiedError,
)
from app.services.lnurl.verification_sources import LNURLVerificationSourceType
from app.services.lnurl.verify import (
    LNURLPaymentForVerification,
    LNURLVerificationResult,
    LNURLVerifyService,
)

PROOF_TYPE = "bastion_lnurl_payment_proof"
PROOF_VERSION = 1
SAFE_CURRENCY = "BTC"


@dataclass(frozen=True, slots=True)
class LNURLPaymentProofConfig:
    enabled: bool = True
    issuer_key_id: str = "bastion-lnurl-proof-v1"
    issuer_private_key: str | None = None
    issuer_public_key: str | None = None
    issuer_pepper: str = "dev-lnurl-payment-proof-pepper-change-me"
    max_verification_age_seconds: int = 3600
    allow_test_settlement: bool = False
    require_policy: bool = True
    schema_epoch: int = 1
    crypto_epoch: int = 1
    policy_epoch: int = 1


@dataclass(frozen=True, slots=True)
class LNURLPrincipalBinding:
    method: LNURLPrincipalBindingMethod = LNURLPrincipalBindingMethod.UNBOUND_PAYMENT
    principal_hash: str | None = None
    principal_type: str | None = None
    verification_hash: str | None = None


@dataclass(frozen=True, slots=True)
class LNURLPaymentProofIssuedEvent:
    event_type: str
    proof_id: str
    proof_fingerprint: str
    payment_request_id: str
    principal_hash: str | None
    payment_context: str
    product_code: str
    amount_msat: int
    settled_at: datetime
    policy_epoch: int
    audit_event_hash: str | None

    def safe_payload(self) -> dict[str, Any]:
        return {
            "proof_id": self.proof_id,
            "proof_fingerprint": self.proof_fingerprint,
            "payment_request_id": self.payment_request_id,
            "principal_hash": self.principal_hash,
            "payment_context": self.payment_context,
            "product_code": self.product_code,
            "amount_msat": self.amount_msat,
            "settled_at": self.settled_at.isoformat().replace("+00:00", "Z"),
            "policy_epoch": self.policy_epoch,
            "audit_event_hash": self.audit_event_hash,
        }


class LNURLPaymentProofRepository(Protocol):
    def get_by_proof_id(self, proof_id: str) -> LNURLPaymentProof | None: ...
    def find_by_payment_request(self, payment_request_id: str) -> LNURLPaymentProof | None: ...
    def find_by_payment_hash(self, payment_hash: str) -> LNURLPaymentProof | None: ...
    def find_by_invoice_hash(self, invoice_hash: str) -> LNURLPaymentProof | None: ...
    def save(self, proof: LNURLPaymentProof) -> LNURLPaymentProof: ...
    def update(self, proof: LNURLPaymentProof) -> LNURLPaymentProof: ...
    def count_entitlements(self) -> int: ...


class InMemoryLNURLPaymentProofRepository:
    def __init__(self) -> None:
        self._by_proof_id: dict[str, LNURLPaymentProof] = {}
        self._by_payment_request: dict[str, LNURLPaymentProof] = {}
        self._by_payment_hash: dict[str, LNURLPaymentProof] = {}
        self._by_invoice_hash: dict[str, LNURLPaymentProof] = {}
        self._lock = asyncio.Lock()
        self.entitlement_count = 0

    def get_by_proof_id(self, proof_id: str) -> LNURLPaymentProof | None:
        return self._by_proof_id.get(proof_id)

    def find_by_payment_request(self, payment_request_id: str) -> LNURLPaymentProof | None:
        return self._by_payment_request.get(payment_request_id)

    def find_by_payment_hash(self, payment_hash: str) -> LNURLPaymentProof | None:
        return self._by_payment_hash.get(payment_hash)

    def find_by_invoice_hash(self, invoice_hash: str) -> LNURLPaymentProof | None:
        return self._by_invoice_hash.get(invoice_hash)

    def save(self, proof: LNURLPaymentProof) -> LNURLPaymentProof:
        existing = self.find_by_payment_request(proof.payment_request_id)
        if existing is not None:
            return existing
        for candidate in (
            self.find_by_payment_hash(proof.payment_hash),
            self.find_by_invoice_hash(proof.invoice_hash),
        ):
            if candidate is not None:
                return candidate
        self._by_proof_id[proof.proof_id] = proof
        self._by_payment_request[proof.payment_request_id] = proof
        self._by_payment_hash[proof.payment_hash] = proof
        self._by_invoice_hash[proof.invoice_hash] = proof
        return proof

    def update(self, proof: LNURLPaymentProof) -> LNURLPaymentProof:
        self._by_proof_id[proof.proof_id] = proof
        self._by_payment_request[proof.payment_request_id] = proof
        self._by_payment_hash[proof.payment_hash] = proof
        self._by_invoice_hash[proof.invoice_hash] = proof
        return proof

    def count_entitlements(self) -> int:
        return self.entitlement_count


class LNURLPaymentProofPolicy(Protocol):
    def decide(self, context: dict[str, Any]) -> tuple[bool, str]: ...


class AllowLNURLPaymentProofPolicy:
    def decide(self, context: dict[str, Any]) -> tuple[bool, str]:
        if context.get("settlement_method") == LNURLSettlementMethod.TEST_SETTLEMENT.value:
            return False, "test_settlement_not_allowed"
        return True, "allow"


class LNURLPaymentProofService:
    def __init__(
        self,
        *,
        verification_service: LNURLVerifyService,
        repository: LNURLPaymentProofRepository | None = None,
        config: LNURLPaymentProofConfig | None = None,
        audit_chain: AccessAuditChain | None = None,
        policy: LNURLPaymentProofPolicy | None = None,
        event_sink: Callable[[LNURLPaymentProofIssuedEvent], None] | None = None,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self.verification_service = verification_service
        self.repository = repository or InMemoryLNURLPaymentProofRepository()
        self.config = config or LNURLPaymentProofConfig()
        self.audit_chain = audit_chain
        self.policy = policy or AllowLNURLPaymentProofPolicy()
        self.event_sink = event_sink
        self.clock = clock or (lambda: datetime.now(UTC))
        self.signatures = Ed25519SignatureSuite()

    async def issue_payment_proof(
        self,
        payment_id: str,
        *,
        payment_context: LNURLPaymentContext | str,
        product_code: str,
        principal_binding: LNURLPrincipalBinding | None = None,
    ) -> LNURLPaymentProof:
        lock = getattr(self.repository, "_lock", None)
        if lock is not None:
            async with lock:
                return await self._issue_locked(
                    payment_id,
                    payment_context=payment_context,
                    product_code=product_code,
                    principal_binding=principal_binding,
                )
        return await self._issue_locked(
            payment_id,
            payment_context=payment_context,
            product_code=product_code,
            principal_binding=principal_binding,
        )

    async def _issue_locked(
        self,
        payment_id: str,
        *,
        payment_context: LNURLPaymentContext | str,
        product_code: str,
        principal_binding: LNURLPrincipalBinding | None,
    ) -> LNURLPaymentProof:
        payment = self._load_payment(payment_id)
        existing = self.repository.find_by_payment_request(payment.payment_request_id)
        if existing is not None:
            return existing
        try:
            verified = self.verification_service.get_verified_settlement(payment_id)
        except Exception as exc:
            raise SettlementNotVerifiedError("settlement_not_verified") from exc
        self._validate_verified_settlement(payment, verified, product_code=product_code)
        context = LNURLPaymentContext(payment_context)
        binding = self._validate_binding(principal_binding or LNURLPrincipalBinding())
        method = self._settlement_method(verified)
        self._validate_policy(payment, verified, context, method, binding)
        unsigned = {
            k: v
            for k, v in self._unsigned_payload(
                payment, verified, context, method, binding, product_code
            ).items()
            if v is not None
        }
        proof_fingerprint = sha256_prefixed(canonical_json(unsigned))
        proof_id = self._proof_id(proof_fingerprint)
        unsigned["proof_id"] = proof_id
        proof_fingerprint = sha256_prefixed(canonical_json(unsigned))
        signature = self._sign(unsigned)
        envelope = build_classical_issuer_envelope(
            unsigned,
            object_type=BastionIssuedObjectType.LNURL_PAYMENT_PROOF_RECEIPT,
            object_id_hash=sha256_prefixed(proof_id),
            object_fingerprint=proof_fingerprint,
            issuer_key_id=self.config.issuer_key_id,
            issuer_private_key=self.config.issuer_private_key or "",
            crypto_epoch=self.config.crypto_epoch,
            policy_epoch=self.config.policy_epoch,
            schema_epoch=self.config.schema_epoch,
            requirement=SignatureRequirementPolicy.CLASSICAL_REQUIRED_PQ_OPTIONAL,
        ).to_dict()
        proof = self._proof_from_payload(unsigned, proof_fingerprint, signature, envelope)
        audit_hash = self._audit_created(proof)
        if audit_hash:
            proof = replace(proof, audit_event_hash=audit_hash)
        saved = self.repository.save(proof)
        if saved.proof_id == proof.proof_id:
            self._emit_issued(saved)
        return saved

    def get_payment_proof(self, proof_id: str) -> LNURLPaymentProof | None:
        return self.repository.get_by_proof_id(proof_id)

    def find_by_payment_request(self, payment_request_id: str) -> LNURLPaymentProof | None:
        return self.repository.find_by_payment_request(payment_request_id)

    def verify_payment_proof_integrity(self, proof: LNURLPaymentProof) -> bool:
        if proof.status == LNURLPaymentProofStatus.REVOKED.value or proof.revoked_at is not None:
            raise PaymentProofRevokedError("payment_proof_revoked")
        payload = proof.unsigned_payload()
        if sha256_prefixed(canonical_json(payload)) != proof.proof_fingerprint:
            raise PaymentProofIntegrityError("proof_fingerprint_mismatch")
        if self.config.issuer_public_key:
            result = verify_lnurl_payment_proof_signature(
                payload, self.config.issuer_public_key, proof.issuer_signature.sig
            )
            if not result.valid:
                raise PaymentProofIntegrityError("proof_signature_invalid")
        return True

    def revoke_payment_proof(
        self, proof_id: str, *, reason: str, actor_hash: str | None = None
    ) -> LNURLPaymentProof:
        allowed = {
            "fraudulent_settlement",
            "provider_reversal",
            "duplicate_payment_mapping",
            "incorrect_product_binding",
            "compromised_issuer_key",
            "administrative_dispute",
            "test_data_cleanup",
        }
        if reason not in allowed:
            raise LNURLPaymentProofError(
                "invalid_revocation_reason", code="invalid_revocation_reason"
            )
        proof = self.repository.get_by_proof_id(proof_id)
        if proof is None:
            raise LNURLPaymentProofError("payment_proof_not_found", code="payment_proof_not_found")
        if proof.status == LNURLPaymentProofStatus.REVOKED.value:
            return proof
        revoked = replace(
            proof, status=LNURLPaymentProofStatus.REVOKED.value, revoked_at=self.clock()
        )
        self.repository.update(revoked)
        self._audit("lnurl_payment_proof_revoked", revoked, reason=reason, actor_hash=actor_hash)
        return revoked

    def create_receipt_reference(self, proof: LNURLPaymentProof) -> str:
        return (
            "brcpt_"
            + sha256_prefixed(proof.proof_fingerprint + proof.proof_id).split(":", 1)[1][:24]
        )

    def _load_payment(self, payment_id: str) -> LNURLPaymentForVerification:
        payment = self.verification_service.repository.get_payment(payment_id)
        if payment is None:
            raise SettlementNotVerifiedError("payment_request_not_found")
        return payment

    def _validate_verified_settlement(
        self,
        payment: LNURLPaymentForVerification,
        verified: LNURLVerificationResult,
        *,
        product_code: str,
    ) -> None:
        if (
            not verified.eligible_for_payment_proof
            or not verified.settled
            or verified.status != "settled"
        ):
            self._audit_failed(payment, "settlement_not_verified")
            raise SettlementNotVerifiedError("settlement_not_verified")
        latest = self.verification_service.get_latest_verification(payment.payment_id)
        if latest is None:
            raise SettlementNotVerifiedError("settlement_not_verified")
        if self.clock() - latest.verified_at > timedelta(
            seconds=self.config.max_verification_age_seconds
        ):
            raise SettlementEvidenceExpiredError("settlement_evidence_expired")
        if verified.invoice_hash != sha256_prefixed(payment.bolt11):
            raise PaymentInvoiceMismatchError("invoice_mismatch")
        if not verified.amount_matches:
            raise PaymentAmountMismatchError("amount_mismatch")
        if not verified.network_matches:
            raise PaymentInvoiceMismatchError("network_mismatch")
        if payment.plan_code and product_code != payment.plan_code:
            raise PaymentProductMismatchError("product_mismatch")

    def _validate_binding(self, binding: LNURLPrincipalBinding) -> LNURLPrincipalBinding:
        method = LNURLPrincipalBindingMethod(binding.method)
        if method is LNURLPrincipalBindingMethod.UNBOUND_PAYMENT:
            return replace(binding, method=method)
        if not binding.principal_hash or not binding.verification_hash:
            raise PaymentBindingInvalidError("principal_binding_not_verified")
        if method not in {
            LNURLPrincipalBindingMethod.EXISTING_POP_SESSION,
            LNURLPrincipalBindingMethod.VERIFIED_LNURL_AUTH,
            LNURLPrincipalBindingMethod.VERIFIED_PAYERDATA_AUTH,
            LNURLPrincipalBindingMethod.BUSINESS_WORKSPACE_CONTEXT,
            LNURLPrincipalBindingMethod.PAYREGISTER_TERMINAL_CONTEXT,
        }:
            raise PaymentBindingInvalidError("principal_binding_invalid")
        return replace(binding, method=method)

    def _validate_policy(
        self,
        payment: LNURLPaymentForVerification,
        verified: LNURLVerificationResult,
        context: LNURLPaymentContext,
        method: LNURLSettlementMethod,
        binding: LNURLPrincipalBinding,
    ) -> None:
        if (
            method is LNURLSettlementMethod.TEST_SETTLEMENT
            and not self.config.allow_test_settlement
        ):
            raise SettlementNotVerifiedError("test_settlement_not_allowed")
        allowed, reason = self.policy.decide(
            {
                "action": "lnurl_payment_proof_issue",
                "payment_context": context.value,
                "product_code": payment.plan_code,
                "amount_msat": payment.amount_msat,
                "settlement_method": method.value,
                "principal_binding_method": binding.method.value,
                "verification_age_seconds": 0,
                "payment_request_status": payment.status,
                "verification_source": verified.verification_source,
            }
        )
        if self.config.require_policy and not allowed:
            raise LNURLPaymentProofError(reason, code="policy_denied")

    def _settlement_method(self, verified: LNURLVerificationResult) -> LNURLSettlementMethod:
        source = verified.verification_source
        if source == LNURLVerificationSourceType.INTERNAL_LIGHTNING_NODE.value:
            return LNURLSettlementMethod.INTERNAL_LIGHTNING_NODE
        if source == LNURLVerificationSourceType.BTCPAY.value:
            return LNURLSettlementMethod.BTCPAY
        if source == LNURLVerificationSourceType.TRUSTED_PAYMENT_PROVIDER.value:
            return LNURLSettlementMethod.LIGHTNING_PROVIDER
        if source == LNURLVerificationSourceType.LUD21_VERIFY_URL.value:
            return LNURLSettlementMethod.LNURL_VERIFY
        if source == LNURLVerificationSourceType.MANUAL_TEST_SOURCE.value:
            return LNURLSettlementMethod.TEST_SETTLEMENT
        if verified.preimage_verified:
            return LNURLSettlementMethod.PREIMAGE_VERIFICATION
        return LNURLSettlementMethod.LNURL_VERIFY

    def _unsigned_payload(
        self,
        payment: LNURLPaymentForVerification,
        verified: LNURLVerificationResult,
        context: LNURLPaymentContext,
        method: LNURLSettlementMethod,
        binding: LNURLPrincipalBinding,
        product_code: str,
    ) -> dict[str, Any]:
        now = self.clock()
        latest = self.verification_service.get_latest_verification(payment.payment_id)
        return {
            "type": PROOF_TYPE,
            "version": PROOF_VERSION,
            "proof_id": "lpp_pending",
            "payment_request_id": payment.payment_request_id,
            "payment_hash": hmac_sha256_prefixed(self.config.issuer_pepper, payment.payment_hash),
            "invoice_hash": verified.invoice_hash,
            "lnurl_callback_hash": getattr(payment, "callback_hash", None)
            or sha256_prefixed(payment.payment_request_id),
            "verify_reference_hash": sha256_prefixed(
                latest.response_fingerprint if latest else verified.invoice_hash
            ),
            "principal_hash": binding.principal_hash,
            "principal_type": binding.principal_type,
            "binding_method": binding.method.value,
            "binding_verification_hash": binding.verification_hash,
            "payment_context": context.value,
            "product_code": product_code,
            "amount_msat": payment.amount_msat,
            "currency": SAFE_CURRENCY,
            "network": payment.network,
            "settled": True,
            "settlement_method": method.value,
            "settled_at": verified.verified_at.isoformat().replace("+00:00", "Z"),
            "verification_timestamp": verified.verified_at.isoformat().replace("+00:00", "Z"),
            "payment_metadata_hash": payment.metadata_hash
            or sha256_prefixed(payment.payment_request_id),
            "payer_data_hash": getattr(payment, "payer_data_hash", None),
            "preimage_commitment": (
                hmac_sha256_prefixed(self.config.issuer_pepper, latest.preimage_hash)
                if latest and latest.preimage_hash
                else None
            ),
            "issuer_key_id": self.config.issuer_key_id,
            "crypto_epoch": self.config.crypto_epoch,
            "schema_epoch": self.config.schema_epoch,
            "policy_epoch": self.config.policy_epoch,
            "created_at": now.isoformat().replace("+00:00", "Z"),
        }

    def _proof_id(self, proof_fingerprint: str) -> str:
        return "lpp_" + proof_fingerprint.split(":", 1)[1][:28]

    def _sign(self, payload: dict[str, Any]) -> LNURLIssuerSignature:
        if not self.config.issuer_private_key:
            raise PaymentProofSigningError("issuer_private_key_missing")
        try:
            sig = self.signatures.sign(
                payload,
                "lnurl_payment_proof",
                self.config.issuer_key_id,
                self.config.issuer_private_key,
                self.config.crypto_epoch,
            )
            return LNURLIssuerSignature(alg=sig.alg, key_id=sig.key_id, sig=sig.signature)
        except Exception as exc:  # noqa: BLE001
            raise PaymentProofSigningError("issuer_signing_failed") from exc

    def _proof_from_payload(
        self,
        payload: dict[str, Any],
        proof_fingerprint: str,
        signature: LNURLIssuerSignature,
        issuer_envelope: dict[str, Any],
    ) -> LNURLPaymentProof:
        return LNURLPaymentProof(
            type=payload["type"],
            version=payload["version"],
            proof_id=payload["proof_id"],
            payment_request_id=payload["payment_request_id"],
            payment_hash=payload["payment_hash"],
            invoice_hash=payload["invoice_hash"],
            lnurl_callback_hash=payload["lnurl_callback_hash"],
            verify_reference_hash=payload["verify_reference_hash"],
            principal_hash=payload.get("principal_hash"),
            principal_type=payload.get("principal_type"),
            binding_method=payload["binding_method"],
            binding_verification_hash=payload.get("binding_verification_hash"),
            payment_context=payload["payment_context"],
            product_code=payload["product_code"],
            amount_msat=payload["amount_msat"],
            currency=payload["currency"],
            network=payload["network"],
            settled=payload["settled"],
            settlement_method=payload["settlement_method"],
            settled_at=datetime.fromisoformat(payload["settled_at"].replace("Z", "+00:00")),
            verification_timestamp=datetime.fromisoformat(
                payload["verification_timestamp"].replace("Z", "+00:00")
            ),
            payment_metadata_hash=payload["payment_metadata_hash"],
            payer_data_hash=payload.get("payer_data_hash"),
            preimage_commitment=payload.get("preimage_commitment"),
            issuer_key_id=payload["issuer_key_id"],
            crypto_epoch=payload["crypto_epoch"],
            schema_epoch=payload["schema_epoch"],
            policy_epoch=payload["policy_epoch"],
            created_at=datetime.fromisoformat(payload["created_at"].replace("Z", "+00:00")),
            proof_fingerprint=proof_fingerprint,
            issuer_signature=signature,
            issuer_envelope=issuer_envelope,
        )

    def _audit_created(self, proof: LNURLPaymentProof) -> str | None:
        return self._audit("lnurl_payment_proof_created", proof)

    def _audit_failed(self, payment: LNURLPaymentForVerification, reason: str) -> None:
        if self.audit_chain:
            self.audit_chain.record_event(
                event_type="lnurl_payment_proof_failed",
                object_hash=sha256_prefixed(payment.payment_request_id),
                metadata={
                    "reason_code": reason,
                    "payment_request_id_hash": sha256_prefixed(payment.payment_request_id),
                },
            )

    def _audit(
        self,
        event_type: str,
        proof: LNURLPaymentProof,
        *,
        reason: str | None = None,
        actor_hash: str | None = None,
    ) -> str | None:
        if not self.audit_chain:
            return None
        event = self.audit_chain.record_event(
            event_type=event_type,
            actor_hash=actor_hash,
            object_hash=sha256_prefixed(proof.proof_id),
            metadata={
                "proof_id_hash": sha256_prefixed(proof.proof_id),
                "payment_request_id_hash": sha256_prefixed(proof.payment_request_id),
                "payment_hash": proof.payment_hash,
                "invoice_hash": proof.invoice_hash,
                "principal_hash": proof.principal_hash,
                "product_code": proof.product_code,
                "payment_context": proof.payment_context,
                "amount_msat": proof.amount_msat,
                "settlement_method": proof.settlement_method,
                "settled_at": proof.settled_at.isoformat().replace("+00:00", "Z"),
                "proof_fingerprint": proof.proof_fingerprint,
                "policy_epoch": proof.policy_epoch,
                "reason_code": reason,
            },
        )
        return getattr(event, "event_hash", None)

    def _emit_issued(self, proof: LNURLPaymentProof) -> None:
        if self.event_sink is None:
            return
        self.event_sink(
            LNURLPaymentProofIssuedEvent(
                "lnurl.payment_proof.issued",
                proof.proof_id,
                proof.proof_fingerprint,
                proof.payment_request_id,
                proof.principal_hash,
                proof.payment_context,
                proof.product_code,
                proof.amount_msat,
                proof.settled_at,
                proof.policy_epoch,
                proof.audit_event_hash,
            )
        )
