from __future__ import annotations

from typing import Any

import httpx

from bitcoin_bastion_sdk.auth import build_headers
from bitcoin_bastion_sdk.config import BastionSDKConfig
from bitcoin_bastion_sdk.errors import (
    BastionAPIError,
    BastionAuthError,
    BastionConnectionError,
    BastionNotFoundError,
    BastionRateLimitError,
    BastionTimeoutError,
    BastionValidationError,
)

JsonDict = dict[str, Any]


def _safe_payload(response: httpx.Response) -> JsonDict:
    try:
        payload = response.json()
    except ValueError:
        return {"message": response.text[:500]}
    return payload if isinstance(payload, dict) else {"data": payload}


def _message_from_payload(payload: JsonDict, default: str) -> str:
    error = payload.get("error")
    if isinstance(error, dict):
        message = error.get("message") or error.get("detail")
        if isinstance(message, str):
            return message
    detail = payload.get("detail")
    if isinstance(detail, str):
        return detail
    message = payload.get("message")
    return message if isinstance(message, str) else default


def _error_code(payload: JsonDict) -> str | None:
    error = payload.get("error")
    if isinstance(error, dict) and isinstance(error.get("code"), str):
        return str(error["code"])
    if isinstance(payload.get("code"), str):
        return str(payload["code"])
    return None


def _raise_for_status(response: httpx.Response) -> None:
    if response.status_code < 400:
        return
    payload = _safe_payload(response)
    message = _message_from_payload(payload, f"Bitcoin Bastion API error ({response.status_code})")
    kwargs = {
        "status_code": response.status_code,
        "error_code": _error_code(payload),
        "request_id": response.headers.get("x-request-id"),
        "payload": payload,
    }
    if response.status_code in {400, 422}:
        raise BastionValidationError(message, **kwargs)
    if response.status_code in {401, 403}:
        raise BastionAuthError(message, **kwargs)
    if response.status_code == 404:
        raise BastionNotFoundError(message, **kwargs)
    if response.status_code == 429:
        raise BastionRateLimitError(message, **kwargs)
    raise BastionAPIError(message, **kwargs)


def unwrap_response(response: httpx.Response, *, raw: bool = False) -> Any:
    _raise_for_status(response)
    if response.status_code == 204 or not response.content:
        return None
    payload = response.json()
    if raw:
        return payload
    if isinstance(payload, dict) and "error" in payload and payload.get("error") is not None:
        raise BastionAPIError(_message_from_payload(payload, "Bitcoin Bastion API error"), payload=payload)
    if isinstance(payload, dict) and "data" in payload and "error" in payload:
        return payload.get("data")
    return payload


class BastionTransport:
    def __init__(
        self,
        *,
        base_url: str,
        api_prefix: str = "/api/v1",
        api_key: str | None = None,
        timeout: float = 5.0,
        headers: dict[str, str] | None = None,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self.config = BastionSDKConfig(base_url=base_url, api_prefix=api_prefix, timeout=timeout)
        self.headers = build_headers(api_key, headers)
        self.client = httpx.Client(
            base_url=f"{self.config.base_url}{self.config.api_prefix}",
            timeout=timeout,
            headers=self.headers,
            transport=transport,
        )

    def request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json: JsonDict | None = None,
        raw: bool = False,
    ) -> Any:
        try:
            response = self.client.request(method, path, params=params, json=json)
        except httpx.TimeoutException as exc:
            raise BastionTimeoutError("Bitcoin Bastion request timed out") from exc
        except httpx.HTTPError as exc:
            raise BastionConnectionError("Bitcoin Bastion connection error") from exc
        return unwrap_response(response, raw=raw)

    def close(self) -> None:
        self.client.close()


class AsyncBastionTransport:
    def __init__(
        self,
        *,
        base_url: str,
        api_prefix: str = "/api/v1",
        api_key: str | None = None,
        timeout: float = 5.0,
        headers: dict[str, str] | None = None,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self.config = BastionSDKConfig(base_url=base_url, api_prefix=api_prefix, timeout=timeout)
        self.headers = build_headers(api_key, headers)
        self.client = httpx.AsyncClient(
            base_url=f"{self.config.base_url}{self.config.api_prefix}",
            timeout=timeout,
            headers=self.headers,
            transport=transport,
        )

    async def request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json: JsonDict | None = None,
        raw: bool = False,
    ) -> Any:
        try:
            response = await self.client.request(method, path, params=params, json=json)
        except httpx.TimeoutException as exc:
            raise BastionTimeoutError("Bitcoin Bastion request timed out") from exc
        except httpx.HTTPError as exc:
            raise BastionConnectionError("Bitcoin Bastion connection error") from exc
        return unwrap_response(response, raw=raw)

    async def close(self) -> None:
        await self.client.aclose()
