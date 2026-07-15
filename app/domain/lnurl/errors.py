"""Log-safe LNURL domain exceptions."""

from __future__ import annotations

_FORBIDDEN_ECHO_TERMS = ("seed", "mnemonic", "xprv", "private", "signature", "preimage", "invoice", "k1", "linking")


class LNURLDomainError(Exception):
    default_message = "LNURL domain error."

    def __init__(self, message: str | None = None, *, safe_reference: str | None = None) -> None:
        safe_message = self.default_message if message is None or _looks_sensitive(message) else message
        if safe_reference:
            safe_message = f"{safe_message} reference={safe_reference}"
        super().__init__(safe_message)


class UnsupportedLNURLTagError(LNURLDomainError):
    default_message = "Unsupported LNURL tag."


class UnsupportedLNURLActionError(LNURLDomainError):
    default_message = "Unsupported LNURL action."


class InvalidLNURLStateTransitionError(LNURLDomainError):
    default_message = "Invalid LNURL state transition."


class InvalidLNURLDomainError(LNURLDomainError):
    default_message = "Invalid LNURL domain."


class InsecureLNURLTransportError(LNURLDomainError):
    default_message = "Insecure LNURL transport."


class LNURLK1InvalidError(LNURLDomainError):
    default_message = "Invalid LNURL k1 challenge."


class LNURLK1ExpiredError(LNURLDomainError):
    default_message = "LNURL k1 challenge expired."


class LNURLK1ReusedError(LNURLDomainError):
    default_message = "LNURL k1 replay rejected."


class LNURLAuthProofInvalidError(LNURLDomainError):
    default_message = "LNURL-auth proof is invalid."


class LNURLPaymentNotSettledError(LNURLDomainError):
    default_message = "LNURL payment is not settled."


class LNURLPaymentVerificationError(LNURLDomainError):
    default_message = "LNURL payment verification failed."


class LNURLWithdrawNotAuthorizedError(LNURLDomainError):
    default_message = "LNURL-withdraw is not authorized."


class LNURLWithdrawExpiredError(LNURLDomainError):
    default_message = "LNURL-withdraw request expired."


class LNURLPayerDataRejectedError(LNURLDomainError):
    default_message = "LNURL payerData rejected."


class LNURLCommentRejectedError(LNURLDomainError):
    default_message = "LNURL comment rejected."


class LNURLSuccessActionRejectedError(LNURLDomainError):
    default_message = "LNURL successAction rejected."


class LightningAddressInvalidError(LNURLDomainError):
    default_message = "Lightning Address is invalid."


class LightningPrincipalRevokedError(LNURLDomainError):
    default_message = "Lightning Principal is revoked."


class LNURLSecretInputForbiddenError(LNURLDomainError):
    default_message = "LNURL secret input is forbidden."


# Backward-compatible aliases.
LNURLInvalidTagError = UnsupportedLNURLTagError
LNURLInvalidActionError = UnsupportedLNURLActionError
LNURLInvalidK1Error = LNURLK1InvalidError
LNURLK1ReplayError = LNURLK1ReusedError
LNURLAuthSignatureInvalidError = LNURLAuthProofInvalidError
LNURLWithdrawPolicyRequiredError = LNURLWithdrawNotAuthorizedError
LNURLPayerDataPrivacyError = LNURLPayerDataRejectedError
LNURLSuccessActionUnsafeError = LNURLSuccessActionRejectedError
LightningAddressNotIdentityError = LightningAddressInvalidError


def _looks_sensitive(message: str) -> bool:
    lowered = message.lower()
    return any(term in lowered for term in _FORBIDDEN_ECHO_TERMS)
