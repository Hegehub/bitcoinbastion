"""Stage-1B0 strict transport foundation.

This module deliberately contains transport contracts only. Domain adapters, Reflex
State, authorization policy, and signing keys do not belong here.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import Literal, Protocol, TypeVar
from urllib.parse import quote
from uuid import UUID

import httpx
from pydantic import BaseModel, ConfigDict, Field, ValidationError

ResponseT = TypeVar("ResponseT", bound=BaseModel)
type JsonScalar = None | bool | int | float | str
type JsonValue = JsonScalar | list[JsonValue] | dict[str, JsonValue]


def serialize_query_value(
    value: JsonValue | date | datetime | Decimal | UUID,
) -> str | int | float | bool | None:
    """Serialize an application query value without admitting arbitrary objects."""
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, (Decimal, UUID)):
        return str(value)
    if isinstance(value, list):
        return ",".join(str(serialize_query_value(item)) for item in value)
    raise ValueError("object query parameters are not supported")


class StrictTransportDTO(BaseModel):
    """Strict generated-contract policy: unknown fields and coercion are rejected."""

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)


class HealthOutDTO(StrictTransportDTO):
    status: str
    app: str
    details: dict[str, str] = Field(default_factory=dict)


class PublicStatusResponseDTO(StrictTransportDTO):
    platform_status: str
    trace_status: str
    production_calibrated: bool
    modules: dict[str, str]
    known_limitations: list[str] = Field(default_factory=list)
    last_update: datetime


class PublicStatusEnvelopeDTO(StrictTransportDTO):
    success: bool = True
    data: PublicStatusResponseDTO


class NoContentDTO(StrictTransportDTO):
    """First-class 204 success; it is not a 200 null or fabricated object."""

    status: Literal[204] = 204


class TextResponseDTO(StrictTransportDTO):
    status: int
    content_type: Literal["text/plain"]
    text: str


class OpaqueHtmlDocumentDTO(StrictTransportDTO):
    """Opaque transport content that must never be treated as trusted/renderable HTML."""

    status: int
    content_type: Literal["text/html"]
    document: str


@dataclass(frozen=True)
class SecurityMetadata:
    identity: str
    public: bool
    access_required: bool
    signed_request_required: bool
    human_intent_required: bool
    source_symbol: str
    review_owner: str

    def __post_init__(self) -> None:
        if self.public and any(
            (self.access_required, self.signed_request_required, self.human_intent_required)
        ):
            raise ValueError("public security metadata cannot require protected material")


@dataclass(frozen=True)
class NormalizedOperation[ResponseT: BaseModel]:
    matrix_id: str
    operation_id: str
    method: Literal["GET", "POST", "PUT", "PATCH", "DELETE"]
    path: str
    backend_tag: str
    product: str
    disposition: Literal["UI_REQUIRED", "UI_OPTIONAL"]
    success_status: int
    response_type: type[ResponseT]
    security: SecurityMetadata
    retry_safe: bool
    owner: str
    response_media_type: str = "application/json"


@dataclass(frozen=True)
class ContractRegistryEntry:
    registry_id: str
    source_head: str
    operation: NormalizedOperation[BaseModel]
    request_schema: str
    success_schema: str
    error_schema: str = "SafeTransportError/v1"
    generation_version: str = "1b0.v1"


@dataclass
class SafeTransportError(Exception):
    status: int | None
    code: str
    retryable: bool
    safe_message: str
    uncertain_outcome: bool = False

    def __str__(self) -> str:
        return f"{self.code} ({self.status or 'network'}): {self.safe_message}"


SECURITY_PROVIDER_FACTORY: Callable[[], RequestSecurityProvider] | None = None


class RequestSecurityProvider(Protocol):
    """Injected non-persistent PoP signer boundary for protected requests."""

    def headers_for(
        self,
        *,
        method: str,
        path: str,
        query_parameters: dict[str, str | int | float | bool | None],
        body: bytes,
    ) -> dict[str, str]: ...


class HttpTransport:
    """One callable engine; secrets/signing providers remain injected boundaries."""

    def __init__(
        self,
        client: httpx.AsyncClient,
        *,
        timeout_seconds: float = 10.0,
        security_provider: RequestSecurityProvider | None = None,
    ) -> None:
        self._client = client
        self._timeout = timeout_seconds
        self._security_provider = security_provider or (
            SECURITY_PROVIDER_FACTORY() if SECURITY_PROVIDER_FACTORY is not None else None
        )

    async def invoke(
        self,
        operation: NormalizedOperation[ResponseT],
        *,
        path_parameters: dict[str, str] | None = None,
        query_parameters: dict[str, str | int | float | bool | None] | None = None,
        body: JsonValue | None = None,
        request_headers: dict[str, str] | None = None,
    ) -> ResponseT:
        path = operation.path
        for name, value in sorted((path_parameters or {}).items()):
            path = path.replace("{" + name + "}", quote(value, safe=""))
        query: dict[str, str | int | float | bool | None] = {
            key: value for key, value in (query_parameters or {}).items() if value is not None
        }
        encoded_body = (
            b""
            if body is None
            else __import__("json")
            .dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
            .encode()
        )
        if not operation.security.public and self._security_provider is None:
            raise SafeTransportError(
                None,
                "security_provider_required",
                False,
                "Protected transport boundary required",
            )
        provider = self._security_provider
        supplied_headers = request_headers or {}
        protected_header_names = {
            "authorization",
            "bastion-request-timestamp",
            "bastion-request-nonce",
            "bastion-request-body-hash",
            "bastion-request-signature",
        }
        if any(
            name.lower().startswith("x-bastion-")
            or name.lower() in protected_header_names
            for name in supplied_headers
        ):
            raise SafeTransportError(None, "reserved_security_header", False, "Reserved header")
        headers = (
            {}
            if operation.security.public or provider is None
            else provider.headers_for(
                method=operation.method,
                path=path,
                query_parameters=query,
                body=encoded_body,
            )
        )
        if body is not None:
            headers = {"content-type": "application/json", **headers}
        headers = {**supplied_headers, **headers}
        try:
            response = await self._client.request(
                operation.method,
                path,
                params=query,
                content=encoded_body or None,
                headers=headers,
                timeout=self._timeout,
            )
        except httpx.TimeoutException as exc:
            raise SafeTransportError(
                None,
                "transport_timeout",
                operation.retry_safe,
                "The request timed out.",
                uncertain_outcome=operation.method != "GET",
            ) from exc
        except httpx.RequestError as exc:
            raise SafeTransportError(
                None,
                "network_failure",
                operation.retry_safe,
                "Network request failed.",
            ) from exc
        if response.status_code != operation.success_status:
            raise self._safe_http_error(response)
        if operation.response_type is NoContentDTO:
            if response.content:
                raise SafeTransportError(
                    204,
                    "unexpected_no_content_body",
                    False,
                    "A no-content response contained data.",
                )
            return operation.response_type.model_validate({"status": 204})
        content_type = response.headers.get("content-type", "").split(";", 1)[0]
        if operation.response_type is TextResponseDTO:
            if content_type != "text/plain":
                raise SafeTransportError(
                    response.status_code,
                    "unexpected_content_type",
                    False,
                    "Unexpected response content type.",
                )
            return operation.response_type.model_validate(
                {
                    "status": response.status_code,
                    "content_type": "text/plain",
                    "text": response.text,
                }
            )
        if operation.response_type is OpaqueHtmlDocumentDTO:
            if content_type != "text/html":
                raise SafeTransportError(
                    response.status_code,
                    "unexpected_content_type",
                    False,
                    "Unexpected response content type.",
                )
            return operation.response_type.model_validate(
                {
                    "status": response.status_code,
                    "content_type": "text/html",
                    "document": response.text,
                }
            )
        try:
            # Validate the actual JSON bytes. Pydantic strict mode correctly
            # accepts JSON date-time strings here while still rejecting Python
            # string coercion passed directly to model_validate().
            return operation.response_type.model_validate_json(response.content)
        except (ValueError, ValidationError) as exc:
            raise SafeTransportError(
                response.status_code,
                "malformed_response",
                False,
                "The server response did not match its contract.",
            ) from exc

    @staticmethod
    def _safe_http_error(response: httpx.Response) -> SafeTransportError:
        retryable = response.status_code == 429 or response.status_code >= 500
        safe_messages = {
            401: "Authentication is required.",
            403: "The request is forbidden.",
            404: "The resource was not found.",
            409: "The request conflicts with current state.",
            422: "The request is invalid.",
            429: "The request was rate limited.",
        }
        return SafeTransportError(
            response.status_code,
            f"http_{response.status_code}",
            retryable,
            safe_messages.get(response.status_code, "The server could not complete the request."),
        )
