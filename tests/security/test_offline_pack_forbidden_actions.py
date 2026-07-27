from app.services.access.offline_policy import FORBIDDEN_OFFLINE_ACTIONS


def test_admin_treasury_recovery_and_lnurl_withdraw_are_always_forbidden():
    assert {
        "transaction_sign",
        "treasury_policy_change",
        "recovery_complete",
        "lockdown_release",
        "lnurl_withdraw_execute",
        "payregister_admin",
    } <= FORBIDDEN_OFFLINE_ACTIONS
