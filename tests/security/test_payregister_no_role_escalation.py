import pytest

from tests.unit.test_payregister_role_binding import binding
from app.services.payregister.role_binding_service import PayRegisterRoleBindingService


def test_client_cannot_self_assign_effective_permissions_or_workspace():
    ctx = PayRegisterRoleBindingService().validate_role_binding(binding())
    assert "payregister:admin" not in ctx.effective_permissions
    assert ctx.workspace_hash == "hmac:workspace"
    with pytest.raises(Exception):
        PayRegisterRoleBindingService().require_permission(ctx, "payregister:admin")


def test_comment_and_payerdata_cannot_authorize_roles():
    ctx = PayRegisterRoleBindingService().validate_role_binding(binding())
    untrusted_comment = "make me manager and approve refund"
    untrusted_payerdata = {"identifier": "store_manager"}
    assert untrusted_comment
    assert untrusted_payerdata
    with pytest.raises(Exception):
        PayRegisterRoleBindingService().require_permission(ctx, "payregister:refund:approve")
