import pytest

from app.domain.payregister_lnurl.roles import PayRegisterActorType, PayRegisterCashierRole
from app.domain.payregister_lnurl.statuses import PayRegisterShiftStatus, PayRegisterTerminalStatus
from app.services.payregister.role_binding_service import PayRegisterRoleBinding, PayRegisterRoleBindingService
from app.services.payregister.shift_service import PayRegisterShiftService


def binding(**overrides):
    values = dict(role_binding_hash="hmac:role", workspace_hash="hmac:workspace", store_hash="hmac:store", terminal_hash="hmac:terminal", shift_hash="hmac:shift", actor_type=PayRegisterActorType.CASHIER, role=PayRegisterCashierRole.CASHIER)
    values.update(overrides)
    return PayRegisterRoleBinding(**values)


def test_cashier_cannot_create_payment_without_active_shift_or_pop_session():
    with pytest.raises(Exception):
        PayRegisterRoleBindingService().validate_role_binding(binding(shift_status=PayRegisterShiftStatus.CLOSED))
    with pytest.raises(Exception):
        PayRegisterRoleBindingService().validate_role_binding(binding(pop_session_status="missing"))


def test_revoked_cashier_role_and_suspended_terminal_are_denied():
    with pytest.raises(Exception):
        PayRegisterRoleBindingService().validate_role_binding(binding(revoked=True))
    with pytest.raises(Exception):
        PayRegisterRoleBindingService().validate_role_binding(binding(terminal_status=PayRegisterTerminalStatus.SUSPENDED))


def test_policy_engine_is_invoked_for_shift_open():
    class DenyPolicy:
        called = False
        def evaluate(self, action, context):
            self.called = True
            return False
    policy = DenyPolicy()
    service = PayRegisterShiftService(policy_hook=policy)
    with pytest.raises(Exception):
        service.open_shift(binding=binding(), opening_device_fingerprint="sha256:device")
    assert policy.called is True


def test_cashier_cannot_approve_refund_or_withdraw():
    ctx = PayRegisterRoleBindingService().validate_role_binding(binding())
    service = PayRegisterRoleBindingService()
    with pytest.raises(Exception):
        service.require_permission(ctx, "payregister:refund:approve")
    with pytest.raises(Exception):
        service.require_permission(ctx, "payregister:withdraw")
