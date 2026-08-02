"""Production HTTP orchestration surface for Wallet-first authentication.

Cryptographic proof, PoP request, policy, revocation, recovery, and audit logic
remain in their service layers. This router accepts no password, email reset,
seed, mnemonic, xprv, private key, Bearer Access Pass, or LNURL protocol flow.
"""

from __future__ import annotations

import os
from collections.abc import Mapping
from typing import Annotated, Any, Protocol

from fastapi import APIRouter, Depends, Header, Path, status
from sqlalchemy.orm import Session

from app.api.wallet_auth_dependencies import (
    require_fresh_wallet_step_up,
    require_wallet_policy,
)
from app.core.exceptions import AppError
from app.db.session import get_db
from app.schemas.wallet_auth import (
    WalletApiChallengeRequest,
    WalletApiChallengeResponse,
    WalletApiLockdownRequest,
    WalletApiLoginResponse,
    WalletApiRecoveryCompleteRequest,
    WalletApiRecoveryFactorRequest,
    WalletApiRecoveryStartRequest,
    WalletApiRegistrationResponse,
    WalletApiSessionRequest,
    WalletApiStepUpRequest,
    WalletLoginRequest,
    WalletRegisterRequest,
)
from app.services.wallet_auth.challenge_service import WalletChallengeError, WalletChallengeService
from app.services.wallet_auth.repositories.challenges import SqlAlchemyWalletChallengeRepository
from app.services.wallet_auth.types import WalletChallengePurpose

router = APIRouter(prefix="/wallet-auth", tags=["wallet-auth"])

SAFETY_WARNING = (
    "This signature does not authorize a Bitcoin transaction. "
    "This signature only proves wallet control for Bastion access."
)
OPAQUE_PATTERN = r"^(wdev|wproof|wrec)_[A-Za-z0-9_-]{8,128}$"


class WalletAuthApiBackend(Protocol):
    async def register(self, request: WalletRegisterRequest, *, idempotency_key: str | None) -> Mapping[str, Any]: ...
    async def login(self, request: WalletLoginRequest) -> Mapping[str, Any]: ...
    async def create_session(self, request: WalletApiSessionRequest, *, idempotency_key: str | None) -> Mapping[str, Any]: ...
    async def step_up(self, context: Any, request: WalletApiStepUpRequest) -> Mapping[str, Any]: ...
    async def me(self, context: Any) -> Mapping[str, Any]: ...
    async def entitlements(self, context: Any) -> Mapping[str, Any]: ...
    async def devices(self, context: Any) -> Mapping[str, Any]: ...
    async def revoke_device(self, context: Any, device_id: str) -> Mapping[str, Any]: ...
    async def wallets(self, context: Any) -> Mapping[str, Any]: ...
    async def revoke_wallet(self, context: Any, proof_id: str) -> Mapping[str, Any]: ...
    async def lockdown(self, context: Any, request: WalletApiLockdownRequest, *, idempotency_key: str | None) -> Mapping[str, Any]: ...
    async def lockdown_status(self, recovery_reference: str | None) -> Mapping[str, Any]: ...
    async def recovery_start(self, request: WalletApiRecoveryStartRequest) -> Mapping[str, Any]: ...
    async def recovery_status(self, recovery_id: str) -> Mapping[str, Any]: ...
    async def recovery_factor(self, recovery_id: str, request: WalletApiRecoveryFactorRequest) -> Mapping[str, Any]: ...
    async def recovery_complete(self, recovery_id: str, request: WalletApiRecoveryCompleteRequest, *, idempotency_key: str | None) -> Mapping[str, Any]: ...


class UnconfiguredWalletAuthBackend:
    """Fail-closed composition boundary until deployment wires verified services."""

    def __getattr__(self, _name: str) -> Any:
        async def unavailable(*_args: Any, **_kwargs: Any) -> Mapping[str, Any]:
            raise _error("wallet_policy_denied", "Wallet Auth service composition is unavailable.", 503)

        return unavailable


def get_wallet_auth_backend() -> WalletAuthApiBackend:
    return UnconfiguredWalletAuthBackend()  # type: ignore[return-value]


def get_wallet_challenge_service(
    db: Annotated[Session, Depends(get_db)],
) -> WalletChallengeService:
    pepper = os.getenv("WALLET_AUTH_SERVER_PEPPER") or os.getenv("ACCESS_SERVER_PEPPER")
    if not pepper:
        raise _error("wallet_policy_denied", "Wallet challenge service is unavailable.", 503)
    return WalletChallengeService(
        SqlAlchemyWalletChallengeRepository(db), server_pepper=pepper
    )


