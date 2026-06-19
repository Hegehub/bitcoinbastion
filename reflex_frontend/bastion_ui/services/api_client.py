from __future__ import annotations

from typing import Any, cast

import httpx

from bastion_ui.config import Settings, get_settings
from bastion_ui.security.safe_logging import redact_payload, safe_error_message
from bastion_ui.services.errors import (
    CONNECTION_PUBLIC_MESSAGE,
    INVALID_JSON_PUBLIC_MESSAGE,
    TIMEOUT_PUBLIC_MESSAGE,
    BastionApiConnectionError,
    BastionApiError,
    BastionApiTimeoutError,
    error_for_status,
)


class ApiClientError(BastionApiError):
    """Backward-compatible alias for older scaffold tests."""


def _extract_request_id(response: httpx.Response) -> str | None:
    return cast(
        str | None, response.headers.get("x-request-id") or response.headers.get("x-correlation-id")
    )


def _extract_error_message(payload: Any) -> str | None:
    if isinstance(payload, dict):
        error = payload.get("error")
        if isinstance(error, str):
            return error
        if isinstance(error, dict):
            message = error.get("message") or error.get("detail")
            if isinstance(message, str):
                return message
        detail = payload.get("detail")
        if isinstance(detail, str):
            return detail
    return None


def unwrap_response_envelope(payload: Any) -> Any:
    if isinstance(payload, dict):
        error = payload.get("error")
        if error is not None:
            message = _extract_error_message(payload) or "Backend returned an error envelope."
            raise BastionApiError(message, public_message=message, details=redact_payload(error))
        if "data" in payload:
            return payload["data"]
    return payload


def normalize_api_error(exc: Exception) -> BastionApiError:
    if isinstance(exc, BastionApiError):
        return exc
    if isinstance(exc, httpx.TimeoutException):
        return BastionApiTimeoutError(
            safe_error_message(exc), public_message=TIMEOUT_PUBLIC_MESSAGE
        )
    if isinstance(exc, httpx.ConnectError | httpx.NetworkError):
        return BastionApiConnectionError(
            safe_error_message(exc), public_message=CONNECTION_PUBLIC_MESSAGE
        )
    if isinstance(exc, httpx.HTTPStatusError):
        response = exc.response
        details: Any | None = None
        message: str | None = None
        try:
            details = redact_payload(response.json())
            message = _extract_error_message(details)
        except ValueError:
            details = None
        return error_for_status(
            response.status_code,
            message=message,
            details=details,
            request_id=_extract_request_id(response),
        )
    if isinstance(exc, httpx.HTTPError):
        return BastionApiConnectionError(
            safe_error_message(exc), public_message=CONNECTION_PUBLIC_MESSAGE
        )
    return BastionApiError(safe_error_message(exc), public_message=INVALID_JSON_PUBLIC_MESSAGE)


class BastionApiClient:
    """Async API client foundation for Reflex state methods and service clients."""

    def __init__(
        self,
        settings: Settings | None = None,
        *,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self._transport = transport

    def build_url(self, path: str) -> str:
        normalized_path = path if path.startswith("/") else f"/{path}"
        return f"{self.settings.api_base_url}{normalized_path}"

    async def get(self, path: str, *, params: dict[str, Any] | None = None) -> Any:
        return await self._request("GET", path, params=params)

    async def post(self, path: str, *, json: dict[str, Any] | None = None) -> Any:
        return await self._request("POST", path, json=json)

    async def patch(self, path: str, *, json: dict[str, Any] | None = None) -> Any:
        return await self._request("PATCH", path, json=json)

    async def delete(self, path: str) -> Any:
        return await self._request("DELETE", path)

    async def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
    ) -> Any:
        url = self.build_url(path)
        safe_json = redact_payload(json) if json is not None else None
        try:
            async with httpx.AsyncClient(
                timeout=self.settings.request_timeout_seconds,
                transport=self._transport,
            ) as client:
                response = await client.request(method, url, params=params, json=json)
                if response.status_code == 204:
                    return None
                response.raise_for_status()
                try:
                    payload = response.json()
                except ValueError as exc:
                    raise BastionApiError(
                        "Backend response was not JSON.",
                        status_code=response.status_code,
                        public_message=INVALID_JSON_PUBLIC_MESSAGE,
                        request_id=_extract_request_id(response),
                    ) from exc
                return unwrap_response_envelope(payload)
        except Exception as exc:
            normalized = normalize_api_error(exc)
            normalized.details = normalized.details or {
                "method": method,
                "path": path,
                "json": safe_json,
            }
            raise normalized from exc


ApiClient = BastionApiClient


async def get(path: str) -> Any:
    return await BastionApiClient().get(path)
