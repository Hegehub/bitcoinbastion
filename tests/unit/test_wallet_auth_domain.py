from app.domain.wallet_auth import (
    BUSINESS_RECOVERY_FACTORS,
    CRITICAL_WALLET_ACTIONS,
    DEDICATED_AUTH_ADDRESS_WARNING,
    ENTERPRISE_RECOVERY_FACTORS,
    FORBIDDEN_WALLET_SECRET_TERMS,
    LITE_BASIC_RECOVERY_FACTORS,
    REQUIRED_SIGNATURE_WARNING,
    SOVEREIGN_RECOVERY_FACTORS,
    RecoveryFactorType,
    WalletAuthAction,
    WalletAuthDomainError,
    WalletDeviceClass,
    WalletNetwork,
    WalletProofTooWeakError,
    WalletProofType,
    WalletRecoveryProfile,
    WalletRiskLevel,
    WalletSecretInputForbiddenError,
    WalletVerificationStrength,
    default_risk_for_action,
    is_compatibility_strength_allowed_for_action,
    is_production_network,
    is_root_of_trust_device_class,
    is_strength_at_least,
    is_test_network,
    verification_strength_rank,
)


def test_wallet_network_values_are_stable_and_not_interchangeable() -> None:
    assert WalletNetwork.BITCOIN_MAINNET.value == "bitcoin-mainnet"
    assert WalletNetwork.BITCOIN_TESTNET.value == "bitcoin-testnet"
    assert WalletNetwork.BITCOIN_SIGNET.value == "bitcoin-signet"
    assert WalletNetwork.BITCOIN_REGTEST.value == "bitcoin-regtest"
    assert is_production_network(WalletNetwork.BITCOIN_MAINNET)
    assert not is_test_network(WalletNetwork.BITCOIN_MAINNET)
    for network in (WalletNetwork.BITCOIN_TESTNET, WalletNetwork.BITCOIN_SIGNET, WalletNetwork.BITCOIN_REGTEST):
        assert not is_production_network(network)
        assert is_test_network(network)


def test_wallet_proof_types_and_strength_rules() -> None:
    assert WalletProofType.BIP322.value == "bip322"
    assert WalletProofType.LNURL_AUTH.value == "lnurl_auth"
    assert WalletProofType.LEGACY_MESSAGE_SIGNATURE.value == "legacy_message_signature"
    assert WalletProofType.ACCESS_CERTIFICATE_BRIDGE.value == "access_certificate_bridge"
    assert not is_strength_at_least(WalletVerificationStrength.COMPATIBILITY, WalletVerificationStrength.HIGH_ASSURANCE)
    assert verification_strength_rank(WalletVerificationStrength.COMPATIBILITY) < verification_strength_rank(WalletVerificationStrength.STANDARD)
    assert verification_strength_rank(WalletVerificationStrength.STANDARD) < verification_strength_rank(WalletVerificationStrength.HIGH_ASSURANCE)
    assert verification_strength_rank(WalletVerificationStrength.HIGH_ASSURANCE) < verification_strength_rank(WalletVerificationStrength.SOVEREIGN)