@router.post(
    "/challenges", response_model=WalletApiChallengeResponse, status_code=status.HTTP_201_CREATED,
    summary="Create a structured, single-use Wallet Auth challenge",
    description="Bastion never requests a Bitcoin seed or private key. Wallet signatures prove wallet control only and never authorize a Bitcoin transaction.",
)
async def create_challenge(
    payload: WalletApiChallengeRequest,
    service: Annotated[WalletChallengeService, Depends(get_wallet_challenge_service)],
) -> WalletApiChallengeResponse:
    try:
        purpose = WalletChallengePurpose(payload.action)
        result = await service.create_challenge(
            purpose=purpose,
            network=payload.network,
            proof_type=payload.proof_type,
            origin=payload.origin,
            device_key_fingerprint=payload.device_key_fingerprint,
            requested_scopes=payload.requested_scopes,
        )
        return WalletApiChallengeResponse(
            challenge_id=result.challenge_id,
            canonical_intent=result.canonical_intent,
            intent_hash=result.intent_hash,
            expires_at=result.expires_at,
            network=payload.network.value,
            proof_type=payload.proof_type.value,
            safety_warning=SAFETY_WARNING,
        )
    except (ValueError, WalletChallengeError) as exc:
        raise _safe_service_error(exc, "wallet_challenge_invalid", 400) from exc


