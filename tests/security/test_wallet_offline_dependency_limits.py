from app.api.access_dependencies import _OFFLINE_FORBIDDEN_ACTIONS


def test_offline_pack_forbidden_actions_remain_closed() -> None:
    assert {"treasury_policy_change", "add_device", "recovery_change", "lockdown_release", "business_role_assignment", "increase_scope"} <= _OFFLINE_FORBIDDEN_ACTIONS
