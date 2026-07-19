"""LNURL post-payment activation status and completion service."""

from __future__ import annotations

from dataclasses import dataclass
from inspect import isawaitable
from datetime import UTC, datetime
from typing import Any, Protocol

from app.db.repositories.lnurl_success_action_repository import LNURLSuccessActionRecord, LNURLSuccessActionRepository
from app.domain.lnurl.success_actions import LNURLActivationPurpose, LNURLActivationStatus, LNURLSuccessActionType
from app.schemas.lnurl_success_action import LNURLActivationStatusResponse
from app.services.access.crypto.hashing import sha256_prefixed
from app.services.lnurl.success_action import LNURLSuccessActionConfig, LNURLSuccessActionMetrics, LNURLSuccessActionService

_SUBSCRIPTION_PURPOSES = {
    LNURLActivationPurpose.SUBSCRIPTION_ACTIVATION,
    LNURLActivationPurpose.SUBSCRIPTION_RENEWAL,
    LNURLActivationPurpose.SUBSCRIPTION_UPGRADE,
    LNURLActivationPurpose.VAULT_SETUP,
    LNURLActivationPurpose.ACCESS_CERTIFICATE_SETUP,
    LNURLActivationPurpose.BUSINESS_ONBOARDING,
    LNURLActivationPurpose.ENTERPRISE_ONBOARDING,
}
_RECEIPT_PURPOSES = {
    LNURLActivationPurpose.PAYMENT_RECEIPT,
    LNURLActivationPurpose.CONTRIBUTION_RECEIPT,
    LNURLActivationPurpose.PAYREGISTER_RECEIPT,
    LNURLActivationPurpose.MERCHANT_RECEIPT,
}


class ActivationPolicyEngine(Protocol):
    def decide(self, action: str, context: dict[str, Any]) -> Any: ...


@dataclass(frozen=True, slots=True)
class ActivationDependencyState:
    payment_settled: bool = False
    payment_proof_exists: bool = False
    entitlement_active: bool = False
    payment_refunded: bool = False
    entitlement_revoked: bool = False
    payment_proof_id: str | None = None
    entitlement_id: str | None = None
    reason_code: str | None = None


class InMemoryActivationStateProvider:
    def __init__(self) -> None:
        self._states: dict[str, ActivationDependencyState] = {}

    def set_state(self, payment_request_id: str, state: ActivationDependencyState) -> None:
        self._states[payment_request_id] = state

    async def get_state(self, record: LNURLSuccessActionRecord) -> ActivationDependencyState:
        state = self._states.get(record.payment_request_id)
        if state is not None:
            return state
        return ActivationDependencyState(
            payment_settled=record.payment_proof_id is not None,
            payment_proof_exists=record.payment_proof_id is not None,
            entitlement_active=record.entitlement_id is not None,
            payment_proof_id=record.payment_proof_id,
            entitlement_id=record.entitlement_id,
        )


