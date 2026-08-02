from __future__ import annotations

import json
from typing import Any

import httpx

from bitcoin_bastion_sdk.access_auth import BastionAccessAuth
from bitcoin_bastion_sdk.access.request_signing import canonical_json_bytes
from bitcoin_bastion_sdk.access.session import BastionPoPSession
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
    BastionAccessChallengeExpired,
    BastionAccessError,
    BastionAccessPolicyDenied,
    BastionAccessRevoked,
    BastionAccessSessionExpired,
    BastionAccessSignatureError,
    BastionAccessUpgradeRequired,
    BastionPolicyError,
    BastionQuotaExceededError,
    BastionRecoveryRequiredError,
    BastionRevokedError,
    BastionStepUpRequiredError,
    BastionUpgradeRequiredError,
    LNURLChallengeExpiredError,
    LNURLChallengeUsedError,
    LNURLInvalidK1Error,
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
    code = _error_code(payload)
    kwargs = {
        "status_code": response.status_code,
        "error_code": code,
        "request_id": response.headers.get("x-request-id"),
        "payload": payload,
    }
    if code in {"access_session_expired", "session_expired"}:
        raise BastionAccessSessionExpired(message)
    if code in {"access_signature_invalid", "invalid_signature", "access_signature_required"}:
        raise BastionAccessSignatureError(message)
    if code in {"challenge_expired", "access_challenge_expired"}:
        raise BastionAccessChallengeExpired(message)
    if code in {"policy_denied", "access_policy_denied"}:
        raise BastionAccessPolicyDenied(message)
    if code in {"upgrade_required", "access_upgrade_required"}:
        raise BastionAccessUpgradeRequired(message)
    if code in {"revoked", "access_session_revoked", "pass_revoked"}:
        raise BastionAccessRevoked(message)
    policy_errors = {
        "upgrade_required": BastionUpgradeRequiredError,
        "access_upgrade_required": BastionUpgradeRequiredError,
        "step_up_required": BastionStepUpRequiredError,
        "wallet_step_up_required": BastionStepUpRequiredError,
        "quota_exceeded": BastionQuotaExceededError,
        "recovery_required": BastionRecoveryRequiredError,
        "access_revoked": BastionRevokedError,
    }
    if code in policy_errors:
        raise policy_errors[code](message, **kwargs)
    if code == "lnurl_k1_expired":
        raise LNURLChallengeExpiredError(message, **kwargs)
    if code == "lnurl_k1_reused":
        raise LNURLChallengeUsedError(message, **kwargs)
    if code in {"lnurl_invalid_k1", "lnurl_unknown_k1"}:
        raise LNURLInvalidK1Error(message, **kwargs)
    if code in {"wallet_policy_denied", "lnurl_policy_denied"}:
        raise BastionPolicyError(message, **kwargs)
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
        raise BastionAPIError(
            _message_from_payload(payload, "Bitcoin Bastion API error"), payload=payload
        )
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
        access_auth: BastionAccessAuth | None = None,
        pop_session: BastionPoPSession | None = None,
        allow_legacy_bearer_auth: bool = False,
        self_hosted_mode: bool = False,
        allow_onion: bool = False,
    ) -> None:
        self.config = BastionSDKConfig(
            base_url=base_url,
            api_prefix=api_prefix,
            timeout=timeout,
            self_hosted_mode=self_hosted_mode,
            allow_onion=allow_onion,
        )
        self.access_auth = access_auth
        self.pop_session = pop_session
        self.headers = build_headers(
            api_key, headers, allow_legacy_bearer_auth=allow_legacy_bearer_auth
        )
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
        require_auth: bool = False,
    ) -> Any:
        try:
            body = canonical_json_bytes(json)
            request_headers = self._signed_headers(
                method, path, params=params, body=body, require_auth=require_auth
            )
            response = self.client.request(
                method,
                path,
                params=params,
                content=body if json is not None else None,
                headers={"Content-Type": "application/json", **(request_headers or {})}
                if json is not None
                else request_headers,
            )
        except httpx.TimeoutException as exc:
            raise BastionTimeoutError("Bitcoin Bastion request timed out") from exc
        except httpx.HTTPError as exc:
            raise BastionConnectionError("Bitcoin Bastion connection error") from exc
        return unwrap_response(response, raw=raw)

    def _signed_headers(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None,
        body: bytes,
        require_auth: bool,
    ) -> dict[str, str] | None:
        if self.pop_session is not None:
            pairs = list(httpx.QueryParams(params or {}).multi_items())
            return self.pop_session.sign(method, path, params=pairs, body=body).headers
        if self.access_auth is None:
            if require_auth:
                raise BastionAccessError("Protected SDK request requires BastionAccessAuth")
            return None
        return self.access_auth.sign_headers(method, path, json_body=json.loads(body) if body else None)

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
        access_auth: BastionAccessAuth | None = None,
        pop_session: BastionPoPSession | None = None,
        allow_legacy_bearer_auth: bool = False,
    ) -> None:
        self.config = BastionSDKConfig(base_url=base_url, api_prefix=api_prefix, timeout=timeout)
        self.access_auth = access_auth
        self.pop_session = pop_session
        self.headers = build_headers(
            api_key, headers, allow_legacy_bearer_auth=allow_legacy_bearer_auth
        )
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
        require_auth: bool = False,
    ) -> Any:
        try:
            request_headers = self._signed_headers(
                method, path, params=params, json_body=json, require_auth=require_auth
            )
            response = await self.client.request(
                method, path, params=params, json=json, headers=request_headers
            )
        except httpx.TimeoutException as exc:
            raise BastionTimeoutError("Bitcoin Bastion request timed out") from exc
        except httpx.HTTPError as exc:
            raise BastionConnectionError("Bitcoin Bastion connection error") from exc
        return unwrap_response(response, raw=raw)

    def _signed_headers(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None,
        json_body: JsonDict | None,
        require_auth: bool,
    ) -> dict[str, str] | None:
        if self.pop_session is not None:
            pairs = list(httpx.QueryParams(params or {}).multi_items())
            return self.pop_session.sign(
                method, path, params=pairs, body=canonical_json_bytes(json_body)
            ).headers
        if self.access_auth is None:
            if require_auth:
                raise BastionAccessError("Protected SDK request requires BastionAccessAuth")
            return None
        return self.access_auth.sign_headers(method, path, json_body=json_body)

    async def close(self) -> None:
        await self.client.aclose()
