# ruff: noqa: E701,E702
"""Production-oriented LNURL-pay settlement verification service.

The verifier records settlement evidence only. It never creates Payment Proofs,
Subscription Entitlements, sessions, or access grants.
"""

from __future__ import annotations

import asyncio
import hashlib
import hmac
import json
from collections.abc import Iterable
from dataclasses import dataclass, replace
from datetime import UTC, datetime, timedelta
from typing import Any, Protocol

from app.services.access.audit_chain import AccessAuditChain
from app.services.access.crypto.hashing import canonical_json, sha256_prefixed
from app.services.lnurl.errors import (
    InvoiceMismatchError,
    LNURLVerifyError,
    PaymentAmountMismatchError,
    PaymentCanceledError,
    PaymentHashMismatchError,
    PaymentMetadataMismatchError,
    PaymentNetworkMismatchError,
    PaymentPreimageMismatchError,
    VerificationPolicyDeniedError,
    VerifyResponseMalformedError,
    VerifySourceUnavailableError,
    VerifyURLRejectedError,
)
from app.services.lnurl.url_safety import LNURLURLPolicy, validate_lnurl_url
from app.services.lnurl.verification_policy import LNURLVerificationPolicy
from app.services.lnurl.verification_sources import (
    Bolt11Decoder,
    LNURLSettlementState,
    LNURLVerificationConfidence,
    LNURLVerificationSourceType,
    ProjectBolt11Decoder,
    SettlementSourceResult,
    SettlementVerificationSource,
)


@dataclass(frozen=True, slots=True)
class LNURLVerifyConfig:
    enabled: bool = True
    allow_remote: bool = True
    require_trusted_origin: bool = True
    connect_timeout_seconds: float = 3
    read_timeout_seconds: float = 5
    total_timeout_seconds: float = 8
    max_response_bytes: int = 65536
    max_retries: int = 3
    initial_delay_seconds: int = 2
    pending_interval_seconds: int = 10
    max_attempts: int = 30
    expiry_grace_seconds: int = 60
    allow_manual_source: bool = False
    trusted_verify_domains: frozenset[str] = frozenset()


@dataclass(frozen=True, slots=True)
class LNURLPaymentForVerification:
    payment_id: str
    payment_request_id: str
    bolt11: str
    amount_msat: int
    payment_hash: str
    network: str
    invoice_hash: str | None = None
    metadata_hash: str | None = None
    provider_invoice_id_hash: str | None = None
    plan_code: str | None = None
    verify_url: str | None = None
    status: str = "invoice_issued"
    canceled: bool = False
    revoked: bool = False


@dataclass(frozen=True, slots=True)
class LNURLVerificationRecord:
    payment_id: str
    payment_request_id: str
    invoice_hash: str
    payment_hash: str
    source_type: str
    source_reference_hash: str | None
    status: str
    settled: bool
    confidence: str
    preimage_present: bool
    preimage_verified: bool
    preimage_hash: str | None
    response_fingerprint: str
    verification_attempt: int
    verified_at: datetime
    next_check_at: datetime | None = None
    error_code: str | None = None
    error_detail_redacted: str | None = None
    idempotency_key: str | None = None


@dataclass(frozen=True, slots=True)
class LNURLVerificationResult:
    payment_id: str
    invoice_hash: str
    status: str
    settled: bool
    verification_source: str
    confidence: str
    payment_hash_matches: bool
    amount_matches: bool
    network_matches: bool
    metadata_matches: bool
    preimage_present: bool
    preimage_verified: bool
    verified_at: datetime
    eligible_for_payment_proof: bool
    reason_code: str


class LNURLVerifyRepository(Protocol):
    def get_payment(self, payment_id: str) -> LNURLPaymentForVerification | None: ...
    def latest(self, payment_id: str) -> LNURLVerificationRecord | None: ...
    def save(self, record: LNURLVerificationRecord) -> LNURLVerificationRecord: ...
    def records(self, payment_id: str) -> tuple[LNURLVerificationRecord, ...]: ...
    def mark_payment_state(self, payment_id: str, state: str) -> None: ...
    def count_entitlements(self) -> int: ...
    def count_payment_proofs(self) -> int: ...


