from __future__ import annotations

import importlib
from datetime import UTC, datetime, timedelta

import pytest

from app.domain.lnurl import (
    DEFAULT_ALLOWED_PAYER_DATA_FIELDS,
    DEFAULT_LNURL_ACTION_INTENT_MAP,
    DEFAULT_OPTIONAL_PAYER_DATA_FIELDS,
    DEFAULT_PROHIBITED_PAYER_DATA_FIELDS,
    LIGHTNING_ADDRESS_IDENTITY_WARNING,
    LNURL_AUTH_CONTROL_WARNING,
    LNURL_COMMENT_SECURITY_WARNING,
    LNURL_FORBIDDEN_SECRET_FIELDS,
    LNURL_K1_BYTES,
    LNURL_PAYMENT_SETTLEMENT_WARNING,
    LNURL_PAYERDATA_PRIVACY_WARNING,
    LNURL_WITHDRAW_SECURITY_WARNING,
    BastionLNURLIntentAction,
    BastionSuccessActionPurpose,
    InvalidLNURLStateTransitionError,
    LightningAddressDescriptor,
    LightningAddressInvalidError,
    LightningAddressPurpose,
    LightningAddressStatus,
    LightningPrincipalIdentity,
    LightningPrincipalStatus,
    LightningPrincipalType,
    LNURLAdapterType,
    LNURLAuthAction,
    LNURLAuthAttemptStatus,
    LNURLCommentPurpose,
    LNURLDomainClass,
    LNURLDomainPolicy,
    LNURLDomainStatus,
    LNURLK1Status,
    LNURLMetadataType,
    LNURLPayerDataField,
    LNURLPayerDataRequirement,
    LNURLPayerDataStatus,
    LNURLPaymentPurpose,
    LNURLPaymentStatus,
    LNURLPaymentVerificationMethod,
    LNURLRiskLevel,
    LNURLSecurityLevel,
    LNURLSettlementEvidence,
    LNURLSuccessActionDescriptor,
    LNURLSuccessActionType,
    LNURLTag,
    LNURLTransportScheme,
    LNURLVerifyStatus,
    LNURLWithdrawPurpose,
    LNURLWithdrawRiskClass,
    LNURLWithdrawStatus,
    UnsupportedLNURLTagError,
    WITHDRAW_REQUIRES_AUTH,
    WITHDRAW_REQUIRES_BUSINESS_POLICY,
    WITHDRAW_REQUIRES_STEP_UP,
    can_transition_auth_attempt,
    can_transition_k1,
    can_transition_payment,
    can_transition_withdraw,
    is_high_risk_lnurl_action,
    is_terminal_payment_status,
    is_terminal_withdraw_status,
    requires_settlement_verification,
    requires_withdraw_policy,
)


def test_tags_and_adapter_values_are_stable_and_unknown_values_fail():
    assert LNURLTag.LOGIN.value == "login"
    assert LNURLTag.PAY_REQUEST.value == "payRequest"
    assert LNURLTag.WITHDRAW_REQUEST.value == "withdrawRequest"
    assert LNURLAdapterType.LNURL_AUTH.value == "lnurl_auth"
    assert LNURLAdapterType.LNURL_VERIFY.value == "lnurl_verify"
    with pytest.raises(ValueError):
        LNURLTag("unknown")


def test_auth_actions_intent_map_k1_and_risk_helpers():
    assert {item.value for item in LNURLAuthAction} >= {"register", "login", "link", "auth"}
    assert DEFAULT_LNURL_ACTION_INTENT_MAP[LNURLAuthAction.AUTH] is BastionLNURLIntentAction.SESSION_CREATE
    assert BastionLNURLIntentAction.CREATE_API_KEY not in DEFAULT_LNURL_ACTION_INTENT_MAP.values()
    assert LNURL_K1_BYTES == 32
    assert can_transition_k1(LNURLK1Status.UNUSED, LNURLK1Status.USED)
    assert not can_transition_k1(LNURLK1Status.USED, LNURLK1Status.UNUSED)
    assert can_transition_auth_attempt(LNURLAuthAttemptStatus.PENDING, LNURLAuthAttemptStatus.REPLAYED)
    assert not can_transition_auth_attempt(LNURLAuthAttemptStatus.EXPIRED, LNURLAuthAttemptStatus.VERIFIED)
    assert is_high_risk_lnurl_action(BastionLNURLIntentAction.DEVICE_ADD)
    assert is_high_risk_lnurl_action(BastionLNURLIntentAction.ENTERPRISE_POLICY_CHANGE)
    assert LNURLRiskLevel.CRITICAL.value == "critical"


