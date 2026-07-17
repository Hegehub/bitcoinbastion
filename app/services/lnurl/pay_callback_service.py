"""LNURL-pay callback invoice service.

This service handles the LNURL-pay callback stage only: it validates a stored
Bastion LNURL-pay request, validates the wallet-selected millisatoshi amount,
binds the invoice to canonical Prompt 29 metadata, calls a trusted Lightning
invoice provider, persists a normalized invoice association, and emits audit
evidence.

Invoice issuance is not settlement, not Payment Proof, not Subscription
Entitlement, not an Access Certificate, not a PoP session, and not API access.
"""

from __future__ import annotations

import asyncio
import hmac
from collections.abc import Mapping
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any, Callable, Protocol

from app.services.access.audit_chain import AccessAuditChain
from app.services.access.crypto.hashing import canonical_json, hash_canonical_json_prefixed, hmac_sha256_prefixed, sha256_prefixed
from app.services.lnurl.pay.errors import LNURLPayInvalidAmountError, LNURLPayMetadataError, LNURLPayRequestError
from app.services.lnurl.pay.subscription_request_service import LNURLPayRequestRecord, LNURLPayRequestStatus
from app.services.lnurl.pay_metadata import metadata_result_from_json

MAX_LNURL_PAY_CALLBACK_AMOUNT_MSAT = 21_000_000 * 100_000_000 * 1_000
MAX_PAYER_DATA_BYTES = 4_096
DEFAULT_INVOICE_TTL_SECONDS = 900
_FORBIDDEN_CALLBACK_KEY_PARTS = (
    "seed",
    "mnemonic",
    "xprv",
    "private_key",
    "wallet_seed",
    "bitcoin_seed",
    "session_token",
    "access_pass",
    "preimage",
    "provider_secret",
    "api_key",
)


class LNURLPayInvoiceStatus(StrEnum):
    INVOICE_ISSUED = "invoice_issued"


@dataclass(frozen=True, slots=True)
class LNURLPayCallbackCommand:
    request_id: str
    amount_msat: int
    comment: str | None = None
    payer_data: dict[str, Any] | None = None
    client_context: dict[str, Any] | None = None
    requested_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class LightningInvoiceResult:
    provider_invoice_id: str
    bolt11: str
    payment_hash: str
    expires_at: datetime
    provider_name: str
    verify_url: str | None = None
    raw_status: str | None = None


class LightningInvoiceProvider(Protocol):
    provider_name: str

    async def create_invoice(
        self,
        *,
        amount_msat: int,
        description_hash: str,
        expiry_seconds: int,
        idempotency_key: str,
        metadata: dict[str, Any],
    ) -> LightningInvoiceResult: ...


class UnconfiguredLightningInvoiceProvider:
    provider_name = "unconfigured"

    async def create_invoice(
        self,
        *,
        amount_msat: int,
        description_hash: str,
        expiry_seconds: int,
        idempotency_key: str,
        metadata: dict[str, Any],
    ) -> LightningInvoiceResult:
        raise LNURLInvoiceProviderUnavailable("No LNURL-pay Lightning invoice provider is configured")


@dataclass(frozen=True, slots=True)
class LNURLPayInvoiceRecord:
    request_id: str
    request_reference_hash: str
    invoice_reference: str
    invoice_reference_hash: str
    provider_invoice_id_hash: str
    provider_name: str
    amount_msat: int
    bolt11: str
    invoice_hash: str
    payment_hash: str
    metadata_hash: str
    idempotency_key_hash: str
    status: str
    issued_at: datetime
    expires_at: datetime
    principal_hash: str | None = None
    product_code: str | None = None
    plan_code: str | None = None
    verify_url: str | None = None
    verify_url_hash: str | None = None
    comment_hash: str | None = None
    payer_data_hash: str | None = None
    audit_event_hash: str | None = None


@dataclass(frozen=True, slots=True)
class LNURLPayInvoiceResult:
    request_id: str
    invoice_reference: str
    pr: str
    routes: tuple[Any, ...]
    success_action: dict[str, Any] | None
    verify_url: str | None
    disposable: bool
    expires_at: datetime
    payment_status: str
    amount_msat: int
    metadata_hash: str
    invoice_hash: str
    provider_name: str
    audit_event_hash: str | None = None

    def to_lnurl_response(self) -> dict[str, Any]:
        response: dict[str, Any] = {"pr": self.pr, "routes": list(self.routes), "disposable": self.disposable}
        if self.success_action is not None:
            response["successAction"] = self.success_action
        if self.verify_url is not None:
            response["verify"] = self.verify_url
        return response


