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
)


def exit_with_error(exc: Exception, *, debug: bool = False) -> NoReturn:
    console = Console(stderr=True)
    message = _safe_error_message(exc)
    console.print(f"Error: {message}")
    if debug:
        console.print_exception(show_locals=False)
    raise typer.Exit(1)


def _safe_error_message(exc: Exception) -> str:
    if isinstance(exc, BastionValidationError):
        return "Invalid input. Review the request and retry."
    if isinstance(exc, BastionAuthError):
        return "Authentication failed or insufficient permission."
    if isinstance(exc, BastionNotFoundError):
        return "Requested resource was not found."
    if isinstance(exc, BastionRateLimitError):
        return "Too many requests. Retry later."
    if isinstance(exc, BastionTimeoutError):
        return "Request timed out. Retry later."
    if isinstance(exc, BastionConnectionError):
        return "API unavailable. Check BB_API_BASE_URL."
    if isinstance(exc, BastionSafetyError):
        return str(exc)
    if isinstance(exc, BastionAPIError):
        return "Bitcoin Bastion API request failed."
    return "Command failed."