def test_payment_statuses_keep_invoice_settlement_and_verification_separate():
    assert LNURLPaymentStatus.INVOICE_ISSUED is not LNURLPaymentStatus.SETTLED
    assert LNURLPaymentStatus.SETTLED is not LNURLPaymentStatus.VERIFIED
    assert can_transition_payment(LNURLPaymentStatus.INVOICE_ISSUED, LNURLPaymentStatus.SETTLED)
    assert requires_settlement_verification(LNURLPaymentStatus.SETTLED)
    assert is_terminal_payment_status(LNURLPaymentStatus.VERIFIED)
    assert not can_transition_payment(LNURLPaymentStatus.VERIFIED, LNURLPaymentStatus.PENDING)
    assert not can_transition_payment(LNURLPaymentStatus.EXPIRED, LNURLPaymentStatus.VERIFIED)
    assert LNURLPaymentPurpose.SUBSCRIPTION.value == "subscription"
    assert LNURLPaymentVerificationMethod.MANUAL_TEST_GRANT.value == "manual_test_grant"
    assert LNURLMetadataType.TEXT_PLAIN.value == "text_plain"
    assert LNURLCommentPurpose.INVOICE_NOTE.value == "invoice_note"


def test_withdraw_policy_hints_and_transitions():
    assert LNURLWithdrawPurpose.SUBSCRIPTION_REFUND in WITHDRAW_REQUIRES_AUTH
    assert LNURLWithdrawPurpose.MERCHANT_PAYOUT in WITHDRAW_REQUIRES_BUSINESS_POLICY
    assert LNURLWithdrawRiskClass.HIGH_VALUE in WITHDRAW_REQUIRES_STEP_UP
    assert requires_withdraw_policy(LNURLWithdrawRiskClass.BUSINESS_CRITICAL)
    assert can_transition_withdraw(LNURLWithdrawStatus.APPROVED, LNURLWithdrawStatus.QR_ISSUED)
    assert not can_transition_withdraw(LNURLWithdrawStatus.PAID, LNURLWithdrawStatus.QR_ISSUED)
    assert is_terminal_withdraw_status(LNURLWithdrawStatus.PAID)


def test_lightning_address_is_routing_not_identity():
    descriptor = LightningAddressDescriptor(
        local_part="store",
        domain="pay.example",
        purpose=LightningAddressPurpose.PAYREGISTER_STORE,
        status=LightningAddressStatus.ACTIVE,
        domain_policy_version=1,
        merchant_hash="hmac-sha256:" + "a" * 64,
    )
    assert descriptor.local_part == "store"
    assert not hasattr(descriptor, "principal_id")
    assert not hasattr(descriptor, "global_user_id")
    assert LightningAddressStatus.SUSPENDED.value == "suspended"
    assert LightningAddressStatus.REVOKED.value == "revoked"
    assert LightningAddressPurpose.CUSTOM_BUSINESS.value == "custom_business"
    with pytest.raises(ValueError):
        LightningAddressDescriptor("", "example.com", LightningAddressPurpose.DONATION, LightningAddressStatus.ACTIVE, 1)


def test_payer_data_privacy_defaults_do_not_require_email_or_name():
    assert LNURLPayerDataField.AUTH in DEFAULT_ALLOWED_PAYER_DATA_FIELDS
    assert LNURLPayerDataField.PUBKEY in DEFAULT_OPTIONAL_PAYER_DATA_FIELDS
    assert LNURLPayerDataField.IDENTIFIER in DEFAULT_OPTIONAL_PAYER_DATA_FIELDS
    assert LNURLPayerDataField.EMAIL in DEFAULT_PROHIBITED_PAYER_DATA_FIELDS
    assert LNURLPayerDataField.NAME in DEFAULT_PROHIBITED_PAYER_DATA_FIELDS
    assert LNURLPayerDataRequirement.MANDATORY_BY_EXPLICIT_BUSINESS_POLICY.value == "mandatory_by_explicit_business_policy"
    assert LNURLPayerDataStatus.REDACTED.value == "redacted"


