"""Wallet auth risk domain hints."""

from __future__ import annotations

from enum import StrEnum

from app.domain.wallet_auth.actions import WalletAuthAction
from app.domain.wallet_auth.proofs import WalletVerificationStrength, is_strength_at_least


class WalletRiskLevel(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


DEFAULT_WALLET_ACTION_RISK = {
    WalletAuthAction.REGISTER: WalletRiskLevel.MEDIUM,
    WalletAuthAction.LOGIN: WalletRiskLevel.MEDIUM,
    WalletAuthAction.CREATE_SESSION: WalletRiskLevel.MEDIUM,
    WalletAuthAction.NEW_DEVICE: WalletRiskLevel.HIGH,
    WalletAuthAction.CREATE_API_KEY: WalletRiskLevel.HIGH,
    WalletAuthAction.INCREASE_SCOPE: WalletRiskLevel.HIGH,
    WalletAuthAction.EXPORT_DATA: WalletRiskLevel.HIGH,
    WalletAuthAction.TREASURY_POLICY_CHANGE: WalletRiskLevel.CRITICAL,
    WalletAuthAction.RECOVERY_COMPLETE: WalletRiskLevel.CRITICAL,
    WalletAuthAction.LOCKDOWN_RELEASE: WalletRiskLevel.CRITICAL,
    WalletAuthAction.ENTERPRISE_POLICY_CHANGE: WalletRiskLevel.CRITICAL,
    WalletAuthAction.PAYREGISTER_ADMIN_ENABLE: WalletRiskLevel.CRITICAL,
    WalletAuthAction.LNURL_WITHDRAW_REFUND: WalletRiskLevel.HIGH,
}


def default_risk_for_action(action: WalletAuthAction | str) -> WalletRiskLevel:
    return DEFAULT_WALLET_ACTION_RISK.get(WalletAuthAction(action), WalletRiskLevel.MEDIUM)


def is_compatibility_strength_allowed_for_action(action: WalletAuthAction | str) -> bool:
    risk = default_risk_for_action(action)
    return risk not in {WalletRiskLevel.HIGH, WalletRiskLevel.CRITICAL}


def is_strength_allowed_for_action(
    strength: WalletVerificationStrength | str, action: WalletAuthAction | str
) -> bool:
    if is_compatibility_strength_allowed_for_action(action):
        return True
    return is_strength_at_least(strength, WalletVerificationStrength.STANDARD)
