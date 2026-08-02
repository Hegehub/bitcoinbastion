from app.services.access.offline_policy import (
    FORBIDDEN_OFFLINE_ACTIONS,
    PROFILE_RULES,
    OfflineProfile,
)


def test_cashier_shift_is_terminal_limited_and_not_settlement_authority():
    rule = PROFILE_RULES[OfflineProfile.PAYREGISTER_CASHIER_SHIFT]
    assert rule["certificate_required"]
    assert rule["device_classes"] == {"payregister_device"}
    assert "lnurl_withdraw_execute" in FORBIDDEN_OFFLINE_ACTIONS
    assert "payment_settled" not in rule["allowed_actions"]
