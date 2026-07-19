import pytest

from app.domain.payregister_lnurl.roles import PayRegisterActorType, PayRegisterCashierRole
from app.domain.payregister_lnurl.statuses import PayRegisterShiftStatus, PayRegisterTerminalStatus
from app.services.payregister.role_binding_service import PayRegisterRoleBinding
from app.services.payregister.shift_service import PayRegisterShiftService


def binding(**overrides):
    values = dict(
        role_binding_hash="hmac:role",
        workspace_hash="hmac:workspace",
        store_hash="hmac:store",
        terminal_hash="hmac:terminal",
        shift_hash="hmac:opening",
        actor_type=PayRegisterActorType.CASHIER,
        role=PayRegisterCashierRole.CASHIER,
    )
    values.update(overrides)
    return PayRegisterRoleBinding(**values)


def test_open_activate_close_shift_lifecycle_emits_audit():
    service = PayRegisterShiftService()
    shift = service.open_shift(binding=binding(), opening_device_fingerprint="sha256:device")
    assert shift.status == PayRegisterShiftStatus.ACTIVE
    assert service.get_active_shift_for_terminal("hmac:terminal").shift_hash == shift.shift_hash
    closing = service.begin_shift_close(shift.shift_id)
    assert closing.status == PayRegisterShiftStatus.CLOSING
    closed = service.close_shift(shift.shift_id)
    assert closed.status == PayRegisterShiftStatus.CLOSED
    assert service.get_active_shift_for_terminal("hmac:terminal") is None
    assert {e["event_type"] for e in service.repository.audit_events} >= {"payregister_shift_open_requested", "payregister_shift_opened", "payregister_shift_closed"}


def test_only_one_active_shift_per_terminal():
    service = PayRegisterShiftService()
    service.open_shift(binding=binding(), opening_device_fingerprint="sha256:device")
    with pytest.raises(Exception):
        service.open_shift(binding=binding(role_binding_hash="hmac:role2"), opening_device_fingerprint="sha256:device2")


def test_revoked_or_suspended_terminal_cannot_open_shift():
    service = PayRegisterShiftService()
    with pytest.raises(Exception):
        service.open_shift(binding=binding(terminal_status=PayRegisterTerminalStatus.REVOKED), opening_device_fingerprint="sha256:device")
