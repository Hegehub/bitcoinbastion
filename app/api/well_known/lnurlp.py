"""Public root-level Lightning Address discovery route.

The endpoint returns raw LNURL protocol JSON and intentionally bypasses the
normal Bastion response envelope. It is read-only discovery: no invoice,
settlement, entitlement, principal, session, or Access Certificate is created.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlparse

from fastapi import APIRouter, Depends, Request, Response
from fastapi.responses import JSONResponse

from app.domain.lnurl.lightning_address import (
    LightningAddressInvalidError,
    LightningAddressReservedError,
    normalize_local_part,
)
from app.schemas.lnurl import LNURLErrorResponse, LNURLPayDiscoveryResponse
from app.services.lnurl.lightning_address_domain_policy import (
    LightningAddressDomainPolicy,
    LightningAddressDomainPolicyConfig,
)
from app.services.lnurl.lightning_address_service import (
    LightningAddressService,
    LightningAddressServiceConfig,
    LightningAddressServiceError,
)

LNURL_CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET, HEAD, OPTIONS",
    "X-Content-Type-Options": "nosniff",
    "Cache-Control": "no-store",
}
GENERIC_UNAVAILABLE = "Lightning address unavailable"
GENERIC_INVALID = "Invalid Lightning address"
GENERIC_TEMPORARY = "Payment endpoint temporarily unavailable"

router = APIRouter(prefix="/.well-known/lnurlp", tags=["LNURL", "Lightning Address"])


@dataclass(frozen=True, slots=True)
class LNURLPRouteConfig:
    public_base_url: str = os.getenv("LNURL_PUBLIC_BASE_URL", "https://bitcoin-bastion.com")
    callback_base_url: str = os.getenv("LNURL_CALLBACK_BASE_URL", "https://bitcoin-bastion.com")
    primary_domain: str = os.getenv("LNURL_PRIMARY_DOMAIN", "bitcoin-bastion.com")
    payregister_domain: str = os.getenv("LNURL_PAYREGISTER_DOMAIN", "payregister.bitcoin-bastion.com")
    allowed_public_hosts: frozenset[str] = frozenset(
        host.strip().lower()
        for host in os.getenv(
            "LNURL_ALLOWED_PUBLIC_HOSTS",
            "bitcoin-bastion.com,payregister.bitcoin-bastion.com,testserver",
        ).split(",")
        if host.strip()
    )
    allow_onion_addresses: bool = os.getenv("LNURL_ALLOW_ONION_ADDRESSES", "false").lower() == "true"
    rate_limit_per_minute: int = int(os.getenv("LNURL_LIGHTNING_ADDRESS_RATE_LIMIT_PER_MINUTE", "120"))


_DEFAULT_SERVICE: LightningAddressService | None = None
_RATE_BUCKETS: dict[tuple[str, int], int] = {}


def _config() -> LNURLPRouteConfig:
    return LNURLPRouteConfig()


def _trusted_service() -> LightningAddressService:
    global _DEFAULT_SERVICE
    if _DEFAULT_SERVICE is None:
        cfg = _config()
        domain_policy = LightningAddressDomainPolicy(
            LightningAddressDomainPolicyConfig(
                primary_domain=cfg.primary_domain,
                first_party_domains=frozenset({cfg.primary_domain}),
                payregister_domains=frozenset({cfg.payregister_domain}),
                allow_onion_addresses=cfg.allow_onion_addresses,
            )
        )
        service = LightningAddressService(
            domain_policy=domain_policy,
            config=LightningAddressServiceConfig(
                primary_domain=cfg.primary_domain,
                payregister_domain=cfg.payregister_domain,
                allow_onion_addresses=cfg.allow_onion_addresses,
            ),
        )
        for alias in ("lite", "basic", "plus", "pro", "business", "enterprise"):
            try:
                service.create_product_address(local_part=alias)
            except Exception:
                pass
        _DEFAULT_SERVICE = service
    return _DEFAULT_SERVICE


def get_lightning_address_service() -> LightningAddressService:
    return _trusted_service()


@router.get(
    "/{name:path}",
    response_model=LNURLPayDiscoveryResponse | LNURLErrorResponse,
    response_model_by_alias=True,
    responses={200: {"description": "Raw LNURL-pay discovery response or LNURL protocol error JSON."}},
    summary="Resolve a Lightning Address local part to an LNURL-pay discovery response",
)
async def get_lnurlp(
    name: str,
    request: Request,
    service: LightningAddressService = Depends(get_lightning_address_service),
) -> JSONResponse:
    return _handle_discovery(name=name, request=request, service=service)


@router.head("/{name:path}", include_in_schema=False)
async def head_lnurlp(
    name: str,
    request: Request,
    service: LightningAddressService = Depends(get_lightning_address_service),
) -> Response:
    response = _handle_discovery(name=name, request=request, service=service)
    return Response(status_code=response.status_code, headers=dict(response.headers), media_type="application/json")


@router.options("/{name:path}", include_in_schema=False)
async def options_lnurlp(name: str) -> Response:
    return Response(status_code=204, headers={**LNURL_CORS_HEADERS, "Allow": "GET, HEAD, OPTIONS"}, media_type="application/json")


def _handle_discovery(*, name: str, request: Request, service: LightningAddressService) -> JSONResponse:
    try:
        cfg = _config()
        _rate_limit(request, cfg)
        _validate_host(request, cfg)
        canonical_name = normalize_local_part(name)
        domain = _domain_for_request(request, cfg)
        resolution = service.resolve_address(f"{canonical_name}@{domain}")
        payload = _payload_from_resolution(resolution, cfg)
        return _lnurl_json(payload, status_code=200)
    except (LightningAddressInvalidError, LightningAddressReservedError):
        return _lnurl_json(LNURLErrorResponse(reason=GENERIC_INVALID).model_dump(), status_code=200)
    except LightningAddressServiceError:
        return _lnurl_json(LNURLErrorResponse(reason=GENERIC_UNAVAILABLE).model_dump(), status_code=200)
    except RuntimeError as exc:
        reason = GENERIC_TEMPORARY if str(exc) == "rate_limited" else GENERIC_UNAVAILABLE
        return _lnurl_json(
            LNURLErrorResponse(reason=reason).model_dump(),
            status_code=200,
            extra_headers={"Retry-After": "60"} if reason == GENERIC_TEMPORARY else None,
        )
    except Exception:
        return _lnurl_json(LNURLErrorResponse(reason=GENERIC_UNAVAILABLE).model_dump(), status_code=200)


def _payload_from_resolution(resolution: Any, cfg: LNURLPRouteConfig) -> dict[str, Any]:
    callback = _trusted_callback_url(cfg, resolution.callback_reference)
    metadata = _metadata_with_identifier(resolution.metadata, resolution.normalized_address)
    model = LNURLPayDiscoveryResponse(
        callback=callback,
        maxSendable=resolution.max_sendable_msat,
        minSendable=resolution.min_sendable_msat,
        metadata=metadata,
        tag="payRequest",
        commentAllowed=resolution.comment_allowed,
        payerData=resolution.payer_data_policy,
    )
    return model.model_dump(by_alias=True, exclude_none=True)


def _metadata_with_identifier(raw_metadata: str, normalized_address: str) -> str:
    metadata = json.loads(raw_metadata)
    if not isinstance(metadata, list):
        raise LightningAddressInvalidError("metadata_invalid")
    plain_entries = [item for item in metadata if isinstance(item, list) and len(item) == 2 and item[0] == "text/plain"]
    if len(plain_entries) != 1:
        raise LightningAddressInvalidError("metadata_plain_text_invalid")
    if not any(isinstance(item, list) and len(item) == 2 and item[0] == "text/identifier" for item in metadata):
        metadata.append(["text/identifier", normalized_address])
    return json.dumps(metadata, ensure_ascii=False, separators=(",", ":"))


def _trusted_callback_url(cfg: LNURLPRouteConfig, callback_reference: str) -> str:
    base = cfg.callback_base_url.rstrip("/")
    parsed = urlparse(base)
    if not parsed.hostname:
        raise LightningAddressInvalidError("callback_host_invalid")
    host = parsed.hostname.lower()
    if host in {"localhost", "127.0.0.1", "::1"} or host.startswith(("10.", "192.168.", "169.254.")):
        raise LightningAddressInvalidError("callback_host_invalid")
    if host.endswith(".onion"):
        if not cfg.allow_onion_addresses or parsed.scheme not in {"http", "https"}:
            raise LightningAddressInvalidError("callback_onion_policy_invalid")
    elif parsed.scheme != "https":
        raise LightningAddressInvalidError("callback_https_required")
    if cfg.allowed_public_hosts and host not in cfg.allowed_public_hosts:
        raise LightningAddressInvalidError("callback_host_not_allowed")
    return f"{base}/api/v1/lnurl/pay/callback/{callback_reference}"


def _domain_for_request(request: Request, cfg: LNURLPRouteConfig) -> str:
    host = (request.headers.get("host") or "").split(":", 1)[0].lower()
    if host == cfg.payregister_domain:
        return cfg.payregister_domain
    if host == cfg.primary_domain:
        return cfg.primary_domain
    return cfg.primary_domain


def _validate_host(request: Request, cfg: LNURLPRouteConfig) -> None:
    host = (request.headers.get("host") or "").split(":", 1)[0].lower()
    forwarded = (request.headers.get("x-forwarded-host") or "").split(",", 1)[0].split(":", 1)[0].lower()
    proto = (request.headers.get("x-forwarded-proto") or "").split(",", 1)[0].lower()
    for candidate in (host, forwarded):
        if candidate and candidate not in cfg.allowed_public_hosts:
            raise RuntimeError("invalid_host")
    if proto and proto not in {"https", "http"}:
        raise RuntimeError("invalid_host")


def _rate_limit(request: Request, cfg: LNURLPRouteConfig) -> None:
    import time

    minute = int(time.time() // 60)
    client = request.client.host if request.client else "unknown"
    key = (client, minute)
    _RATE_BUCKETS[key] = _RATE_BUCKETS.get(key, 0) + 1
    if _RATE_BUCKETS[key] > cfg.rate_limit_per_minute:
        raise RuntimeError("rate_limited")


def _lnurl_json(payload: dict[str, Any], *, status_code: int, extra_headers: dict[str, str] | None = None) -> JSONResponse:
    headers = dict(LNURL_CORS_HEADERS)
    if extra_headers:
        headers.update(extra_headers)
    return JSONResponse(status_code=status_code, content=payload, headers=headers, media_type="application/json")


__all__ = ["router", "get_lightning_address_service", "LNURL_CORS_HEADERS"]