class InMemoryLNURLVerifyRepository:
    def __init__(self, payments: dict[str, LNURLPaymentForVerification] | None = None) -> None:
        self.payments = payments or {}
        self._records: dict[str, LNURLVerificationRecord] = {}
        self._by_payment: dict[str, list[LNURLVerificationRecord]] = {}
        self._lock = asyncio.Lock()
        self.entitlement_count = 0
        self.payment_proof_count = 0

    def get_payment(self, payment_id: str) -> LNURLPaymentForVerification | None:
        return self.payments.get(payment_id)

    def latest(self, payment_id: str) -> LNURLVerificationRecord | None:
        rs = self._by_payment.get(payment_id, [])
        return rs[-1] if rs else None

    def save(self, record: LNURLVerificationRecord) -> LNURLVerificationRecord:
        key = record.idempotency_key or record.response_fingerprint
        if key in self._records:
            return self._records[key]
        prev = self.latest(record.payment_id)
        if (
            prev
            and prev.status == LNURLSettlementState.SETTLED.value
            and record.status
            in {LNURLSettlementState.PENDING.value, LNURLSettlementState.EXPIRED.value}
        ):
            return prev
        self._records[key] = record
        self._by_payment.setdefault(record.payment_id, []).append(record)
        return record

    def records(self, payment_id: str) -> tuple[LNURLVerificationRecord, ...]:
        return tuple(self._by_payment.get(payment_id, ()))

    def mark_payment_state(self, payment_id: str, state: str) -> None:
        pass

    def count_entitlements(self) -> int:
        return self.entitlement_count

    def count_payment_proofs(self) -> int:
        return self.payment_proof_count


