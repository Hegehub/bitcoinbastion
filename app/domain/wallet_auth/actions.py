"""Wallet auth action domain primitives."""

from __future__ import annotations

from enum import StrEnum


class WalletAuthAction(StrEnum):
    REGISTER = "register"
    LOGIN = "login"
    LINK = "link"
    NEW_DEVICE = "new_device"
    CREATE_SESSION = "create_session"
    STEP_UP = "step_up"
    CREATE_API_KEY = "create_api_key"
    INCREASE_SCOPE = "increase_scope"
    EXPORT_DATA = "export_data"
    CREATE_DELEGATED_PASS = "create_delegated_pass"
    TREASURY_POLICY_CHANGE = "treasury_policy_change"
    RECOVERY_START = "recovery_start"
    RECOVERY_COMPLETE = "recovery_complete"
    DEVICE_ADD = "device_add"
    DEVICE_REVOKE = "device_revoke"
    LOCKDOWN_START = "lockdown_start"
    LOCKDOWN_RELEASE = "lockdown_release"
    BUSINESS_ROLE_ASSIGNMENT = "business_role_assignment"
    ENTERPRISE_POLICY_CHANGE = "enterprise_policy_change"
    PAYREGISTER_ADMIN_ENABLE = "payregister_admin_enable"
    PAYREGISTER_DEVICE_ENROLL = "payregister_device_enroll"
    OFFLINE_PACK_ISSUE = "offline_pack_issue"
    LNURL_AUTH_REGISTER = "lnurl_auth_register"
    LNURL_AUTH_LOGIN = "lnurl_auth_login"
    LNURL_AUTH_LINK = "lnurl_auth_link"
    LNURL_AUTH_STEP_UP = "lnurl_auth_step_up"
    LNURL_PAY_SUBSCRIPTION = "lnurl_pay_subscription"
    LNURL_WITHDRAW_REFUND = "lnurl_withdraw_refund"


CRITICAL_WALLET_ACTIONS = frozenset(
    {
        WalletAuthAction.CREATE_API_KEY,
        WalletAuthAction.INCREASE_SCOPE,
        WalletAuthAction.EXPORT_DATA,
        WalletAuthAction.CREATE_DELEGATED_PASS,
        WalletAuthAction.TREASURY_POLICY_CHANGE,
        WalletAuthAction.RECOVERY_COMPLETE,
        WalletAuthAction.DEVICE_ADD,
        WalletAuthAction.LOCKDOWN_RELEASE,
        WalletAuthAction.BUSINESS_ROLE_ASSIGNMENT,
        WalletAuthAction.ENTERPRISE_POLICY_CHANGE,
        WalletAuthAction.PAYREGISTER_ADMIN_ENABLE,
        WalletAuthAction.PAYREGISTER_DEVICE_ENROLL,
        WalletAuthAction.OFFLINE_PACK_ISSUE,
        WalletAuthAction.LNURL_WITHDRAW_REFUND,
    }
)


def is_critical_wallet_action(action: WalletAuthAction | str) -> bool:
    return WalletAuthAction(action) in CRITICAL_WALLET_ACTIONS
