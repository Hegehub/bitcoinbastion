"""Compatibility facade for the unified Wallet/LNURL access dependencies.

New protected routes should import from :mod:`app.api.access_dependencies`.
The resolver hooks remain temporarily for deployments migrating Prompt 64
composition; their default path is the canonical PoP/revocation context.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Annotated, Any

from fastapi import Depends, Request
from sqlalchemy.orm import Session

from app.api import access_dependencies as unified
from app.core.exceptions import AppError
from app.db.session import get_db
from app.domain.access.context import AccessContext

WalletRequestResolver = Callable[[Request, Session], Any | Awaitable[Any]]
WalletPolicyResolver = Callable[[Any, str, Session], Any | Awaitable[Any]]

WALLET_REQUEST_CONTEXT_RESOLVER: WalletRequestResolver | None = None
WALLET_POLICY_RESOLVER: WalletPolicyResolver | None = None


def wallet_error(code: str, message: str, status_code: int = 403) -> AppError:
    return AppError(message=message, status_code=status_code, code=code)


async def require_wallet_session(
    request: Request, db: Annotated[Session, Depends(get_db)]
) -> Any:
    if WALLET_REQUEST_CONTEXT_RESOLVER is None:
        try:
            return await unified.get_access_context(request, db)
        except AppError as exc:
            raise wallet_error(
                "wallet_session_invalid", "Wallet PoP Session is invalid.", exc.status_code
            ) from exc
    authorization = request.headers.get("authorization", "")
    if not authorization.startswith("PoP sess_"):
        raise wallet_error("wallet_session_invalid", "A Device-bound PoP Session is required.", 401)
    if any(not request.headers.get(name) for name in (
        "bastion-request-timestamp",
        "bastion-request-nonce",
        "bastion-request-body-hash",
        "bastion-request-signature",
        "bastion-principal",
    )):
        raise wallet_error("wallet_session_invalid", "A valid PoP request signature is required.", 401)
    try:
        result = WALLET_REQUEST_CONTEXT_RESOLVER(request, db)
        return await result if hasattr(result, "__await__") else result
    except AppError:
        raise
    except Exception as exc:
        raise wallet_error("wallet_session_invalid", "Wallet session is invalid.", 401) from exc


async def require_wallet_policy(
    request: Request,
    context: Annotated[Any, Depends(require_wallet_session)],
    db: Annotated[Session, Depends(get_db)],
) -> Any:
    route = request.scope.get("route")
    action = str(getattr(route, "name", request.method.lower()))
    if WALLET_POLICY_RESOLVER is not None:
        result = WALLET_POLICY_RESOLVER(context, action, db)
        decision = await result if hasattr(result, "__await__") else result
        allowed = getattr(decision, "allowed", None)
        if allowed is None:
            allowed = getattr(decision, "decision", None) == "allow" or decision is True
        if not allowed:
            raise wallet_error("wallet_policy_denied", "Wallet policy denied this action.")
        return context
    if not isinstance(context, AccessContext):
        raise wallet_error("wallet_policy_denied", "Wallet policy evaluation is unavailable.", 503)
    return unified.require_policy_decision(context, action=action)


async def require_fresh_wallet_step_up(
    request: Request,
    context: Annotated[Any, Depends(require_wallet_policy)],
) -> Any:
    route = request.scope.get("route")
    action = str(getattr(route, "name", request.method.lower()))
    if not isinstance(context, AccessContext):
        if not request.headers.get("bastion-wallet-step-up"):
            raise wallet_error("wallet_step_up_required", "Fresh Wallet step-up is required.")
        return context
    unified._validate_fresh_step_up(context, action, max_age_seconds=300)
    return unified.require_policy_decision(context, action=action, risk_level="high")


get_access_context = unified.get_access_context
require_access_session = unified.require_access_session
require_scope = unified.require_scope
require_metric_entitlement = unified.require_metric_entitlement
require_plan = unified.require_plan
require_business_role = unified.require_business_role
require_business_policy = unified.require_business_policy
require_payregister_device = unified.require_payregister_device
require_offline_policy = unified.require_offline_policy
require_withdraw_authorization = unified.require_withdraw_authorization

setattr(require_wallet_session, "__bastion_route_classification__", "protected")
setattr(require_wallet_policy, "__bastion_route_classification__", "protected")
setattr(require_fresh_wallet_step_up, "__bastion_route_classification__", "high_risk")