class LNURLVerifyService:
    def __init__(
        self,
        *,
        repository: LNURLVerifyRepository | None = None,
        sources: Iterable[SettlementVerificationSource] = (),
        policy: LNURLVerificationPolicy | None = None,
        config: LNURLVerifyConfig | None = None,
        decoder: Bolt11Decoder | None = None,
        audit_chain: AccessAuditChain | None = None,
        clock: Any | None = None,
    ) -> None:
        self.repository = repository or InMemoryLNURLVerifyRepository()
        self.sources = {s.source_type: s for s in sources}
        self.policy = policy or LNURLVerificationPolicy()
        self.config = config or LNURLVerifyConfig()
        self.decoder = decoder or ProjectBolt11Decoder()
        self.audit_chain = audit_chain
        self.clock = clock or (lambda: datetime.now(UTC))

    async def verify_payment(
        self, payment_id: str, force_refresh: bool = False
    ) -> LNURLVerificationResult:
        lock = getattr(self.repository, "_lock", None)
        if lock is not None:
            async with lock:
                return await self._verify_locked(payment_id, force_refresh)
        return await self._verify_locked(payment_id, force_refresh)

    async def _verify_locked(self, payment_id: str, force_refresh: bool) -> LNURLVerificationResult:
        payment = self.repository.get_payment(payment_id)
        if payment is None:
            raise LNURLVerifyError("payment_not_found", code="payment_not_found")  # noqa: F405
        latest = self.repository.latest(payment_id)
        if latest and latest.status == LNURLSettlementState.SETTLED.value and not force_refresh:
            return self._result_from_record(payment, latest, "settlement_verified")
        self._audit("lnurl_verify_started", payment, None, "started", "unverified", None)
        result = await self.reconcile_verification_sources(payment)
        rec = self.persist_verification_result(payment, result)
        return self._result_from_record(
            payment, rec, "settlement_verified" if rec.settled else rec.error_code or rec.status
        )

    async def reconcile_verification_sources(
        self, payment: LNURLPaymentForVerification
    ) -> SettlementSourceResult:
        ordered = [
            LNURLVerificationSourceType.INTERNAL_LIGHTNING_NODE,
            LNURLVerificationSourceType.TRUSTED_PAYMENT_PROVIDER,
            LNURLVerificationSourceType.BTCPAY,
            LNURLVerificationSourceType.LUD21_VERIFY_URL,
            LNURLVerificationSourceType.MANUAL_TEST_SOURCE,
        ]
        usable = [s for s in ordered if s in self.sources and self.policy.source_allowed(s)]
        if not usable:
            return SettlementSourceResult(
                LNURLVerificationSourceType.RECONCILIATION,
                False,
                LNURLSettlementState.VERIFICATION_UNAVAILABLE,
            )
        results = []
        for st in usable:
            try:
                results.append(await self._retry_source(self.sources[st], payment))
            except VerifySourceUnavailableError:
                results.append(
                    SettlementSourceResult(st, False, LNURLSettlementState.VERIFICATION_UNAVAILABLE)
                )  # noqa: F405
            except LNURLVerifyError:
                results.append(
                    SettlementSourceResult(st, False, LNURLSettlementState.VERIFICATION_UNAVAILABLE)
                )  # noqa: F405
        settled = [r for r in results if r.settled]
        authoritative = [
            r
            for r in results
            if r.source
            in {
                LNURLVerificationSourceType.INTERNAL_LIGHTNING_NODE,
                LNURLVerificationSourceType.TRUSTED_PAYMENT_PROVIDER,
                LNURLVerificationSourceType.BTCPAY,
            }
        ]
        if any(r.status == LNURLSettlementState.FAILED for r in authoritative):
            return authoritative[0]
        if (
            authoritative
            and settled
            and any(
                not r.settled
                and r.status
                not in {LNURLSettlementState.PENDING, LNURLSettlementState.VERIFICATION_UNAVAILABLE}
                for r in authoritative
            )
        ):
            return SettlementSourceResult(
                LNURLVerificationSourceType.RECONCILIATION, False, LNURLSettlementState.INCONSISTENT
            )
        if len(settled) >= 2:
            return replace(
                settled[0],
                source=LNURLVerificationSourceType.RECONCILIATION,
                confidence_hint=LNURLVerificationConfidence.DUAL_CONFIRMED,
            )
        return settled[0] if settled else results[0]

    async def _retry_source(
        self, source: SettlementVerificationSource, payment: LNURLPaymentForVerification
    ) -> SettlementSourceResult:
        last = None
        for attempt in range(1, self.config.max_retries + 1):
            try:
                return await source.verify(payment)
            except VerifySourceUnavailableError as exc:  # noqa: F405
                last = exc
                await asyncio.sleep(min(0.01 * attempt, 0.03))
        raise last or VerifySourceUnavailableError("source_unavailable")  # noqa: F405

    def validate_verify_response(
        self, payment: LNURLPaymentForVerification, response: SettlementSourceResult
    ) -> tuple[bool, bool, bool, bool, bool, str | None]:
        original = self.decoder.decode(payment.bolt11)
        returned = self.decoder.decode(response.invoice or payment.bolt11)
        invoice_match = response.invoice is None or hmac.compare_digest(
            response.invoice, payment.bolt11
        )
        payment_hash_matches = hmac.compare_digest(
            returned.payment_hash, original.payment_hash
        ) and hmac.compare_digest(
            original.payment_hash, payment.payment_hash.removeprefix("sha256:")
        )
        amount_matches = returned.amount_msat == original.amount_msat == payment.amount_msat
        network_matches = returned.network == original.network == payment.network
        metadata_matches = not payment.metadata_hash or returned.description_hash in {
            None,
            payment.metadata_hash,
        }
        if not invoice_match:
            raise InvoiceMismatchError("invoice_mismatch")  # noqa: F405
        if not payment_hash_matches:
            raise PaymentHashMismatchError("payment_hash_mismatch")  # noqa: F405
        if not amount_matches:
            raise PaymentAmountMismatchError("payment_amount_mismatch")  # noqa: F405
        if not network_matches:
            raise PaymentNetworkMismatchError("payment_network_mismatch")  # noqa: F405
        if not metadata_matches:
            raise PaymentMetadataMismatchError("payment_metadata_mismatch")  # noqa: F405
        preimage_verified = False
        ph = None
        if response.preimage:
            try:
                pre = bytes.fromhex(response.preimage)
            except ValueError:
                raise PaymentPreimageMismatchError("preimage_malformed")  # noqa: F405
            if len(pre) != 32:
                raise PaymentPreimageMismatchError("preimage_length")  # noqa: F405
            ph = hashlib.sha256(pre).hexdigest()
            if not hmac.compare_digest(ph, original.payment_hash):
                raise PaymentPreimageMismatchError("preimage_mismatch")  # noqa: F405
            preimage_verified = True
        return (
            payment_hash_matches,
            amount_matches,
            network_matches,
            metadata_matches,
            preimage_verified,
            (sha256_prefixed(bytes.fromhex(ph)) if ph else None),
        )

    def persist_verification_result(
        self, payment: LNURLPaymentForVerification, result: SettlementSourceResult
    ) -> LNURLVerificationRecord:
        latest_record = self.repository.latest(payment.payment_id)
        attempt = latest_record.verification_attempt + 1 if latest_record else 1
        now = self.clock()
        err = None
        preok = False
        prehash = None
        status = result.status
        settled = result.settled
        try:
            if payment.canceled or payment.revoked:
                raise PaymentCanceledError("payment_canceled")  # noqa: F405
            _, _, _, _, preok, prehash = self.validate_verify_response(payment, result)
        except LNURLVerifyError as exc:  # noqa: F405
            status = LNURLSettlementState.INCONSISTENT if exc.code.endswith("mismatch") else status
            settled = False
            err = exc.code
        conf = self._confidence(result, preok, status)
        eligible = (
            settled
            and status == LNURLSettlementState.SETTLED
            and self.policy.confidence_allowed(
                plan_code=payment.plan_code, confidence=conf, preimage_verified=preok
            )
        )
        if settled and not eligible:
            err = "verification_policy_denied"
        fp = sha256_prefixed(
            canonical_json(
                {
                    "source": result.source.value,
                    "status": status.value if hasattr(status, "value") else status,
                    "settled": settled,
                    "event": result.provider_event_id,
                    "invoice": sha256_prefixed(result.invoice or payment.bolt11),
                }
            )
        )
        rec = LNURLVerificationRecord(
            payment.payment_id,
            payment.payment_request_id,
            sha256_prefixed(payment.bolt11),
            payment.payment_hash,
            result.source.value,
            result.source_reference and sha256_prefixed(result.source_reference),
            status.value if hasattr(status, "value") else str(status),
            settled and eligible,
            conf.value,
            bool(result.preimage),
            preok,
            prehash,
            fp,
            attempt,
            now,
            (
                self.schedule_recheck_if_pending(payment.payment_id)
                if status == LNURLSettlementState.PENDING
                else None
            ),
            err,
            err,
            sha256_prefixed(payment.payment_id + fp + result.source.value),
        )
        saved = self.repository.save(rec)
        self._audit(
            f"lnurl_verify_{saved.status if saved.status!='verification_unavailable' else 'unavailable'}",
            payment,
            saved,
            saved.status,
            saved.confidence,
            err,
        )
        return saved

    def _confidence(
        self, result: SettlementSourceResult, preok: bool, status: LNURLSettlementState
    ) -> LNURLVerificationConfidence:
        if status == LNURLSettlementState.INCONSISTENT:
            return LNURLVerificationConfidence.INCONSISTENT
        if result.confidence_hint:
            return result.confidence_hint
        if result.source == LNURLVerificationSourceType.INTERNAL_LIGHTNING_NODE:
            return LNURLVerificationConfidence.INTERNALLY_CONFIRMED
        if result.source in {
            LNURLVerificationSourceType.TRUSTED_PAYMENT_PROVIDER,
            LNURLVerificationSourceType.BTCPAY,
        }:
            return LNURLVerificationConfidence.PROVIDER_CONFIRMED
        if result.source == LNURLVerificationSourceType.LUD21_VERIFY_URL and result.settled:
            return LNURLVerificationConfidence.REMOTE_ONLY
        return LNURLVerificationConfidence.UNVERIFIED

    def get_latest_verification(self, payment_id: str) -> LNURLVerificationRecord | None:
        return self.repository.latest(payment_id)

    def schedule_recheck_if_pending(self, payment_id: str) -> datetime:
        return self.clock() + timedelta(seconds=self.config.pending_interval_seconds)

    def mark_payment_inconsistent(self, payment_id: str, reason: str) -> None:
        p = self.repository.get_payment(payment_id)
        if p:
            self.repository.save(
                LNURLVerificationRecord(
                    payment_id,
                    p.payment_request_id,
                    sha256_prefixed(p.bolt11),
                    p.payment_hash,
                    LNURLVerificationSourceType.RECONCILIATION.value,
                    None,
                    LNURLSettlementState.INCONSISTENT.value,
                    False,
                    LNURLVerificationConfidence.INCONSISTENT.value,
                    False,
                    False,
                    None,
                    sha256_prefixed(reason),
                    1,
                    self.clock(),
                    None,
                    reason,
                    reason,
                    sha256_prefixed(payment_id + reason),
                )
            )

    def get_verified_settlement(self, payment_id: str) -> LNURLVerificationResult:
        p = self.repository.get_payment(payment_id)
        r = self.repository.latest(payment_id)
        if not p or not r or r.status != LNURLSettlementState.SETTLED.value or not r.settled:
            raise VerificationPolicyDeniedError("settlement_not_eligible")  # noqa: F405
        return self._result_from_record(p, r, "settlement_verified")

    def _result_from_record(
        self, p: LNURLPaymentForVerification, r: LNURLVerificationRecord, reason: str
    ) -> LNURLVerificationResult:
        return LNURLVerificationResult(
            p.payment_id,
            r.invoice_hash,
            r.status,
            r.settled,
            r.source_type,
            r.confidence,
            not r.error_code,
            not r.error_code,
            not r.error_code,
            not r.error_code,
            r.preimage_present,
            r.preimage_verified,
            r.verified_at,
            r.settled and r.status == LNURLSettlementState.SETTLED.value,
            reason,
        )

    def _audit(
        self,
        event: str,
        p: LNURLPaymentForVerification,
        r: LNURLVerificationRecord | None,
        status: str,
        confidence: str | LNURLVerificationConfidence | None,
        reason: str | None,
    ) -> None:
        if self.audit_chain:
            self.audit_chain.record_event(
                event_type=event,
                object_hash=sha256_prefixed(p.payment_id),
                metadata={
                    "payment_id_hash": sha256_prefixed(p.payment_id),
                    "invoice_hash": sha256_prefixed(p.bolt11),
                    "payment_hash_fingerprint": sha256_prefixed(p.payment_hash),
                    "source_type": r.source_type if r else None,
                    "result_status": status,
                    "confidence": str(confidence),
                    "reason_code": reason,
                    "attempt": r.verification_attempt if r else 0,
                    "verification_timestamp": self.clock().isoformat(),
                    "policy_hash": sha256_prefixed(str(self.policy)),
                },
            )


