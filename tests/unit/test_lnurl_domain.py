from app.domain.lnurl import (
    DEFAULT_ALLOWED_PAYERDATA_FIELDS,
    LIGHTNING_ADDRESS_NOT_IDENTITY_WARNING,
    LNURL_AUTH_ALLOWED_ACTIONS,
    LNURL_K1_BYTES,
    LNURLAdapterType,
    LNURLAuthAction,
    LNURLAuthStatus,
    LNURLCommentPolicy,
    LNURLDomainError,
    LNURLK1ReplayError,
    LNURLK1Status,
    LNURLPayerDataField,
    LNURLPaymentStatus,
    LNURLSecurityLevel,
    LNURLSuccessActionType,
    LNURLSuccessActionUnsafeError,
    LNURLTag,
    LNURLVerifyStatus,
    LNURLWithdrawPurpose,
    LNURLWithdrawStatus,
    LightningAddressStatus,
    LightningAddressType,
    LightningPrincipalType,
    PRIVACY_SENSITIVE_PAYERDATA_FIELDS,
)


def test_lnurl_tags_and_adapters_are_stable() -> None:
    assert LNURLTag.LOGIN.value == "login"
    assert LNURLTag.PAY_REQUEST.value == "payRequest"
    assert LNURLTag.WITHDRAW_REQUEST.value == "withdrawRequest"
    assert LNURLAdapterType.LNURL_AUTH.value == "lnurl_auth"
    assert LNURLAdapterType.LNURL_PAY.value == "lnurl_pay"


def test_lnurl_auth_actions_and_statuses() -> None:
    assert LNURL_AUTH_ALLOWED_ACTIONS == {
        LNURLAuthAction.REGISTER,
        LNURLAuthAction.LOGIN,
        LNURLAuthAction.LINK,
        LNURLAuthAction.AUTH,
    }
    assert LNURLAuthAction.AUTH.value == "auth"
    assert LNURLAuthStatus.CHALLENGE_CREATED.value == "challenge_created"
    assert LNURLAuthStatus.VERIFIED.value == "verified"


def test_k1_security_constants_and_statuses() -> None:
    assert LNURL_K1_BYTES == 32
    assert LNURLK1Status.UNUSED.value == "unused"
    assert LNURLK1Status.USED.value == "used"
    assert LNURLK1Status.EXPIRED.value == "expired"
    assert LNURLK1Status.REPLAY_REJECTED.value == "replay_rejected"
    assert "raw-k1" not in str(LNURLK1ReplayError()).lower()


def test_lnurl_pay_statuses_separate_invoice_settlement_and_entitlement() -> None:
    assert LNURLPaymentStatus.INVOICE_ISSUED.value == "invoice_issued"
    assert LNURLPaymentStatus.SETTLED.value == "settled"
    assert LNURLPaymentStatus.INVOICE_ISSUED is not LNURLPaymentStatus.SETTLED
    assert LNURLPaymentStatus.ENTITLEMENT_ISSUED.value == "entitlement_issued"


def test_lnurl_verify_statuses_support_settlement_fallbacks() -> None:
    assert LNURLVerifyStatus.SETTLED_TRUE.value == "settled_true"
    assert LNURLVerifyStatus.SETTLED_FALSE.value == "settled_false"
    assert LNURLVerifyStatus.NOT_AVAILABLE.value == "not_available"


def test_lnurl_withdraw_states_and_purposes() -> None:
    ordered_statuses = list(LNURLWithdrawStatus)
    assert LNURLWithdrawStatus.POLICY_PENDING in ordered_statuses
    assert LNURLWithdrawStatus.POLICY_APPROVED in ordered_statuses
    assert ordered_statuses.index(LNURLWithdrawStatus.POLICY_APPROVED) < ordered_statuses.index(LNURLWithdrawStatus.QR_ISSUED)
    assert LNURLWithdrawPurpose.SUBSCRIPTION_REFUND.value == "subscription_refund"
    assert LNURLWithdrawPurpose.PAYREGISTER_REFUND.value == "payregister_refund"


def test_lightning_address_is_payment_routing_not_identity() -> None:
    assert LightningAddressType.PRODUCT.value == "product"
    assert LightningAddressType.MERCHANT.value == "merchant"
    assert LightningAddressStatus.DOMAIN_VERIFIED.value == "domain_verified"
    assert "not identity" in LIGHTNING_ADDRESS_NOT_IDENTITY_WARNING


def test_payerdata_defaults_are_privacy_first() -> None:
    assert DEFAULT_ALLOWED_PAYERDATA_FIELDS == [LNURLPayerDataField.AUTH.value]
    assert LNURLPayerDataField.EMAIL.value in PRIVACY_SENSITIVE_PAYERDATA_FIELDS
    assert LNURLPayerDataField.NAME.value in PRIVACY_SENSITIVE_PAYERDATA_FIELDS
    assert LNURLPayerDataField.IDENTIFIER.value in PRIVACY_SENSITIVE_PAYERDATA_FIELDS
    assert LNURLPayerDataField.EMAIL.value not in DEFAULT_ALLOWED_PAYERDATA_FIELDS


def test_success_action_comment_policy_principals_and_security_levels() -> None:
    assert LNURLSuccessActionType.MESSAGE.value == "message"
    assert LNURLSuccessActionType.URL.value == "url"
    assert "session" not in str(LNURLSuccessActionUnsafeError()).lower()
    assert LNURLCommentPolicy.DISABLED.value == "disabled"
    assert LNURLCommentPolicy.ALLOWED_UNTRUSTED.value == "allowed_untrusted"
    assert LNURLCommentPolicy.ALLOWED_RECEIPT_ONLY.value == "allowed_receipt_only"
    assert LightningPrincipalType.LNURL_AUTH_PRINCIPAL.value == "lnurl_auth_principal"
    assert LightningPrincipalType.LIGHTNING_ADDRESS_PRINCIPAL.value == "lightning_address_principal"
    assert LightningPrincipalType.PAYERDATA_AUTH_PRINCIPAL.value == "payerdata_auth_principal"
    assert {level.value for level in LNURLSecurityLevel} == {
        "compatibility",
        "standard",
        "high_assurance",
        "business",
        "sovereign",
    }


def test_lnurl_domain_errors_are_safe_for_logs() -> None:
    for error in (LNURLDomainError(), LNURLK1ReplayError(), LNURLSuccessActionUnsafeError()):
        message = str(error).lower()
        assert message
        for secret_like in ("raw_k1", "raw signature", "lnurl key", "session-token", "access pass", "seed", "private key"):
            assert secret_like not in message
