from __future__ import annotations

from typing import Any

import httpx
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class ApiClientError(RuntimeError):
    """Normalized API client error safe for public UI display."""


class ApiSettings(BaseSettings):
    """Environment-driven settings for the experimental frontend API client."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    api_base_url: str = Field(default="http://localhost:8000", alias="BB_API_BASE_URL")
    request_timeout_seconds: float = Field(default=5.0, alias="BB_REQUEST_TIMEOUT_SECONDS")


INVALID_INPUT_MESSAGE = "Input is invalid. Please review and retry."
NOT_FOUND_MESSAGE = "Requested data was not found."
RATE_LIMIT_MESSAGE = "Too many requests. Please wait and try again."
TIMEOUT_MESSAGE = "Request timed out. Please retry."
FALLBACK_MESSAGE = "Service is temporarily unavailable. Please retry shortly."


def _normalize_http_status(status_code: int) -> str:
    if status_code in {400, 422}:
        return INVALID_INPUT_MESSAGE
    if status_code == 404:
        return NOT_FOUND_MESSAGE
    if status_code == 429:
        return RATE_LIMIT_MESSAGE
    return FALLBACK_MESSAGE


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


def _unwrap_response_envelope(payload: Any) -> Any:
    if isinstance(payload, dict) and "data" in payload:
        return payload["data"]
    return payload


async def _request(method: str, path: str, payload: dict[str, Any] | None = None) -> Any:
    settings = ApiSettings()
    normalized_path = path if path.startswith("/") else f"/{path}"
    url = f"{settings.api_base_url.rstrip('/')}{normalized_path}"
    try:
        async with httpx.AsyncClient(timeout=settings.request_timeout_seconds) as client:
            response = await client.request(method, url, json=payload)
    except Exception as exc:
        raise ApiClientError(normalize_api_error(exc)) from exc
    if response.status_code >= 400:
        raise ApiClientError(_normalize_http_status(response.status_code))
    try:
        return _unwrap_response_envelope(response.json())
    except ValueError as exc:
        raise ApiClientError(FALLBACK_MESSAGE) from exc


async def api_get(path: str) -> Any:
    return await _request("GET", path)


async def api_post(path: str, payload: dict[str, Any]) -> Any:
    return await _request("POST", path, payload)
