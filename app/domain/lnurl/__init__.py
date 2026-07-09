"""Pure LNURL domain primitives."""

from app.domain.lnurl.address import LightningAddressStatus, LightningAddressType
from app.domain.lnurl.auth import LNURL_AUTH_ALLOWED_ACTIONS, LNURLAuthAction, LNURLAuthStatus
from app.domain.lnurl.constants import (
    LIGHTNING_ADDRESS_NOT_IDENTITY_WARNING,
    LNURL_AUTH_DEFAULT_TTL_SECONDS,
    LNURL_AUTH_STABLE_DOMAIN_WARNING,
    LNURL_INVOICE_NOT_SETTLED_WARNING,
    LNURL_K1_BYTES,
    LNURL_PAY_DEFAULT_TTL_SECONDS,
    LNURL_PAYERDATA_PRIVACY_WARNING,
    LNURL_WITHDRAW_AUTH_REQUIRED_WARNING,
    LNURL_WITHDRAW_DEFAULT_TTL_SECONDS,
)
from app.domain.lnurl.errors import (
    LNURLAuthSignatureInvalidError,
    LNURLDomainError,
    LNURLInvalidActionError,
    LNURLInvalidK1Error,
    LNURLInvalidTagError,
    LNURLK1ExpiredError,
    LNURLK1ReplayError,
    LNURLPayerDataPrivacyError,
    LNURLPaymentNotSettledError,
    LNURLSuccessActionUnsafeError,
    LNURLWithdrawPolicyRequiredError,
    LightningAddressNotIdentityError,
)
from app.domain.lnurl.pay import LNURLPaymentPurpose, LNURLPaymentStatus
from app.domain.lnurl.payer_data import (
    DEFAULT_ALLOWED_PAYERDATA_FIELDS,
    PRIVACY_SENSITIVE_PAYERDATA_FIELDS,
    LNURLCommentPolicy,
    LNURLPayerDataField,
)
from app.domain.lnurl.principals import LightningPrincipalType
from app.domain.lnurl.security import LNURLK1Status, LNURLSecurityLevel
from app.domain.lnurl.success_action import LNURLSuccessActionType
from app.domain.lnurl.tags import LNURLAdapterType, LNURLTag
from app.domain.lnurl.verify import LNURLVerifyStatus
from app.domain.lnurl.withdraw import LNURLWithdrawPurpose, LNURLWithdrawStatus

__all__ = [
    "DEFAULT_ALLOWED_PAYERDATA_FIELDS",
    "LIGHTNING_ADDRESS_NOT_IDENTITY_WARNING",
    "LNURL_AUTH_ALLOWED_ACTIONS",
    "LNURL_AUTH_DEFAULT_TTL_SECONDS",
    "LNURL_AUTH_STABLE_DOMAIN_WARNING",
    "LNURL_INVOICE_NOT_SETTLED_WARNING",
    "LNURL_K1_BYTES",
    "LNURL_PAY_DEFAULT_TTL_SECONDS",
    "LNURL_PAYERDATA_PRIVACY_WARNING",
    "LNURL_WITHDRAW_AUTH_REQUIRED_WARNING",
    "LNURL_WITHDRAW_DEFAULT_TTL_SECONDS",
    "LNURLAdapterType",
    "LNURLAuthAction",
    "LNURLAuthSignatureInvalidError",
    "LNURLAuthStatus",
    "LNURLCommentPolicy",
    "LNURLDomainError",
    "LNURLInvalidActionError",
    "LNURLInvalidK1Error",
    "LNURLInvalidTagError",
    "LNURLK1ExpiredError",
    "LNURLK1ReplayError",
    "LNURLK1Status",
    "LNURLPayerDataField",
    "LNURLPayerDataPrivacyError",
    "LNURLPaymentNotSettledError",
    "LNURLPaymentPurpose",
    "LNURLPaymentStatus",
    "LNURLSecurityLevel",
    "LNURLSuccessActionType",
    "LNURLSuccessActionUnsafeError",
    "LNURLTag",
    "LNURLVerifyStatus",
    "LNURLWithdrawPolicyRequiredError",
    "LNURLWithdrawPurpose",
    "LNURLWithdrawStatus",
    "LightningAddressNotIdentityError",
    "LightningAddressStatus",
    "LightningAddressType",
    "LightningPrincipalType",
    "PRIVACY_SENSITIVE_PAYERDATA_FIELDS",
]
