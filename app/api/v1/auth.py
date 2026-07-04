from typing import Any

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/auth", tags=["auth"])

LEGACY_AUTH_DISABLED_CODE = "legacy_auth_disabled"
LEGACY_AUTH_REPLACEMENT = "/api/v1/access/payment-intents"
LEGACY_AUTH_DISABLED_MESSAGE = (
    "Legacy email/password authentication is disabled. Use Bastion Proof-of-Access."
)


def _legacy_auth_disabled_response() -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_410_GONE,
        content={
            "error": {
                "code": LEGACY_AUTH_DISABLED_CODE,
                "message": LEGACY_AUTH_DISABLED_MESSAGE,
                "replacement": LEGACY_AUTH_REPLACEMENT,
            }
        },
    )


_DISABLED_OPENAPI: dict[str, Any] = {
    "x-legacy-auth-disabled": True,
    "x-replacement": LEGACY_AUTH_REPLACEMENT,
}


@router.post(
    "/register",
    deprecated=True,
    summary="Legacy password registration disabled",
    description=(
        "Legacy email/username/password registration is disabled. "
        "Use the Proof-of-Access payment, certificate, challenge, and session flow instead."
    ),
    openapi_extra=_DISABLED_OPENAPI,
)
def register() -> JSONResponse:
    """Reject legacy password-backed account creation."""
    return _legacy_auth_disabled_response()


@router.post(
    "/login",
    deprecated=True,
    summary="Legacy password login disabled",
    description=(
        "Legacy username/password login and bearer-token issuance are disabled. "
        "Use Bastion Proof-of-Access sessions and per-request signatures instead."
    ),
    openapi_extra=_DISABLED_OPENAPI,
)
def login() -> JSONResponse:
    """Reject legacy password login and never issue bearer tokens."""
    return _legacy_auth_disabled_response()
