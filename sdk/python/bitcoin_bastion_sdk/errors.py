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
