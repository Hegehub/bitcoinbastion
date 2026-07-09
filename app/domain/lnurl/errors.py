"""Log-safe LNURL domain exceptions."""

from __future__ import annotations


class LNURLDomainError(Exception):
    """Base class for LNURL domain errors with safe messages."""

    default_message = "LNURL domain error."

    def __init__(self, message: str | None = None) -> None:
        super().__init__(message or self.default_message)


class LNURLInvalidTagError(LNURLDomainError):
    default_message = "Invalid LNURL tag."


class LNURLInvalidActionError(LNURLDomainError):
    default_message = "Invalid LNURL action."


class LNURLInvalidK1Error(LNURLDomainError):
    default_message = "Invalid LNURL k1 challenge."


class LNURLK1ReplayError(LNURLDomainError):
    default_message = "LNURL k1 replay rejected."


class LNURLK1ExpiredError(LNURLDomainError):
    default_message = "LNURL k1 challenge expired."


class LNURLAuthSignatureInvalidError(LNURLDomainError):
    default_message = "LNURL-auth signature is invalid."


class LNURLPaymentNotSettledError(LNURLDomainError):
    default_message = "LNURL payment is not settled."


class LNURLWithdrawPolicyRequiredError(LNURLDomainError):
    default_message = "LNURL-withdraw requires policy approval."


class LNURLPayerDataPrivacyError(LNURLDomainError):
    default_message = "LNURL payerData violates privacy policy."


class LNURLSuccessActionUnsafeError(LNURLDomainError):
    default_message = "LNURL successAction is unsafe."


class LightningAddressNotIdentityError(LNURLDomainError):
    default_message = "Lightning Address is not an identity."
