import pytest

from app.domain.payregister_lnurl.roles import PayRegisterActorType, PayRegisterCashierRole
from app.domain.payregister_lnurl.statuses import PayRegisterShiftStatus, PayRegisterTerminalStatus
from app.services.payregister.role_binding_service import PayRegisterRoleBinding, PayRegisterRoleBindingService


def binding(**overrides):
    values = dict(
        role_binding_hash="hmac:role",
        workspace_hash="hmac:workspace",
        store_hash="hmac:store",
        terminal_hash="hmac:terminal",
        shift_hash="hmac:shift",
        actor_type=PayRegisterActorType.CASHIER,
        role=PayRegisterCashierRole.CASHIER,
    )
    values.update(overrides)
    return PayRegisterRoleBinding(**values)


def test_cashier_permissions_are_explicit_and_no_admin_wildcard():
    ctx = PayRegisterRoleBindingService().validate_role_binding(binding())
    assert "payregister:payment:create" in ctx.effective_permissions
    assert "payregister:receipt:read" in ctx.effective_permissions
    assert "payregister:refund:approve" in ctx.forbidden_permissions
    assert "payregister:*" not in ctx.effective_permissions


def test_revoked_role_terminal_or_pop_session_is_denied():
    service = PayRegisterRoleBindingService()
    with pytest.raises(Exception, match="revoked"):
        service.validate_role_binding(binding(revoked=True))
    with pytest.raises(Exception, match="Terminal"):
        service.validate_role_binding(binding(terminal_status=PayRegisterTerminalStatus.SUSPENDED))
    with pytest.raises(Exception, match="PoP"):
        service.validate_role_binding(binding(pop_session_status="missing"))


def test_inactive_shift_blocks_payment_context_authorization():
    with pytest.raises(Exception, match="Shift"):
        PayRegisterRoleBindingService().validate_role_binding(binding(shift_status=PayRegisterShiftStatus.CLOSED))


def test_cashier_cannot_approve_refund():
    ctx = PayRegisterRoleBindingService().validate_role_binding(binding())
    with pytest.raises(Exception):
        PayRegisterRoleBindingService().require_permission(ctx, "payregister:refund:approve")