class LUD21VerificationSource:
    source_type = LNURLVerificationSourceType.LUD21_VERIFY_URL

    def __init__(self, *, fetch_json: Any, config: LNURLVerifyConfig | None = None) -> None:
        self.fetch_json = fetch_json
        self.config = config or LNURLVerifyConfig()

    async def verify(self, payment: LNURLPaymentForVerification) -> SettlementSourceResult:
        if not payment.verify_url:
            raise VerifySourceUnavailableError("verify_url_missing")  # noqa: F405
        policy = (
            LNURLURLPolicy.remote_fetch()
            if not self.config.trusted_verify_domains
            else LNURLURLPolicy.service_owned_callback(domains=self.config.trusted_verify_domains)
        )
        try:
            url = validate_lnurl_url(payment.verify_url, policy=policy)
        except Exception as exc:
            raise VerifyURLRejectedError("verify_url_rejected") from exc  # noqa: F405
        data = await self.fetch_json(url.normalized_url, self.config)
        if len(json.dumps(data).encode()) > self.config.max_response_bytes:
            raise VerifyResponseMalformedError("verify_response_oversized")  # noqa: F405
        if data.get("status") == "ERROR":
            return SettlementSourceResult(
                self.source_type,
                False,
                LNURLSettlementState.FAILED,
                diagnostics={"reason": str(data.get("reason", ""))[:160]},
            )
        if (
            data.get("status") != "OK"
            or not isinstance(data.get("settled"), bool)
            or "pr" not in data
        ):
            raise VerifyResponseMalformedError("verify_response_malformed")  # noqa: F405
        return SettlementSourceResult(
            self.source_type,
            bool(data["settled"]),
            LNURLSettlementState.SETTLED if data["settled"] else LNURLSettlementState.PENDING,
            invoice=data.get("pr"),
            preimage=data.get("preimage"),
        )
