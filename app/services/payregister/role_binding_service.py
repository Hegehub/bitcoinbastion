"""Workspace-scoped PayRegister role binding validation."""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Protocol

from app.domain.payregister_lnurl.errors import PayRegisterPolicyDeniedError, PayRegisterRevokedError, PayRegisterShiftInactiveError, PayRegisterTerminalInactiveError
from app.domain.payregister_lnurl.roles import PayRegisterActorType, PayRegisterCashierRole
from app.domain.payregister_lnurl.statuses import PayRegisterShiftStatus, PayRegisterTerminalStatus


@dataclass(frozen=True, slots=True)
class PayRegisterRoleBinding:
    role_binding_hash: str
    workspace_hash: str
    store_hash: str
    terminal_hash: str
    shift_hash: str
    actor_type: PayRegisterActorType
    role: PayRegisterCashierRole
    terminal_status: PayRegisterTerminalStatus = PayRegisterTerminalStatus.ACTIVE
    shift_status: PayRegisterShiftStatus = PayRegisterShiftStatus.ACTIVE
    device_status: str = "active"
    pop_session_status: str = "active"
    revoked: bool = False


@dataclass(frozen=True, slots=True)
class PayRegisterResolvedRoleContext:
    allowed: bool
    actor_type: PayRegisterActorType
    role: PayRegisterCashierRole
    workspace_hash: str
    store_hash: str
    terminal_hash: str
    shift_hash: str
    role_binding_hash: str
    effective_permissions: frozenset[str]
    forbidden_permissions: frozenset[str]
    policy_hash: str


class PayRegisterRoleRevocationChecker(Protocol):
    def is_revoked(self, target_type: str, target_hash: str) -> bool: ...


class NoopPayRegisterRoleRevocationChecker:
    def is_revoked(self, target_type: str, target_hash: str) -> bool:
        return False


_ROLE_PERMISSIONS: Mapping[PayRegisterCashierRole, frozenset[str]] = {
    PayRegisterCashierRole.CASHIER: frozenset({"payregister:payment:create", "payregister:receipt:read"}),
    PayRegisterCashierRole.SENIOR_CASHIER: frozenset({"payregister:payment:create", "payregister:receipt:read", "payregister:refund:request"}),
    PayRegisterCashierRole.SHIFT_SUPERVISOR: frozenset({"payregister:payment:create", "payregister:receipt:read", "payregister:refund:request", "payregister:shift:suspend"}),
    PayRegisterCashierRole.STORE_MANAGER: frozenset({"payregister:payment:create", "payregister:receipt:read", "payregister:shift:open", "payregister:shift:close"}),
}
_FORBIDDEN_DEFAULT = frozenset({"payregister:refund:approve", "payregister:admin", "treasury:read", "treasury:policy:write", "payregister:withdraw"})


class PayRegisterRoleBindingService:
    def __init__(self, *, revocation_checker: PayRegisterRoleRevocationChecker | None = None) -> None:
        self.revocation_checker = revocation_checker or NoopPayRegisterRoleRevocationChecker()

    def validate_role_binding(self, binding: PayRegisterRoleBinding) -> PayRegisterResolvedRoleContext:
        if binding.revoked or self.revocation_checker.is_revoked("payregister_cashier_role", binding.role_binding_hash):
            raise PayRegisterRevokedError("Cashier role binding is revoked")
        if binding.terminal_status != PayRegisterTerminalStatus.ACTIVE:
            raise PayRegisterTerminalInactiveError("Terminal is not active")
        if binding.shift_status != PayRegisterShiftStatus.ACTIVE:
            raise PayRegisterShiftInactiveError("Shift is not active")
        if binding.device_status != "active" or binding.pop_session_status != "active":
            raise PayRegisterPolicyDeniedError("Active device binding and PoP session are required")
        effective = _ROLE_PERMISSIONS[binding.role]
        return PayRegisterResolvedRoleContext(
            allowed=True,
            actor_type=binding.actor_type,
            role=binding.role,
            workspace_hash=binding.workspace_hash,
            store_hash=binding.store_hash,
            terminal_hash=binding.terminal_hash,
            shift_hash=binding.shift_hash,
            role_binding_hash=binding.role_binding_hash,
            effective_permissions=effective,
            forbidden_permissions=_FORBIDDEN_DEFAULT,
            policy_hash="sha256:payregister-role-policy-v1",
        )

    def require_permission(self, context: PayRegisterResolvedRoleContext, permission: str) -> None:
        if permission in context.forbidden_permissions or permission not in context.effective_permissions:
            raise PayRegisterPolicyDeniedError("PayRegister role is not authorized for this action")