@router.post("/register", response_model=WalletApiRegistrationResponse, summary="Register a Wallet Principal and bind a Device Key")
async def register_wallet(
    payload: WalletRegisterRequest,
    backend: Annotated[WalletAuthApiBackend, Depends(get_wallet_auth_backend)],
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> Mapping[str, Any]:
    return await _call(backend.register(payload, idempotency_key=idempotency_key))


@router.post("/login", response_model=WalletApiLoginResponse, summary="Verify control of an existing Wallet Principal")
async def wallet_login(
    payload: WalletLoginRequest,
    backend: Annotated[WalletAuthApiBackend, Depends(get_wallet_auth_backend)],
) -> Mapping[str, Any]:
    return await _call(backend.login(payload), public_code="wallet_principal_not_available")


@router.post("/sessions", summary="Consume a single-use authentication grant and create a Device-bound PoP Session")
async def create_wallet_session(
    payload: WalletApiSessionRequest,
    backend: Annotated[WalletAuthApiBackend, Depends(get_wallet_auth_backend)],
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> Mapping[str, Any]:
    return await _call(backend.create_session(payload, idempotency_key=idempotency_key))


@router.post("/step-up", summary="Authorize one high-risk action with a fresh Wallet Proof")
async def wallet_step_up(
    payload: WalletApiStepUpRequest,
    context: Annotated[Any, Depends(require_wallet_policy)],
    backend: Annotated[WalletAuthApiBackend, Depends(get_wallet_auth_backend)],
) -> Mapping[str, Any]:
    return await _call(backend.step_up(context, payload))


@router.get("/me", summary="Return privacy-safe Wallet Principal context")
async def wallet_me(context: Annotated[Any, Depends(require_wallet_policy)], backend: Annotated[WalletAuthApiBackend, Depends(get_wallet_auth_backend)]) -> Mapping[str, Any]:
    return await _call(backend.me(context))


@router.get("/entitlements", summary="Return effective verified entitlement and policy limits")
async def wallet_entitlements(context: Annotated[Any, Depends(require_wallet_policy)], backend: Annotated[WalletAuthApiBackend, Depends(get_wallet_auth_backend)]) -> Mapping[str, Any]:
    return await _call(backend.entitlements(context))


@router.get("/devices", summary="List opaque Device bindings")
async def wallet_devices(context: Annotated[Any, Depends(require_wallet_policy)], backend: Annotated[WalletAuthApiBackend, Depends(get_wallet_auth_backend)]) -> Mapping[str, Any]:
    return await _call(backend.devices(context))


@router.delete("/devices/{device_id}", summary="Revoke a Device binding and freeze dependent sessions")
async def revoke_wallet_device(device_id: Annotated[str, Path(pattern=OPAQUE_PATTERN)], context: Annotated[Any, Depends(require_fresh_wallet_step_up)], backend: Annotated[WalletAuthApiBackend, Depends(get_wallet_auth_backend)]) -> Mapping[str, Any]:
    return await _call(backend.revoke_device(context, device_id))


@router.get("/wallets", summary="List opaque Wallet Proof bindings")
async def wallet_bindings(context: Annotated[Any, Depends(require_wallet_policy)], backend: Annotated[WalletAuthApiBackend, Depends(get_wallet_auth_backend)]) -> Mapping[str, Any]:
    return await _call(backend.wallets(context))


@router.delete("/wallets/{proof_id}", summary="Revoke a Wallet Proof binding without deleting audit history")
async def revoke_wallet_binding(proof_id: Annotated[str, Path(pattern=OPAQUE_PATTERN)], context: Annotated[Any, Depends(require_fresh_wallet_step_up)], backend: Annotated[WalletAuthApiBackend, Depends(get_wallet_auth_backend)]) -> Mapping[str, Any]:
    return await _call(backend.revoke_wallet(context, proof_id))


@router.post("/lockdown", summary="Enter idempotent Emergency Lockdown Mode")
async def wallet_lockdown(payload: WalletApiLockdownRequest, context: Annotated[Any, Depends(require_wallet_policy)], backend: Annotated[WalletAuthApiBackend, Depends(get_wallet_auth_backend)], idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None) -> Mapping[str, Any]:
    return await _call(backend.lockdown(context, payload, idempotency_key=idempotency_key))


@router.get("/lockdown/status", summary="Inspect privacy-safe Lockdown state through a recovery-safe path")
async def wallet_lockdown_status(backend: Annotated[WalletAuthApiBackend, Depends(get_wallet_auth_backend)], recovery_reference: str | None = None) -> Mapping[str, Any]:
    return await _call(backend.lockdown_status(recovery_reference), public_code="wallet_principal_not_available")


@router.post("/recovery/start", summary="Start an anti-enumerating Recovery Capsule attempt")
async def wallet_recovery_start(payload: WalletApiRecoveryStartRequest, backend: Annotated[WalletAuthApiBackend, Depends(get_wallet_auth_backend)]) -> Mapping[str, Any]:
    return await _call(backend.recovery_start(payload), public_code="wallet_principal_not_available")


@router.get("/recovery/{recovery_id}", summary="Inspect safe Recovery Capsule progress")
async def wallet_recovery_status(recovery_id: Annotated[str, Path(pattern=OPAQUE_PATTERN)], backend: Annotated[WalletAuthApiBackend, Depends(get_wallet_auth_backend)]) -> Mapping[str, Any]:
    return await _call(backend.recovery_status(recovery_id), public_code="wallet_principal_not_available")


@router.post("/recovery/{recovery_id}/factor", summary="Submit one independently verified recovery factor")
async def wallet_recovery_factor(recovery_id: Annotated[str, Path(pattern=OPAQUE_PATTERN)], payload: WalletApiRecoveryFactorRequest, backend: Annotated[WalletAuthApiBackend, Depends(get_wallet_auth_backend)]) -> Mapping[str, Any]:
    return await _call(backend.recovery_factor(recovery_id, payload), public_code="wallet_recovery_factor_invalid")


@router.post("/recovery/{recovery_id}/complete", summary="Complete policy-approved recovery after factors and cooldown")
async def wallet_recovery_complete(recovery_id: Annotated[str, Path(pattern=OPAQUE_PATTERN)], payload: WalletApiRecoveryCompleteRequest, backend: Annotated[WalletAuthApiBackend, Depends(get_wallet_auth_backend)], idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None) -> Mapping[str, Any]:
    return await _call(backend.recovery_complete(recovery_id, payload, idempotency_key=idempotency_key))


async def _call(awaitable: Any, *, public_code: str | None = None) -> Mapping[str, Any]:
    try:
        result = await awaitable
        return dict(result)
    except AppError:
        raise
    except Exception as exc:
        code = public_code or getattr(exc, "code", None) or getattr(exc, "reason_code", None) or "wallet_policy_denied"
        raise _error(str(code), "Wallet Auth request could not be completed.", 403) from exc


def _safe_service_error(exc: Exception, fallback: str, status_code: int) -> AppError:
    code = getattr(exc, "code", None) or getattr(exc, "reason_code", None) or fallback
    mapping = {
        "wallet_challenge_origin_mismatch": "wallet_origin_mismatch",
        "wallet_challenge_network_mismatch": "wallet_network_mismatch",
        "wallet_challenge_consumed": "wallet_challenge_used",
    }
    return _error(mapping.get(str(code), str(code)), "Wallet challenge is invalid.", status_code)


def _error(code: str, message: str, status_code: int) -> AppError:
    return AppError(message=message, status_code=status_code, code=code)
