"""Safe LNURL-pay subscription request errors."""

from __future__ import annotations


class LNURLPayRequestError(ValueError):
    reason_code = "lnurl_pay_request_error"
    public_message = "LNURL payment request could not be created."


class LNURLPayDisabledError(LNURLPayRequestError):
    reason_code = "lnurl_pay_disabled"


class LNURLPayUnknownPlanError(LNURLPayRequestError):
    reason_code = "lnurl_pay_unknown_plan"


class LNURLPayPlanUnavailableError(LNURLPayRequestError):
    reason_code = "lnurl_pay_plan_unavailable"


class LNURLPayInvalidAmountError(LNURLPayRequestError):
    reason_code = "lnurl_pay_invalid_amount"


class LNURLPayInvalidRangeError(LNURLPayRequestError):
    reason_code = "lnurl_pay_invalid_range"


class LNURLPayPricingExpiredError(LNURLPayRequestError):
    reason_code = "lnurl_pay_pricing_expired"


class LNURLPayMetadataError(LNURLPayRequestError):
    reason_code = "lnurl_pay_metadata_error"


class LNURLPayUnsafeCallbackError(LNURLPayRequestError):
    reason_code = "lnurl_pay_unsafe_callback"


class LNURLPayPrincipalUnavailableError(LNURLPayRequestError):
    reason_code = "lnurl_pay_principal_unavailable"


class LNURLPayAnonymousCheckoutDeniedError(LNURLPayRequestError):
    reason_code = "lnurl_pay_anonymous_checkout_denied"


class LNURLPayIdempotencyConflictError(LNURLPayRequestError):
    reason_code = "lnurl_pay_idempotency_conflict"


class LNURLPayRequestPersistenceError(LNURLPayRequestError):
    reason_code = "lnurl_pay_request_persistence_error"


class LNURLPayPolicyDeniedError(LNURLPayRequestError):
    reason_code = "lnurl_pay_policy_denied"