class LNURLPayCallbackRepository(Protocol):
    def get_request(self, request_id: str) -> LNURLPayRequestRecord | None: ...

    def save_request(self, record: LNURLPayRequestRecord) -> None: ...

    def get_invoice_by_request_id(self, request_id: str) -> LNURLPayInvoiceRecord | None: ...

    def create_invoice(self, invoice: LNURLPayInvoiceRecord, request: LNURLPayRequestRecord) -> LNURLPayInvoiceRecord: ...

    def update_invoice_audit_hash(self, invoice_reference: str, audit_event_hash: str) -> None: ...

    def count_entitlements(self) -> int: ...

    def count_payment_proofs(self) -> int: ...

    def count_sessions(self) -> int: ...


class InMemoryLNURLPayCallbackRepository:
    def __init__(self, requests: dict[str, LNURLPayRequestRecord] | None = None) -> None:
        self.requests: dict[str, LNURLPayRequestRecord] = requests if requests is not None else {}
        self.invoices_by_request_id: dict[str, LNURLPayInvoiceRecord] = {}
        self.invoices_by_idempotency_hash: dict[str, LNURLPayInvoiceRecord] = {}
        self.entitlement_count = 0
        self.payment_proof_count = 0
        self.session_count = 0
        self._lock = asyncio.Lock()

    def get_request(self, request_id: str) -> LNURLPayRequestRecord | None:
        return self.requests.get(request_id)

    def save_request(self, record: LNURLPayRequestRecord) -> None:
        self.requests[record.request_id] = record

    def get_invoice_by_request_id(self, request_id: str) -> LNURLPayInvoiceRecord | None:
        return self.invoices_by_request_id.get(request_id)

    def create_invoice(self, invoice: LNURLPayInvoiceRecord, request: LNURLPayRequestRecord) -> LNURLPayInvoiceRecord:
        existing = self.invoices_by_request_id.get(invoice.request_id)
        if existing is not None:
            if existing.idempotency_key_hash == invoice.idempotency_key_hash:
                return existing
            raise LNURLInvoiceConflict("LNURL-pay callback conflicts with an existing invoice")
        if invoice.idempotency_key_hash in self.invoices_by_idempotency_hash:
            return self.invoices_by_idempotency_hash[invoice.idempotency_key_hash]
        self.invoices_by_request_id[invoice.request_id] = invoice
        self.invoices_by_idempotency_hash[invoice.idempotency_key_hash] = invoice
        self.requests[request.request_id] = request
        return invoice

    def update_invoice_audit_hash(self, invoice_reference: str, audit_event_hash: str) -> None:
        for request_id, invoice in list(self.invoices_by_request_id.items()):
            if invoice.invoice_reference == invoice_reference:
                updated = replace(invoice, audit_event_hash=audit_event_hash)
                self.invoices_by_request_id[request_id] = updated
                self.invoices_by_idempotency_hash[updated.idempotency_key_hash] = updated
                return

    def count_entitlements(self) -> int:
        return self.entitlement_count

    def count_payment_proofs(self) -> int:
        return self.payment_proof_count

    def count_sessions(self) -> int:
        return self.session_count


class LNURLPayRequestNotFound(LNURLPayRequestError):
    reason_code = "lnurl_pay_request_not_found"


class LNURLPayRequestExpired(LNURLPayRequestError):
    reason_code = "lnurl_pay_request_expired"


class LNURLPayRequestRevoked(LNURLPayRequestError):
    reason_code = "lnurl_pay_request_revoked"


class LNURLPayCommentNotAllowed(LNURLPayRequestError):
    reason_code = "lnurl_pay_comment_not_allowed"


class LNURLPayCommentTooLong(LNURLPayRequestError):
    reason_code = "lnurl_pay_comment_too_long"


class LNURLPayerDataInvalid(LNURLPayRequestError):
    reason_code = "lnurl_payer_data_invalid"


