"""Log-safe wallet auth domain exceptions."""

from __future__ import annotations


class WalletAuthDomainError(Exception):
    """Base class for wallet auth domain errors with safe messages."""

    default_message = "Wallet auth domain error."

    def __init__(self, message: str | None = None) -> None:
        super().__init__(message or self.default_message)


class UnsupportedWalletNetworkError(WalletAuthDomainError):
    default_message = "Unsupported wallet network."


class UnsupportedWalletProofTypeError(WalletAuthDomainError):
    default_message = "Unsupported wallet proof type."


class WalletProofTooWeakError(WalletAuthDomainError):
    default_message = "Wallet proof is too weak for the requested action."


class WalletPrincipalRevokedError(WalletAuthDomainError):
    default_message = "Wallet principal is revoked."


class WalletPrincipalSuspendedError(WalletAuthDomainError):
    default_message = "Wallet principal is suspended."


class WalletDeviceRevokedError(WalletAuthDomainError):
    default_message = "Wallet device is revoked."


class WalletSessionInvalidError(WalletAuthDomainError):
    default_message = "Wallet session is invalid."


class WalletActionRequiresStepUpError(WalletAuthDomainError):
    default_message = "Wallet action requires step-up verification."


class WalletRecoveryNotAllowedError(WalletAuthDomainError):
    default_message = "Wallet recovery is not allowed for this request."


class WalletSecretInputForbiddenError(WalletAuthDomainError):
    default_message = "Wallet secret input is forbidden."