class LNURLActivationService:
    """Consumes verification/proof/entitlement state; never creates sessions or entitlements."""

    def __init__(
        self,
        *,
        success_action_service: LNURLSuccessActionService | None = None,
        state_provider: InMemoryActivationStateProvider | None = None,
        policy_engine: ActivationPolicyEngine | None = None,
        audit_chain: Any | None = None,
        metrics: LNURLSuccessActionMetrics | None = None,
    ) -> None:
        self.success_action_service = success_action_service or LNURLSuccessActionService()
        self.repository: LNURLSuccessActionRepository = self.success_action_service.repository
        self.state_provider = state_provider or InMemoryActivationStateProvider()
        self.policy_engine = policy_engine
        self.audit_chain = audit_chain or self.success_action_service.audit_chain
        self.metrics = metrics or self.success_action_service.metrics

    async def create_activation(
        self,
        *,
        payment_request_id: str,
        purpose: LNURLActivationPurpose,
        callback_origin: str,
        expected_entitlement_id: str | None = None,
        wallet_principal_hash: str | None = None,
        lightning_principal_hash: str | None = None,
        payregister_context_hash: str | None = None,
        merchant_context_hash: str | None = None,
        ttl_seconds: int | None = None,
    ) -> tuple[LNURLSuccessActionRecord, str]:
        if not payment_request_id:
            raise ValueError("payment_request_required")
        return await self.success_action_service.create_activation_record(
            payment_request_id=payment_request_id,
            purpose=purpose,
            callback_origin=callback_origin,
            action_type=LNURLSuccessActionType.URL,
            entitlement_id=expected_entitlement_id,
            wallet_principal_hash=wallet_principal_hash,
            lightning_principal_hash=lightning_principal_hash,
            payregister_context_hash=payregister_context_hash,
            merchant_context_hash=merchant_context_hash,
            ttl_seconds=ttl_seconds,
        )

    async def get_activation_status(self, activation_reference: str) -> LNURLActivationStatusResponse:
        record = await self._lookup_generic(activation_reference)
        record = await self._refresh_status(record)
        return self._response(record)

    async def open_activation(self, activation_reference: str) -> LNURLActivationStatusResponse:
        record = await self._lookup_generic(activation_reference)
        record = await self._refresh_status(record)
        if record.status not in {LNURLActivationStatus.COMPLETED, LNURLActivationStatus.EXPIRED, LNURLActivationStatus.REVOKED, LNURLActivationStatus.REFUNDED}:
            record = await self.repository.mark_opened(record.activation_id)
            record = await self._refresh_status(record)
        self.metrics.increment("lnurl_activation_opened_total", purpose=record.purpose.value)
        await self._audit("lnurl_activation_opened", record, reason_code="opened")
        return self._response(record)

    async def complete_activation(
        self,
        activation_reference: str,
        *,
        expected_purpose: LNURLActivationPurpose,
        device_key_fingerprint: str | None = None,
        active_pop_session_context: dict[str, Any] | None = None,
    ) -> LNURLActivationStatusResponse:
        record = await self._lookup_generic(activation_reference)
        record = await self._refresh_status(record)
        if record.purpose != LNURLActivationPurpose(expected_purpose):
            raise ValueError("policy_denied")
        if record.status is LNURLActivationStatus.COMPLETED:
            return self._response(record)
        if record.status is LNURLActivationStatus.EXPIRED:
            raise ValueError("activation_expired")
        if record.status is LNURLActivationStatus.REVOKED:
            raise ValueError("activation_revoked")
        if record.status is LNURLActivationStatus.REFUNDED:
            raise ValueError("activation_refunded")
        state = await self.state_provider.get_state(record)
        if not state.payment_settled:
            await self._audit("lnurl_activation_payment_pending", record, reason_code="payment_not_settled")
            raise ValueError("payment_not_settled")
        if not state.payment_proof_exists:
            raise ValueError("payment_proof_missing")
        if record.purpose in _SUBSCRIPTION_PURPOSES and not state.entitlement_active:
            await self._audit("lnurl_activation_entitlement_pending", record, reason_code="entitlement_pending")
            raise ValueError("entitlement_pending")
        decision = self._policy_decision(record, state, device_key_fingerprint, active_pop_session_context)
        if decision not in {"allow", "allowed", True, None}:
            await self._audit("lnurl_activation_policy_denied", record, reason_code=str(decision))
            self.metrics.increment("lnurl_activation_policy_denied_total", reason=str(decision))
            raise ValueError(str(decision) or "policy_denied")
        record = await self.repository.mark_completed(record.activation_id)
        self.metrics.increment("lnurl_activation_completed_total", purpose=record.purpose.value)
        await self._audit("lnurl_activation_completed", record, reason_code="completed")
        return self._response(record)

    async def expire_activation(self, activation_reference: str) -> LNURLActivationStatusResponse:
        record = await self._lookup_generic(activation_reference)
        updated = await self.repository.mark_expired(record.activation_id)
        self.metrics.increment("lnurl_activation_expired_total", purpose=updated.purpose.value)
        await self._audit("lnurl_activation_expired", updated, reason_code="expired")
        return self._response(updated)

    async def revoke_activation(self, activation_reference: str) -> LNURLActivationStatusResponse:
        updated = await self.success_action_service.revoke_success_action(activation_reference)
        return self._response(updated)

    async def handle_payment_refund(self, payment_request_id: str) -> int:
        records = await self.repository.get_by_payment_request_id(payment_request_id)
        count = 0
        for record in records:
            updated = await self.repository.mark_refunded(record.activation_id)
            self.metrics.increment("lnurl_activation_refunded_total", purpose=updated.purpose.value)
            await self._audit("lnurl_activation_refunded", updated, reason_code="refunded")
            count += 1
        return count

    async def handle_entitlement_revocation(self, entitlement_id: str) -> int:
        # Repository protocol intentionally indexes payment ids; SQL implementations can provide a direct lookup.
        count = 0
        if hasattr(self.repository, "_records"):
            for record in list(getattr(self.repository, "_records").values()):
                if record.entitlement_id == entitlement_id:
                    updated = await self.repository.revoke(record.activation_id)
                    await self._audit("lnurl_activation_revoked", updated, reason_code="entitlement_revoked")
                    count += 1
        return count

    async def _refresh_status(self, record: LNURLSuccessActionRecord) -> LNURLSuccessActionRecord:
        now = datetime.now(UTC)
        if record.status is LNURLActivationStatus.COMPLETED:
            return record
        if record.status in {LNURLActivationStatus.EXPIRED, LNURLActivationStatus.REVOKED, LNURLActivationStatus.REFUNDED, LNURLActivationStatus.FAILED}:
            return record
        if record.expires_at <= now:
            return await self.repository.mark_expired(record.activation_id)
        state = await self.state_provider.get_state(record)
        if state.payment_refunded:
            return await self.repository.mark_refunded(record.activation_id)
        if state.entitlement_revoked:
            return await self.repository.revoke(record.activation_id)
        if not state.payment_settled:
            return await self.repository.mark_payment_pending(record.activation_id)
        if not state.payment_proof_exists:
            return await self.repository.mark_payment_settled(record.activation_id, state.payment_proof_id)
        if record.purpose in _SUBSCRIPTION_PURPOSES and not state.entitlement_active:
            return await self.repository.mark_entitlement_pending(record.activation_id)
        return await self.repository.mark_ready(record.activation_id, state.entitlement_id)

    async def _lookup_generic(self, activation_reference: str) -> LNURLSuccessActionRecord:
        record = await self.repository.get_by_activation_reference_hash(self.success_action_service.activation_reference_hash(activation_reference))
        if record is None:
            raise ValueError("activation_not_found")
        return record

    def _response(self, record: LNURLSuccessActionRecord) -> LNURLActivationStatusResponse:
        ready = record.status in {LNURLActivationStatus.READY, LNURLActivationStatus.COMPLETED}
        next_url = None
        if ready and record.purpose in _RECEIPT_PURPOSES:
            next_url = "/receipts/ready"
        elif ready:
            next_url = "/access/continue"
        return LNURLActivationStatusResponse(
            activation_id=sha256_prefixed(record.activation_id),
            status=record.status,
            purpose=record.purpose,
            payment_status="settled" if record.status in {LNURLActivationStatus.PAYMENT_SETTLED, LNURLActivationStatus.ENTITLEMENT_PENDING, LNURLActivationStatus.READY, LNURLActivationStatus.COMPLETED} else "pending",
            entitlement_status="active" if ready and record.purpose in _SUBSCRIPTION_PURPOSES else ("not_required" if record.purpose in _RECEIPT_PURPOSES else "pending"),
            ready=ready,
            completed=record.status is LNURLActivationStatus.COMPLETED,
            expires_at=record.expires_at,
            safe_next_url=next_url,
            receipt_reference=sha256_prefixed(record.activation_id) if record.purpose in _RECEIPT_PURPOSES else None,
            reason_code=record.status.value,
        )

    def _policy_decision(self, record: LNURLSuccessActionRecord, state: ActivationDependencyState, device_key_fingerprint: str | None, active_pop_session_context: dict[str, Any] | None) -> Any:
        if self.policy_engine is None:
            return "allow"
        result = self.policy_engine.decide(
            "lnurl_activation_complete",
            {
                "purpose": record.purpose.value,
                "payment_status": "settled" if state.payment_settled else "pending",
                "entitlement_status": "active" if state.entitlement_active else "pending",
                "device_status": "present" if device_key_fingerprint else "missing",
                "pop_session_status": "present" if active_pop_session_context else "missing",
                "revocation_state": record.status.value,
            },
        )
        return getattr(result, "decision", result)

    async def _audit(self, event_type: str, record: LNURLSuccessActionRecord, *, reason_code: str) -> None:
        if self.audit_chain is None:
            return
        payload = {
            "activation_object_hash": sha256_prefixed(record.activation_id),
            "purpose": record.purpose.value,
            "payment_request_hash": sha256_prefixed(record.payment_request_id),
            "payment_proof_fingerprint": record.payment_proof_id,
            "entitlement_fingerprint": record.entitlement_id,
            "principal_pseudonym": record.wallet_principal_hash or record.lightning_principal_hash,
            "reason_code": reason_code,
        }
        result = self.audit_chain.record_event(event_type, payload) if hasattr(self.audit_chain, "record_event") else None
        if isawaitable(result):
            await result


def default_activation_service() -> LNURLActivationService:
    config = LNURLSuccessActionConfig()
    success_action_service = LNURLSuccessActionService(config=config)
    return LNURLActivationService(success_action_service=success_action_service)