def test_critical_wallet_actions_are_explicit() -> None:
    required = {
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
    assert required <= CRITICAL_WALLET_ACTIONS
    assert WalletAuthAction.LOGIN not in CRITICAL_WALLET_ACTIONS
    assert WalletAuthAction.REGISTER not in CRITICAL_WALLET_ACTIONS


def test_default_risk_mapping_and_compatibility_hints() -> None:
    assert default_risk_for_action(WalletAuthAction.REGISTER) is WalletRiskLevel.MEDIUM
    assert default_risk_for_action(WalletAuthAction.LOGIN) is WalletRiskLevel.MEDIUM
    assert default_risk_for_action(WalletAuthAction.CREATE_SESSION) is WalletRiskLevel.MEDIUM
    assert default_risk_for_action(WalletAuthAction.NEW_DEVICE) is WalletRiskLevel.HIGH
    assert default_risk_for_action(WalletAuthAction.CREATE_API_KEY) is WalletRiskLevel.HIGH
    assert default_risk_for_action(WalletAuthAction.INCREASE_SCOPE) is WalletRiskLevel.HIGH
    assert default_risk_for_action(WalletAuthAction.EXPORT_DATA) is WalletRiskLevel.HIGH
    assert default_risk_for_action(WalletAuthAction.TREASURY_POLICY_CHANGE) is WalletRiskLevel.CRITICAL
    assert default_risk_for_action(WalletAuthAction.RECOVERY_COMPLETE) is WalletRiskLevel.CRITICAL
    assert default_risk_for_action(WalletAuthAction.LOCKDOWN_RELEASE) is WalletRiskLevel.CRITICAL
    assert default_risk_for_action(WalletAuthAction.ENTERPRISE_POLICY_CHANGE) is WalletRiskLevel.CRITICAL
    assert default_risk_for_action(WalletAuthAction.PAYREGISTER_ADMIN_ENABLE) is WalletRiskLevel.CRITICAL
    assert default_risk_for_action(WalletAuthAction.LNURL_WITHDRAW_REFUND) is WalletRiskLevel.HIGH
    assert not is_compatibility_strength_allowed_for_action(WalletAuthAction.TREASURY_POLICY_CHANGE)
    assert not is_compatibility_strength_allowed_for_action(WalletAuthAction.LNURL_WITHDRAW_REFUND)


def test_wallet_device_domain_rules() -> None:
    assert WalletDeviceClass.BROWSER_EXTENSION.value == "browser_extension"
    assert WalletDeviceClass.HARDWARE_WALLET.value == "hardware_wallet"
    assert WalletDeviceClass.LIGHTNING_WALLET.value == "lightning_wallet"
    assert WalletDeviceClass.PAYREGISTER_DEVICE.value == "payregister_device"
    assert not is_root_of_trust_device_class(WalletDeviceClass.BROWSER_EXTENSION)
    assert is_root_of_trust_device_class(WalletDeviceClass.HARDWARE_WALLET)


def test_recovery_profiles_and_factors_do_not_reintroduce_forbidden_recovery() -> None:
    assert WalletRecoveryProfile.ENTERPRISE.value == "enterprise"
    all_factors = set().union(
        LITE_BASIC_RECOVERY_FACTORS,
        BUSINESS_RECOVERY_FACTORS,
        ENTERPRISE_RECOVERY_FACTORS,
        SOVEREIGN_RECOVERY_FACTORS,
    )
    serialized = " ".join(factor.value for factor in all_factors)
    for forbidden in ("seed", "private_key", "mnemonic", "xprv", "support", "email"):
        assert forbidden not in serialized
    assert RecoveryFactorType.LNURL_AUTH_RESIGNATURE not in BUSINESS_RECOVERY_FACTORS
    assert RecoveryFactorType.LNURL_AUTH_RESIGNATURE not in ENTERPRISE_RECOVERY_FACTORS
    assert len(ENTERPRISE_RECOVERY_FACTORS) > 1
    assert len(SOVEREIGN_RECOVERY_FACTORS) > 1


def test_wallet_constants_include_required_safety_copy() -> None:
    assert "does not authorize a Bitcoin transaction" in REQUIRED_SIGNATURE_WARNING
    assert "Bastion will never ask for your Bitcoin seed" in DEDICATED_AUTH_ADDRESS_WARNING
    assert {"seed", "private_key", "mnemonic", "xprv"} <= set(FORBIDDEN_WALLET_SECRET_TERMS)


def test_wallet_domain_errors_are_safe_for_logs() -> None:
    for error in (WalletAuthDomainError(), WalletProofTooWeakError(), WalletSecretInputForbiddenError()):
        message = str(error).lower()
        assert message
        for secret_like in ("bc1qrawaddress", "raw_signature", "seed phrase", "private key", "k1=", "session-token"):
            assert secret_like not in message