def test_success_action_descriptors_reject_secret_references():
    descriptor = LNURLSuccessActionDescriptor(
        action_type=LNURLSuccessActionType.MESSAGE,
        purpose=BastionSuccessActionPurpose.SUBSCRIPTION_ACTIVATED,
        description="Subscription ready",
        message="Payment verified",
    )
    assert descriptor.requires_entitlement_check is True
    with pytest.raises(ValueError):
        LNURLSuccessActionDescriptor(
            action_type=LNURLSuccessActionType.URL,
            purpose=BastionSuccessActionPurpose.RECEIPT,
            description="Receipt",
            url_reference="https://example.test/activate?session_token=raw",
        )


def test_lightning_principal_uses_hashed_identity_fields_only():
    principal = LightningPrincipalIdentity(
        principal_hash="hmac-sha256:" + "a" * 64,
        lnurl_key_hash="hmac-sha256:" + "b" * 64,
        auth_domain_hash="sha256:" + "c" * 64,
        principal_type=LightningPrincipalType.LNURL_AUTH_PRINCIPAL,
        verification_strength=LNURLSecurityLevel.STANDARD,
        status=LightningPrincipalStatus.ACTIVE,
        created_at=datetime.now(UTC),
    )
    assert principal.principal_hash.startswith("hmac-sha256:")
    assert not hasattr(principal, "linking_key")
    assert not hasattr(principal, "global_user_id")
    assert LightningPrincipalStatus.REVOKED.value == "revoked"
    assert LightningPrincipalStatus.RECOVERY_LOCKED.value == "recovery_locked"


def test_transport_domain_policy_separates_https_and_onion():
    policy = LNURLDomainPolicy(
        domain="auth.example",
        domain_class=LNURLDomainClass.BASTION_AUTH,
        status=LNURLDomainStatus.ACTIVE,
        allowed_schemes=(LNURLTransportScheme.HTTPS,),
        allow_cors_get=True,
        stable_auth_domain=True,
        policy_version=1,
    )
    assert policy.stable_auth_domain is True
    with pytest.raises(ValueError):
        LNURLDomainPolicy("plain.example", LNURLDomainClass.BASTION_AUTH, LNURLDomainStatus.ACTIVE, (LNURLTransportScheme.HTTP_ONION,), False, False, 1)


def test_safety_warnings_and_forbidden_fields_are_explicit():
    assert "does not prove ownership" in LNURL_AUTH_CONTROL_WARNING
    assert "Invoice creation does not prove payment" in LNURL_PAYMENT_SETTLEMENT_WARNING
    assert "payment-routing identifier" in LIGHTNING_ADDRESS_IDENTITY_WARNING
    assert "does not require email" in LNURL_PAYERDATA_PRIVACY_WARNING
    assert "Policy Engine approval" in LNURL_WITHDRAW_SECURITY_WARNING
    assert "untrusted metadata" in LNURL_COMMENT_SECURITY_WARNING
    for field in {"seed", "mnemonic", "private_key", "bitcoin_seed", "xprv", "linking_private_key"}:
        assert field in LNURL_FORBIDDEN_SECRET_FIELDS


def test_settlement_evidence_uses_fingerprints_and_safe_errors_do_not_echo_secrets():
    evidence = LNURLSettlementEvidence(
        status=LNURLVerifyStatus.SETTLED,
        verification_method=LNURLPaymentVerificationMethod.LNURL_VERIFY,
        payment_hash_fingerprint="sha256:" + "a" * 64,
        invoice_fingerprint="sha256:" + "b" * 64,
        preimage_fingerprint="sha256:" + "c" * 64,
        verified_at=datetime.now(UTC) + timedelta(seconds=1),
        limitations=("validated-by-test",),
    )
    assert evidence.status is LNURLVerifyStatus.SETTLED
    with pytest.raises(ValueError):
        LNURLSettlementEvidence(LNURLVerifyStatus.SETTLED, LNURLPaymentVerificationMethod.LNURL_VERIFY, "raw", "sha256:" + "b" * 64)
    error = UnsupportedLNURLTagError("raw k1 signature preimage seed xprv should not echo")
    assert "raw k1" not in str(error)
    assert "seed" not in str(error)
    assert str(InvalidLNURLStateTransitionError()) == "Invalid LNURL state transition."
    assert str(LightningAddressInvalidError("raw invoice private key")) == "Lightning Address is invalid."


def test_domain_package_import_is_pure_without_runtime_dependencies():
    module = importlib.import_module("app.domain.lnurl")
    assert module.LNURLTag.LOGIN.value == "login"
    imported_names = set(module.__all__)
    assert "LNURLTag" in imported_names
    assert "LightningPrincipalIdentity" in imported_names
    assert "LNURLDomainPolicy" in imported_names
