from __future__ import annotations

from typing import Any

import httpx

from bastion_ui.services.settings import Settings, get_settings

INVALID_INPUT_MESSAGE = "Input is invalid. Please review and retry."
NOT_FOUND_MESSAGE = "Requested data was not found."
RATE_LIMIT_MESSAGE = "Too many requests. Please wait and try again."
TIMEOUT_MESSAGE = "Request timed out. Please retry."
FALLBACK_MESSAGE = "Service is temporarily unavailable. Please retry shortly."


class ApiClientError(RuntimeError):
    """Normalized API client error safe for public UI display."""


def normalize_api_error(exc: Exception) -> str:
    if isinstance(exc, ApiClientError):
        return str(exc)
    if isinstance(exc, httpx.TimeoutException):
        return TIMEOUT_MESSAGE
    if isinstance(exc, httpx.HTTPStatusError):
        return _normalize_http_status(exc.response.status_code)
    if isinstance(exc, httpx.HTTPError):
        return FALLBACK_MESSAGE
    return FALLBACK_MESSAGE


def _normalize_http_status(status_code: int) -> str:
    if status_code in {400, 422}:
        return INVALID_INPUT_MESSAGE
    if status_code == 404:
        return NOT_FOUND_MESSAGE
    if status_code == 429:
        return RATE_LIMIT_MESSAGE
    return FALLBACK_MESSAGE


def _unwrap_response_envelope(payload: Any) -> Any:
    if isinstance(payload, dict) and "data" in payload:
        return payload["data"]
    return payload


class ApiClient:
    """Minimal async API foundation for later route-specific Reflex clients."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    async def get(self, path: str) -> Any:
        normalized_path = path if path.startswith("/") else f"/{path}"
        url = f"{self.settings.api_base_url.rstrip('/')}{normalized_path}"
        try:
            async with httpx.AsyncClient(timeout=self.settings.request_timeout_seconds) as client:
                response = await client.get(url)
                response.raise_for_status()
                return _unwrap_response_envelope(response.json())
        except Exception as exc:
            raise ApiClientError(normalize_api_error(exc)) from exc


async def get(path: str) -> Any:
    """Convenience wrapper for scaffold tests and later clients."""

    return await ApiClient().get(path)
