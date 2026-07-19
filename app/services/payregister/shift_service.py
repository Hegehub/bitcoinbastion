"""PayRegister cashier shift lifecycle service."""
from __future__ import annotations

import secrets
from dataclasses import dataclass, replace
from datetime import UTC, datetime, timedelta
from typing import Any, Protocol

from app.domain.payregister_lnurl.errors import PayRegisterPolicyDeniedError, PayRegisterRevokedError, PayRegisterShiftInactiveError, PayRegisterTerminalInactiveError
from app.domain.payregister_lnurl.statuses import PayRegisterShiftStatus, PayRegisterTerminalStatus
from app.services.access.crypto.hashing import hmac_sha256_prefixed, sha256_prefixed
from app.services.payregister.role_binding_service import PayRegisterRoleBinding, PayRegisterRoleBindingService


@dataclass(frozen=True, slots=True)
class PayRegisterShiftRecord:
    shift_id: str
    shift_hash: str
    workspace_hash: str
    store_hash: str
    terminal_hash: str
    role_binding_hash: str
    opening_device_fingerprint: str
    status: PayRegisterShiftStatus
    opened_at: datetime
    expires_at: datetime
    policy_hash: str
    opening_audit_event_hash: str
    activated_at: datetime | None = None
    closing_started_at: datetime | None = None
    closed_at: datetime | None = None
    closing_audit_event_hash: str | None = None


class PayRegisterShiftPolicyHook(Protocol):
    def evaluate(self, action: str, context: dict[str, Any]) -> bool: ...


class AllowShiftPolicy:
    def evaluate(self, action: str, context: dict[str, Any]) -> bool:
        return True


class InMemoryPayRegisterShiftRepository:
    def __init__(self) -> None:
        self.shifts_by_id: dict[str, PayRegisterShiftRecord] = {}
        self.active_shift_by_terminal_hash: dict[str, str] = {}
        self.audit_events: list[dict[str, Any]] = []

    def save(self, shift: PayRegisterShiftRecord) -> PayRegisterShiftRecord:
        self.shifts_by_id[shift.shift_id] = shift
        if shift.status == PayRegisterShiftStatus.ACTIVE:
            self.active_shift_by_terminal_hash[shift.terminal_hash] = shift.shift_id
        elif self.active_shift_by_terminal_hash.get(shift.terminal_hash) == shift.shift_id:
            self.active_shift_by_terminal_hash.pop(shift.terminal_hash, None)
        return shift

    def get(self, shift_ref: str) -> PayRegisterShiftRecord | None:
        return self.shifts_by_id.get(shift_ref) or next((shift for shift in self.shifts_by_id.values() if shift.shift_hash == shift_ref), None)

    def get_active_for_terminal(self, terminal_hash: str) -> PayRegisterShiftRecord | None:
        shift_id = self.active_shift_by_terminal_hash.get(terminal_hash)
        return self.shifts_by_id.get(shift_id) if shift_id else None

    def audit(self, event_type: str, payload: dict[str, Any]) -> str:
        event_hash = sha256_prefixed(f"{event_type}:{len(self.audit_events)}:{payload}")
        self.audit_events.append({"event_type": event_type, "event_hash": event_hash, **payload})
        return event_hash


