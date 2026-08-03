from __future__ import annotations

from typing import NoReturn

import typer
from rich.console import Console

from bitcoin_bastion_sdk.errors import (
    BastionAPIError,
    BastionAuthError,
    BastionConnectionError,
    BastionNotFoundError,
    BastionRateLimitError,
    BastionSafetyError,
    BastionTimeoutError,
    BastionValidationError,
    BastionStepUpRequiredError,
    BastionUpgradeRequiredError,
    BastionQuotaExceededError,
    BastionRevokedError,
    BastionRecoveryRequiredError,
    SessionExpiredError,
)


def exit_with_error(exc: Exception, *, debug: bool = False) -> NoReturn:
    console = Console(stderr=True)
    message = _safe_error_message(exc)
    console.print(f"Error: {message}")
    if debug:
        console.print_exception(show_locals=False)
    raise typer.Exit(_exit_code(exc))


def _exit_code(exc: Exception) -> int:
    if isinstance(exc, (BastionStepUpRequiredError,)):
        return 5
    if isinstance(exc, (BastionUpgradeRequiredError, BastionQuotaExceededError)):
        return 6
    if isinstance(exc, BastionRevokedError):
        return 7
    if isinstance(exc, SessionExpiredError):
        return 8
    if isinstance(exc, (BastionTimeoutError, BastionConnectionError)):
        return 9
    if isinstance(exc, BastionSafetyError):
        return 10
    if isinstance(exc, BastionRecoveryRequiredError):
        return 7
    if isinstance(exc, BastionAuthError):
        return 3
    if isinstance(exc, BastionAPIError) and exc.status_code in {401}:
        return 3
    if isinstance(exc, BastionAPIError) and exc.status_code in {403}:
        return 4
    return 1


def _safe_error_message(exc: Exception) -> str:
    if isinstance(exc, BastionValidationError):
        return "Invalid input. Review the request and retry."
    if isinstance(exc, BastionAuthError):
        return "Authentication failed or insufficient permission."
    if isinstance(exc, BastionStepUpRequiredError):
        return "STEP-UP REQUIRED: complete fresh wallet or LNURL proof."
    if isinstance(exc, BastionUpgradeRequiredError):
        return "UPGRADE REQUIRED: backend entitlement policy denied this operation."
    if isinstance(exc, BastionQuotaExceededError):
        return "QUOTA EXCEEDED: backend policy denied this operation."
    if isinstance(exc, BastionRevokedError):
        return "REVOKED: principal, device, or session is revoked."
    if isinstance(exc, BastionRecoveryRequiredError):
        return "RECOVERY REQUIRED: follow the backend Recovery Capsule flow."
    if isinstance(exc, SessionExpiredError):
        return "EXPIRED: establish a new Device-bound PoP Session."
    if isinstance(exc, BastionNotFoundError):
        return "Requested resource was not found."
    if isinstance(exc, BastionRateLimitError):
        return "Too many requests. Retry later."
    if isinstance(exc, BastionTimeoutError):
        return "Request timed out. Retry later."
    if isinstance(exc, BastionConnectionError):
        return "API unavailable. Check BB_API_BASE_URL."
    if isinstance(exc, BastionSafetyError):
        return f"Never submit seed phrases or private keys to Bitcoin Bastion. {exc}"
    if isinstance(exc, BastionAPIError):
        return "Bitcoin Bastion API request failed."
    return "Command failed."
