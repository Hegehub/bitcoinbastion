from __future__ import annotations

from typing import Any


class BastionSDKError(Exception):
    """Base SDK exception."""


class BastionAPIError(BastionSDKError):
    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
        error_code: str | None = None,
        request_id: str | None = None,
        payload: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.request_id = request_id
        self.payload = payload or {}


class BastionAuthError(BastionAPIError):
    pass


class BastionAccessError(BastionSDKError):
    pass


class BastionAccessSessionExpired(BastionAccessError):
    pass


class BastionAccessSignatureError(BastionAccessError):
    pass


class BastionAccessChallengeExpired(BastionAccessError):
    pass


class BastionAccessPolicyDenied(BastionAccessError):
    pass


class BastionAccessUpgradeRequired(BastionAccessError):
    pass


class BastionAccessRevoked(BastionAccessError):
    pass


class BastionLegacyAuthDisabled(BastionAccessError):
    pass


class BastionNotFoundError(BastionAPIError):
    pass


class BastionValidationError(BastionAPIError):
    pass


class BastionRateLimitError(BastionAPIError):
    pass


class BastionTimeoutError(BastionSDKError):
    pass


class BastionConnectionError(BastionSDKError):
    pass


class BastionWebSocketError(BastionSDKError):
    pass


class BastionSafetyError(BastionSDKError):
    pass


class BastionPolicyError(BastionAPIError):
    """Structured Policy Engine denial."""


class BastionUpgradeRequiredError(BastionPolicyError): ...
class BastionStepUpRequiredError(BastionPolicyError): ...
class BastionQuotaExceededError(BastionPolicyError): ...
class BastionRevokedError(BastionPolicyError): ...
class BastionRecoveryRequiredError(BastionPolicyError): ...
class WalletProofError(BastionAuthError): ...
class WalletProofTooWeakError(WalletProofError): ...
class DeviceBindingError(BastionAuthError): ...
class SessionExpiredError(BastionAuthError): ...
class BastionLNURLError(BastionAPIError): ...
class LNURLDecodeError(BastionLNURLError): ...
class LNURLDomainMismatchError(BastionLNURLError): ...
class LNURLChallengeExpiredError(BastionLNURLError): ...
class LNURLChallengeUsedError(BastionLNURLError): ...
class LNURLInvalidK1Error(BastionLNURLError): ...
class LNURLPaymentError(BastionLNURLError): ...
class LNURLPaymentNotSettledError(LNURLPaymentError): ...
class LNURLWithdrawError(BastionLNURLError): ...
class BastionRecoveryError(BastionAPIError): ...


class BitcoinWalletSecretForbiddenError(BastionSafetyError):
    def __init__(self) -> None:
        super().__init__(
            "Bitcoin Bastion rejects wallet secrets: never submit your Bitcoin wallet seed "
            "or private key for authentication or recovery."
        )