class PayRegisterShiftService:
    def __init__(self, *, repository: InMemoryPayRegisterShiftRepository | None = None, role_service: PayRegisterRoleBindingService | None = None, policy_hook: PayRegisterShiftPolicyHook | None = None, pepper: str = "dev-payregister-shift-pepper-change-me", clock: Any | None = None) -> None:
        self.repository = repository or InMemoryPayRegisterShiftRepository()
        self.role_service = role_service or PayRegisterRoleBindingService()
        self.policy_hook = policy_hook or AllowShiftPolicy()
        self.pepper = pepper
        self.clock = clock or (lambda: datetime.now(UTC))

    def open_shift(self, *, binding: PayRegisterRoleBinding, opening_device_fingerprint: str, ttl_seconds: int = 28_800) -> PayRegisterShiftRecord:
        self.repository.audit("payregister_shift_open_requested", {"workspace_hash": binding.workspace_hash, "terminal_hash": binding.terminal_hash, "role_binding_hash": binding.role_binding_hash})
        if binding.terminal_status in {PayRegisterTerminalStatus.REVOKED, PayRegisterTerminalStatus.SUSPENDED, PayRegisterTerminalStatus.MAINTENANCE}:
            self.repository.audit("payregister_shift_open_denied", {"terminal_hash": binding.terminal_hash, "reason_code": "terminal_inactive"})
            raise PayRegisterTerminalInactiveError("Terminal cannot open shift")
        if binding.revoked:
            self.repository.audit("payregister_shift_open_denied", {"role_binding_hash": binding.role_binding_hash, "reason_code": "role_revoked"})
            raise PayRegisterRevokedError("Role binding is revoked")
        active = self.repository.get_active_for_terminal(binding.terminal_hash)
        if active is not None:
            raise PayRegisterPolicyDeniedError("Only one active shift per terminal is allowed")
        resolved = self.role_service.validate_role_binding(replace(binding, shift_status=PayRegisterShiftStatus.ACTIVE))
        if not self.policy_hook.evaluate("payregister:shift:open", {"workspace_hash": resolved.workspace_hash, "terminal_hash": resolved.terminal_hash, "role": resolved.role.value}):
            self.repository.audit("payregister_shift_open_denied", {"terminal_hash": binding.terminal_hash, "reason_code": "policy_denied"})
            raise PayRegisterPolicyDeniedError("Policy denied shift open")
        now = self.clock()
        shift_id = f"prs_{secrets.token_urlsafe(18)}"
        shift_hash = hmac_sha256_prefixed(self.pepper, f"{binding.workspace_hash}:{binding.terminal_hash}:{shift_id}")
        audit_hash = self.repository.audit("payregister_shift_opened", {"workspace_hash": binding.workspace_hash, "store_hash": binding.store_hash, "terminal_hash": binding.terminal_hash, "shift_hash": shift_hash, "role_binding_hash": binding.role_binding_hash})
        return self.repository.save(
            PayRegisterShiftRecord(
                shift_id=shift_id,
                shift_hash=shift_hash,
                workspace_hash=binding.workspace_hash,
                store_hash=binding.store_hash,
                terminal_hash=binding.terminal_hash,
                role_binding_hash=binding.role_binding_hash,
                opening_device_fingerprint=opening_device_fingerprint,
                status=PayRegisterShiftStatus.ACTIVE,
                opened_at=now,
                activated_at=now,
                expires_at=now + timedelta(seconds=ttl_seconds),
                policy_hash=resolved.policy_hash,
                opening_audit_event_hash=audit_hash,
            )
        )

    def get_active_shift_for_terminal(self, terminal_hash: str) -> PayRegisterShiftRecord | None:
        shift = self.repository.get_active_for_terminal(terminal_hash)
        if shift and shift.expires_at <= self.clock():
            return self.expire_stale_shift(shift.shift_id)
        return shift

    def suspend_shift(self, shift_ref: str) -> PayRegisterShiftRecord:
        shift = self._shift(shift_ref)
        updated = replace(shift, status=PayRegisterShiftStatus.SUSPENDED)
        self.repository.audit("payregister_shift_suspended", {"shift_hash": shift.shift_hash})
        return self.repository.save(updated)

    def resume_shift(self, shift_ref: str) -> PayRegisterShiftRecord:
        shift = self._shift(shift_ref)
        if shift.closed_at is not None:
            raise PayRegisterShiftInactiveError("Closed shift cannot resume")
        updated = replace(shift, status=PayRegisterShiftStatus.ACTIVE)
        self.repository.audit("payregister_shift_resumed", {"shift_hash": shift.shift_hash})
        return self.repository.save(updated)

    def begin_shift_close(self, shift_ref: str) -> PayRegisterShiftRecord:
        shift = self._shift(shift_ref)
        updated = replace(shift, status=PayRegisterShiftStatus.CLOSING, closing_started_at=self.clock())
        self.repository.audit("payregister_shift_close_requested", {"shift_hash": shift.shift_hash})
        return self.repository.save(updated)

    def close_shift(self, shift_ref: str) -> PayRegisterShiftRecord:
        shift = self._shift(shift_ref)
        audit_hash = self.repository.audit("payregister_shift_closed", {"shift_hash": shift.shift_hash})
        return self.repository.save(replace(shift, status=PayRegisterShiftStatus.CLOSED, closed_at=self.clock(), closing_audit_event_hash=audit_hash))

    def revoke_shift(self, shift_ref: str) -> PayRegisterShiftRecord:
        shift = self._shift(shift_ref)
        self.repository.audit("payregister_shift_revoked", {"shift_hash": shift.shift_hash})
        return self.repository.save(replace(shift, status=PayRegisterShiftStatus.REVOKED))

    def expire_stale_shift(self, shift_ref: str) -> PayRegisterShiftRecord:
        shift = self._shift(shift_ref)
        if shift.status == PayRegisterShiftStatus.ACTIVE and shift.expires_at <= self.clock():
            self.repository.audit("payregister_shift_expired", {"shift_hash": shift.shift_hash})
            return self.repository.save(replace(shift, status=PayRegisterShiftStatus.EXPIRED))
        return shift

    def _shift(self, shift_ref: str) -> PayRegisterShiftRecord:
        shift = self.repository.get(shift_ref)
        if shift is None:
            raise PayRegisterShiftInactiveError("Shift unavailable")
        return shift
