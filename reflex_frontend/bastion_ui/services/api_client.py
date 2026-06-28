from __future__ import annotations

from typing import Any, Literal

import httpx

from bastion_ui.config import AppConfig, get_config
from bastion_ui.services.errors import (
    CONNECTION_PUBLIC_MESSAGE,
    TIMEOUT_PUBLIC_MESSAGE,
    BastionApiConnectionError,
    BastionApiError,
    BastionApiTimeoutError,
    BastionApiUnavailableError,
    error_for_status,
)

HttpMethod = Literal["GET", "POST", "PATCH", "DELETE"]


class BastionApiClient:
    """Async API client for Reflex state methods.

    The client delegates domain behavior to FastAPI and only normalizes transport,
    envelope, timeout, and display-safe error behavior.
    """

    def __init__(
        self,
        config: AppConfig | None = None,
        *,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self.config = config or get_config()
        self._transport = transport

    @property
    def base_url(self) -> str:
        return self.config.api_base_url.rstrip("/")

    def build_url(self, path: str) -> str:
        normalized_path = path if path.startswith("/") else f"/{path}"
        return f"{self.base_url}{normalized_path}"

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
        method: HttpMethod,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
    ) -> Any:
        url = self.build_url(path)
        try:
            async with httpx.AsyncClient(
                timeout=self.config.request_timeout_seconds,
                transport=self._transport,
            ) as client:
                response = await client.request(method, url, params=params, json=json)
            return self._handle_response(response)
        except BastionApiError:
            raise
        except httpx.TimeoutException as exc:
            raise BastionApiTimeoutError(
                "Backend request timed out.",
                public_message=TIMEOUT_PUBLIC_MESSAGE,
            ) from exc
        except httpx.ConnectError as exc:
            raise BastionApiConnectionError(
                "Backend connection failed.",
                public_message=CONNECTION_PUBLIC_MESSAGE,
            ) from exc
        except httpx.TransportError as exc:
            raise BastionApiConnectionError(
                "Backend transport failed.",
                public_message=CONNECTION_PUBLIC_MESSAGE,
            ) from exc

    def _handle_response(self, response: httpx.Response) -> Any:
        request_id = response.headers.get("x-request-id")
        if response.status_code == 204:
            return None
        if response.is_error:
            details = self._safe_json_or_none(response)
            message = self._extract_error_message(details) or f"HTTP {response.status_code}"
            raise error_for_status(
                response.status_code,
                message=message,
                details=details,
                request_id=request_id,
            )
        payload = self._safe_json_or_error(response, request_id=request_id)
        return self._unwrap_response_envelope(payload, request_id=request_id)

    def _safe_json_or_none(self, response: httpx.Response) -> Any | None:
        try:
            return response.json()
        except ValueError:
            return None

    def _safe_json_or_error(self, response: httpx.Response, *, request_id: str | None) -> Any:
        try:
            return response.json()
        except ValueError as exc:
            raise BastionApiUnavailableError(
                "Backend returned a non-JSON response.",
                public_message="Bitcoin Bastion is temporarily unavailable.",
                status_code=response.status_code,
                request_id=request_id,
            ) from exc

    def _unwrap_response_envelope(self, payload: Any, *, request_id: str | None = None) -> Any:
        if isinstance(payload, dict):
            error = payload.get("error")
            if error is not None:
                message = self._extract_error_message(error) or "Backend returned an error."
                raise BastionApiError(
                    message,
                    public_message="Bitcoin Bastion is temporarily unavailable.",
                    details=error,
                    request_id=request_id,
                )
            if "data" in payload:
                return payload["data"]
        return payload

    def _extract_error_message(self, payload: Any) -> str | None:
        if isinstance(payload, str):
            return payload
        if isinstance(payload, dict):
            for key in ("message", "detail", "error"):
                value = payload.get(key)
                if isinstance(value, str):
                    return value
        return None


async def get(path: str) -> Any:
    return await BastionApiClient().get(path)