class LNURLPayMetadataMismatch(LNURLPayMetadataError):
    reason_code = "lnurl_pay_metadata_mismatch"


class LNURLInvoiceProviderUnavailable(LNURLPayRequestError):
    reason_code = "lnurl_invoice_provider_unavailable"


class LNURLInvoiceCreationFailed(LNURLPayRequestError):
    reason_code = "lnurl_invoice_creation_failed"


class LNURLInvoiceConflict(LNURLPayRequestError):
    reason_code = "lnurl_invoice_conflict"


class LNURLInvoiceAlreadyIssued(LNURLPayRequestError):
    reason_code = "lnurl_invoice_already_issued"


@dataclass(frozen=True, slots=True)
class LNURLPayCallbackConfig:
    invoice_ttl_seconds: int = DEFAULT_INVOICE_TTL_SECONDS
    invoice_idempotency_pepper: str = "dev-lnurl-pay-invoice-idempotency-pepper-change-me"
    invoice_reference_pepper: str = "dev-lnurl-pay-invoice-reference-pepper-change-me"
    max_payer_data_bytes: int = MAX_PAYER_DATA_BYTES


class LNURLPayCallbackService:
    def __init__(
        self,
        *,
        repository: LNURLPayCallbackRepository | None = None,
        invoice_provider: LightningInvoiceProvider | None = None,
        audit_chain: AccessAuditChain | None = None,
        config: LNURLPayCallbackConfig | None = None,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self.repository = repository or InMemoryLNURLPayCallbackRepository()
        self.invoice_provider = invoice_provider or UnconfiguredLightningInvoiceProvider()
        self.audit_chain = audit_chain
        self.config = config or LNURLPayCallbackConfig()
        self.clock = clock or (lambda: datetime.now(UTC))

    async def create_invoice(self, command: LNURLPayCallbackCommand) -> LNURLPayInvoiceResult:
        lock = getattr(self.repository, "_lock", None)
        if lock is not None:
            async with lock:
                return await self._create_invoice_locked(command)
        return await self._create_invoice_locked(command)

    async def _create_invoice_locked(self, command: LNURLPayCallbackCommand) -> LNURLPayInvoiceResult:
        self._reject_secret_material(command.client_context)
        amount_msat = self._validate_amount_type(command.amount_msat)
        request = self.repository.get_request(command.request_id)
        if request is None:
            raise LNURLPayRequestNotFound("LNURL-pay request could not be found")
        now = self._now(command.requested_at)
        if request.revoked_at is not None or request.status == LNURLPayRequestStatus.REVOKED:
            raise LNURLPayRequestRevoked("LNURL-pay request is revoked")
        self._validate_amount_against_request(request, amount_msat)
        comment_hash = self._validate_comment(request, command.comment)
        payer_data_hash = self._validate_payer_data(request, command.payer_data)
        metadata_hash = self._verify_metadata(request)
        idempotency_key = self._invoice_idempotency_key(
            request=request,
            amount_msat=amount_msat,
            metadata_hash=metadata_hash,
            comment_hash=comment_hash,
            payer_data_hash=payer_data_hash,
        )
        idempotency_key_hash = sha256_prefixed(idempotency_key)
        existing = self.repository.get_invoice_by_request_id(request.request_id)
        if existing is not None:
            return self._idempotent_existing_result(existing, amount_msat, metadata_hash, idempotency_key_hash)
        self._validate_request_state(request, now)
        expiry_seconds = self._invoice_expiry_seconds(request, now)
        provider_result = await self._create_provider_invoice(
            amount_msat=amount_msat,
            metadata_hash=metadata_hash,
            expiry_seconds=expiry_seconds,
            idempotency_key=idempotency_key,
            request=request,
        )
        self._validate_provider_result(provider_result, amount_msat, now)
        invoice_reference = self._invoice_reference(idempotency_key)
        invoice_record = LNURLPayInvoiceRecord(
            request_id=request.request_id,
            request_reference_hash=request.request_reference_hash,
            invoice_reference=invoice_reference,
            invoice_reference_hash=hmac_sha256_prefixed(self.config.invoice_reference_pepper, invoice_reference),
            provider_invoice_id_hash=sha256_prefixed(provider_result.provider_invoice_id),
            provider_name=provider_result.provider_name,
            amount_msat=amount_msat,
            bolt11=provider_result.bolt11,
            invoice_hash=sha256_prefixed(provider_result.bolt11),
            payment_hash=sha256_prefixed(provider_result.payment_hash),
            metadata_hash=metadata_hash,
            idempotency_key_hash=idempotency_key_hash,
            status=LNURLPayInvoiceStatus.INVOICE_ISSUED.value,
            issued_at=now,
            expires_at=provider_result.expires_at.astimezone(UTC),
            principal_hash=request.principal_hash,
            product_code=request.product_code,
            plan_code=request.plan_code,
            verify_url=provider_result.verify_url,
            verify_url_hash=sha256_prefixed(provider_result.verify_url) if provider_result.verify_url else None,
            comment_hash=comment_hash,
            payer_data_hash=payer_data_hash,
        )
        updated_request = replace(request, status=LNURLPayRequestStatus.INVOICE_ISSUED)
        persisted = self.repository.create_invoice(invoice_record, updated_request)
        audit_hash = self._audit_invoice_issued(persisted)
        if audit_hash:
            self.repository.update_invoice_audit_hash(persisted.invoice_reference, audit_hash)
            refreshed = self.repository.get_invoice_by_request_id(request.request_id)
            persisted = refreshed or persisted
        return self._result_from_invoice(persisted)

    async def reconcile_invoice(self, request_id: str) -> LNURLPayInvoiceRecord | None:
        """Return the locally persisted invoice association for future provider reconciliation."""

        return self.repository.get_invoice_by_request_id(request_id)

    def _validate_amount_type(self, amount_msat: int) -> int:
        if not isinstance(amount_msat, int) or isinstance(amount_msat, bool):
            raise LNURLPayInvalidAmountError("LNURL-pay callback amount must be integer millisatoshis")
        if amount_msat <= 0 or amount_msat > MAX_LNURL_PAY_CALLBACK_AMOUNT_MSAT:
            raise LNURLPayInvalidAmountError("LNURL-pay callback amount is outside supported bounds")
        return amount_msat

    def _validate_request_state(self, request: LNURLPayRequestRecord, now: datetime) -> None:
        if request.revoked_at is not None or request.status == LNURLPayRequestStatus.REVOKED:
            raise LNURLPayRequestRevoked("LNURL-pay request is revoked")
        if request.expires_at <= now or request.status == LNURLPayRequestStatus.EXPIRED:
            raise LNURLPayRequestExpired("LNURL-pay request is expired")
        if request.status not in {LNURLPayRequestStatus.CREATED, LNURLPayRequestStatus.PENDING_CALLBACK}:
            raise LNURLInvoiceAlreadyIssued("LNURL-pay request cannot issue a new invoice")

    def _validate_amount_against_request(self, request: LNURLPayRequestRecord, amount_msat: int) -> None:
        if amount_msat < request.min_amount_msat or amount_msat > request.max_amount_msat:
            raise LNURLPayInvalidAmountError("LNURL-pay callback amount is outside request range")
        if request.fixed_amount_msat is not None and amount_msat != request.fixed_amount_msat:
            raise LNURLPayInvalidAmountError("LNURL-pay fixed-price amount mismatch")
        if request.min_amount_msat == request.max_amount_msat and amount_msat != request.min_amount_msat:
            raise LNURLPayInvalidAmountError("LNURL-pay fixed-price amount mismatch")

    def _validate_comment(self, request: LNURLPayRequestRecord, comment: str | None) -> str | None:
        if comment is None or comment == "":
            return None
        if request.comment_allowed is None or request.comment_allowed <= 0:
            raise LNURLPayCommentNotAllowed("LNURL-pay comments are not allowed for this request")
        if not isinstance(comment, str):
            raise LNURLPayCommentNotAllowed("LNURL-pay comment is invalid")
        normalized = " ".join(comment.replace("\r", " ").replace("\n", " ").split())
        if len(normalized) > request.comment_allowed:
            raise LNURLPayCommentTooLong("LNURL-pay comment exceeds allowed length")
        if any(ord(ch) < 32 or ord(ch) == 127 for ch in normalized):
            raise LNURLPayCommentNotAllowed("LNURL-pay comment contains control characters")
        lowered = normalized.lower()
        if any(part in lowered for part in _FORBIDDEN_CALLBACK_KEY_PARTS) or any(claim in lowered for claim in ("grants access", "entitlement active", "payment settled")):
            raise LNURLPayCommentNotAllowed("LNURL-pay comment contains unsafe material")
        return sha256_prefixed(normalized)

    def _validate_payer_data(self, request: LNURLPayRequestRecord, payer_data: dict[str, Any] | None) -> str | None:
        if not payer_data:
            return None
        if not isinstance(payer_data, dict):
            raise LNURLPayerDataInvalid("LNURL-pay payerData must be an object")
        if request.payer_data_policy is None:
            raise LNURLPayerDataInvalid("LNURL-pay payerData was not declared for this request")
        allowed_fields = set(request.payer_data_policy)
        if not set(payer_data).issubset(allowed_fields):
            raise LNURLPayerDataInvalid("LNURL-pay payerData contains undeclared fields")
        serialized = canonical_json(payer_data)
        if len(serialized.encode("utf-8")) > self.config.max_payer_data_bytes:
            raise LNURLPayerDataInvalid("LNURL-pay payerData is too large")
        self._reject_secret_material(payer_data)
        return hash_canonical_json_prefixed(payer_data)

    def _verify_metadata(self, request: LNURLPayRequestRecord) -> str:
        recalculated = metadata_result_from_json(request.metadata).metadata_hash
        if not hmac.compare_digest(recalculated, request.metadata_hash):
            raise LNURLPayMetadataMismatch("LNURL-pay metadata hash mismatch")
        return recalculated

    def _invoice_idempotency_key(
        self,
        *,
        request: LNURLPayRequestRecord,
        amount_msat: int,
        metadata_hash: str,
        comment_hash: str | None,
        payer_data_hash: str | None,
    ) -> str:
        payload = canonical_json(
            {
                "request_id": request.request_id,
                "amount_msat": amount_msat,
                "metadata_hash": metadata_hash,
                "principal_hash": request.principal_hash,
                "payment_epoch": request.crypto_epoch,
                "comment_hash": comment_hash,
                "payer_data_hash": payer_data_hash,
            }
        )
        return hmac_sha256_prefixed(self.config.invoice_idempotency_pepper, payload)

    def _invoice_expiry_seconds(self, request: LNURLPayRequestRecord, now: datetime) -> int:
        remaining = int((request.expires_at - now).total_seconds())
        ttl = min(self.config.invoice_ttl_seconds, remaining)
        if ttl <= 0:
            raise LNURLPayRequestExpired("LNURL-pay request has no remaining invoice lifetime")
        return ttl

    async def _create_provider_invoice(
        self,
        *,
        amount_msat: int,
        metadata_hash: str,
        expiry_seconds: int,
        idempotency_key: str,
        request: LNURLPayRequestRecord,
    ) -> LightningInvoiceResult:
        try:
            return await self.invoice_provider.create_invoice(
                amount_msat=amount_msat,
                description_hash=metadata_hash,
                expiry_seconds=expiry_seconds,
                idempotency_key=idempotency_key,
                metadata={
                    "lnurl_pay_request_hash": request.request_reference_hash,
                    "metadata_hash": metadata_hash,
                    "product_code": request.product_code,
                    "plan_code": request.plan_code,
                    "principal_bound": request.principal_hash is not None,
                },
            )
        except LNURLPayRequestError:
            raise
        except Exception as exc:
            raise LNURLInvoiceCreationFailed("LNURL-pay invoice provider failed safely") from exc

    def _validate_provider_result(self, provider_result: LightningInvoiceResult, amount_msat: int, now: datetime) -> None:
        if not provider_result.bolt11 or not provider_result.payment_hash or not provider_result.provider_invoice_id:
            raise LNURLInvoiceCreationFailed("LNURL-pay invoice provider returned an invalid invoice")
        if provider_result.expires_at.tzinfo is None:
            raise LNURLInvoiceCreationFailed("LNURL-pay invoice expiry must be timezone-aware")
        if provider_result.expires_at.astimezone(UTC) <= now:
            raise LNURLInvoiceCreationFailed("LNURL-pay invoice provider returned an expired invoice")
        if amount_msat <= 0:
            raise LNURLInvoiceCreationFailed("LNURL-pay invoice amount is invalid")

    def _idempotent_existing_result(self, existing: LNURLPayInvoiceRecord, amount_msat: int, metadata_hash: str, idempotency_key_hash: str) -> LNURLPayInvoiceResult:
        if existing.amount_msat != amount_msat or existing.metadata_hash != metadata_hash or existing.idempotency_key_hash != idempotency_key_hash:
            raise LNURLInvoiceConflict("LNURL-pay callback conflicts with the already issued invoice")
        return self._result_from_invoice(existing)

    def _invoice_reference(self, idempotency_key: str) -> str:
        return hmac_sha256_prefixed(self.config.invoice_reference_pepper, idempotency_key)

    def _audit_invoice_issued(self, invoice: LNURLPayInvoiceRecord) -> str | None:
        if self.audit_chain is None:
            return None
        event = self.audit_chain.record_event(
            event_type="lnurl_invoice_issued",
            actor_hash=invoice.principal_hash,
            object_hash=invoice.request_reference_hash,
            metadata={
                "request_hash": invoice.request_reference_hash,
                "invoice_reference_hash": invoice.invoice_reference_hash,
                "amount_msat": invoice.amount_msat,
                "metadata_hash": invoice.metadata_hash,
                "provider_name": invoice.provider_name,
                "product_code": invoice.product_code,
                "plan_code": invoice.plan_code,
                "principal_hash": invoice.principal_hash,
                "expires_at": invoice.expires_at,
                "invoice_status": invoice.status,
            },
        )
        return str(event.event_hash)

    def _result_from_invoice(self, invoice: LNURLPayInvoiceRecord) -> LNURLPayInvoiceResult:
        return LNURLPayInvoiceResult(
            request_id=invoice.request_id,
            invoice_reference=invoice.invoice_reference,
            pr=invoice.bolt11,
            routes=(),
            success_action=None,
            verify_url=invoice.verify_url,
            disposable=True,
            expires_at=invoice.expires_at,
            payment_status=invoice.status,
            amount_msat=invoice.amount_msat,
            metadata_hash=invoice.metadata_hash,
            invoice_hash=invoice.invoice_hash,
            provider_name=invoice.provider_name,
            audit_event_hash=invoice.audit_event_hash,
        )

    def _reject_secret_material(self, values: Mapping[str, Any] | None) -> None:
        if not values:
            return
        for key, value in values.items():
            lowered_key = str(key).lower()
            if any(part in lowered_key for part in _FORBIDDEN_CALLBACK_KEY_PARTS):
                raise LNURLPayRequestError("LNURL-pay callback contains forbidden secret material")
            if isinstance(value, str):
                lowered_value = value.lower()
                if any(part in lowered_value for part in ("seed phrase", "private key", "mnemonic", "xprv", "preimage", "provider secret")):
                    raise LNURLPayRequestError("LNURL-pay callback contains forbidden secret material")
            elif isinstance(value, Mapping):
                self._reject_secret_material(value)

    def _now(self, requested_at: datetime | None = None) -> datetime:
        value = requested_at or self.clock()
        if value.tzinfo is None:
            value = value.replace(tzinfo=UTC)
        return value.astimezone(UTC)


__all__ = [
    "InMemoryLNURLPayCallbackRepository",
    "LNURLInvoiceAlreadyIssued",
    "LNURLInvoiceConflict",
    "LNURLInvoiceCreationFailed",
    "LNURLInvoiceProviderUnavailable",
    "LNURLPayCallbackCommand",
    "LNURLPayCallbackConfig",
    "LNURLPayCallbackRepository",
    "LNURLPayCallbackService",
    "LNURLPayCommentNotAllowed",
    "LNURLPayCommentTooLong",
    "LNURLPayInvoiceRecord",
    "LNURLPayInvoiceResult",
    "LNURLPayInvoiceStatus",
    "LNURLPayMetadataMismatch",
    "LNURLPayRequestExpired",
    "LNURLPayRequestNotFound",
    "LNURLPayRequestRevoked",
    "LNURLPayerDataInvalid",
    "LightningInvoiceProvider",
    "LightningInvoiceResult",
    "UnconfiguredLightningInvoiceProvider",
]
