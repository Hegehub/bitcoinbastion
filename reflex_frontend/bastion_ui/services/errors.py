from __future__ import annotations

from typing import Any


class BastionFrontendError(Exception):
    """Base frontend-safe error."""


class BastionApiError(BastionFrontendError):
    """Normalized API error safe for UI display."""

    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
        public_message: str | None = None,
        details: Any | None = None,
        request_id: str | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.message = message
        self.public_message = public_message or message
        self.details = details
        self.request_id = request_id


class BastionApiTimeoutError(BastionApiError):
    pass


class BastionApiConnectionError(BastionApiError):
    pass


class BastionApiValidationError(BastionApiError):
    pass


class BastionApiNotFoundError(BastionApiError):
    pass


class BastionApiRateLimitError(BastionApiError):
    pass


class BastionApiUnavailableError(BastionApiError):
    pass


VALIDATION_PUBLIC_MESSAGE = "The request could not be processed. Check the input and try again."
NOT_FOUND_PUBLIC_MESSAGE = "The requested resource was not found."
RATE_LIMIT_PUBLIC_MESSAGE = "Too many requests. Wait briefly and try again."
UNAVAILABLE_PUBLIC_MESSAGE = "Bitcoin Bastion is temporarily unavailable."
TIMEOUT_PUBLIC_MESSAGE = "The request timed out. Try again shortly."
CONNECTION_PUBLIC_MESSAGE = "Unable to reach Bitcoin Bastion backend."
INVALID_JSON_PUBLIC_MESSAGE = "Bitcoin Bastion returned an unreadable response."


def error_for_status(
    status_code: int,
    *,
    message: str | None = None,
    details: Any | None = None,
    request_id: str | None = None,
) -> BastionApiError:
    safe_message = message or f"Backend request failed with status {status_code}."
    if status_code in {400, 422}:
        return BastionApiValidationError(
            safe_message,
            status_code=status_code,
            public_message=VALIDATION_PUBLIC_MESSAGE,
            details=details,
            request_id=request_id,
        )
    if status_code == 404:
        return BastionApiNotFoundError(
            safe_message,
            status_code=status_code,
            public_message=NOT_FOUND_PUBLIC_MESSAGE,
            details=details,
            request_id=request_id,
        )
    if status_code == 429:
        return BastionApiRateLimitError(
            safe_message,
            status_code=status_code,
            public_message=RATE_LIMIT_PUBLIC_MESSAGE,
            details=details,
            request_id=request_id,
        )
    if status_code >= 500:
        return BastionApiUnavailableError(
            safe_message,
            status_code=status_code,
            public_message=UNAVAILABLE_PUBLIC_MESSAGE,
            details=details,
            request_id=request_id,
        )
    return BastionApiError(
        safe_message,
        status_code=status_code,
        public_message=UNAVAILABLE_PUBLIC_MESSAGE,
        details=details,
        request_id=request_id,
    )
