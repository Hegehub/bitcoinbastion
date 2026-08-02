"""Proof-of-Access dependency layer for protected API endpoints.

These dependencies reject legacy Authorization: Bearer as Access proof and build
policy-checked AccessContext objects from Bastion PoP session/request headers.
They do not accept raw Access Passes, passwords, user IDs, Bitcoin seeds, or
private keys as authorization material.
"""

from __future__ import annotations

import os
from collections.abc import Awaitable, Callable
from dataclasses import replace
from datetime import UTC, datetime
from enum import Enum
from typing import Annotated, Any

from fastapi import Depends, Request
from sqlalchemy.orm import Session

from app.core.exceptions import AppError
from app.db.session import get_db
from app.domain.access.context import AccessContext, UnifiedAccessContext
from app.domain.access.plans import PlanCode, normalize_plan_code, plan_rank
from app.services.access.plan_entitlements import (
    build_entitlement_overlay,
    required_plan_for_metric_group,
)
from app.services.access.policy_context import AccessPolicyContext
from app.services.access.policy_engine import AccessPolicyEngine

ACCESS_REQUIRED = "access_required"
ACCESS_SESSION_MISSING = ACCESS_REQUIRED
ACCESS_SESSION_INVALID = "access_session_invalid"
ACCESS_SESSION_EXPIRED = "access_session_expired"
ACCESS_SESSION_REVOKED = "access_session_revoked"
ACCESS_SIGNATURE_REQUIRED = "access_signature_required"
ACCESS_SIGNATURE_INVALID = "access_signature_invalid"
ACCESS_SCOPE_MISSING = "scope_required"
ACCESS_PLAN_REQUIRED = "access_plan_required"
ACCESS_UPGRADE_REQUIRED = "access_upgrade_required"
ACCESS_METRIC_NOT_ALLOWED = "access_metric_not_allowed"
ACCESS_QUOTA_EXCEEDED = "access_quota_exceeded"
ACCESS_POLICY_DENIED = "access_policy_denied"
ACCESS_HUMAN_INTENT_REQUIRED = "access_human_intent_required"
ACCESS_BUSINESS_ROLE_REQUIRED = "access_business_role_required"
ACCESS_ENTERPRISE_POLICY_REQUIRED = "access_enterprise_policy_required"
ACCESS_STEP_UP_REQUIRED = "access_step_up_required"
ACCESS_RECOVERY_REQUIRED = "access_recovery_required"
ACCESS_LOCKDOWN_ACTIVE = "access_lockdown_active"
ACCESS_PRINCIPAL_MISMATCH = "access_principal_mismatch"
ACCESS_REVOCATION_UNAVAILABLE = "access_revocation_unavailable"
ACCESS_LEGACY_BEARER_REJECTED = "access_legacy_bearer_rejected"

CRITICAL_ACTIONS = frozenset(
    {
        "create_api_key",
        "increase_scope",
        "export_data",
        "create_delegated_pass",
        "enable_payregister_admin",
        "treasury_policy_change",
        "recovery_change",
        "device_add",
        "lockdown_disable",
        "business_role_assignment",
        "enterprise_policy_change",
        "subscription_upgrade_with_new_permissions",
    }
)

SessionContextResolver = Callable[[str, Session], Any]
SignatureVerifier = Callable[[Request, Session], AccessContext | Awaitable[AccessContext]]
RevocationChecker = Callable[[AccessContext, Session], dict[str, Any]]
PolicyEngineFactory = Callable[[], AccessPolicyEngine]

SESSION_CONTEXT_RESOLVER: SessionContextResolver | None = None
REQUEST_SIGNATURE_VERIFIER: SignatureVerifier | None = None
REVOCATION_CHECKER: RevocationChecker | None = None
POLICY_ENGINE_FACTORY: PolicyEngineFactory = AccessPolicyEngine


class RouteClassification(str, Enum):
    PUBLIC = "public"
    AUTH_BOOTSTRAP = "auth_bootstrap"
    PROTECTED = "protected"
    HIGH_RISK = "high_risk"
    BUSINESS = "business"
    ENTERPRISE = "enterprise"
    SOVEREIGN = "sovereign"


def classified(classification: RouteClassification) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Mark dependencies and handlers for runtime route-security introspection."""

    def decorator(target: Callable[..., Any]) -> Callable[..., Any]:
        setattr(target, "__bastion_route_classification__", classification.value)
        return target

    return decorator


def access_error(code: str, message: str, status_code: int = 403) -> AppError:
    return AppError(message=message, status_code=status_code, code=code)


async def get_access_context(
    request: Request, db: Annotated[Session, Depends(get_db)]
) -> UnifiedAccessContext:
    cached = getattr(request.state, "unified_access_context", None)
    if isinstance(cached, AccessContext):
        return cached
    authorization = request.headers.get("authorization", "")
    if authorization.lower().startswith("bearer "):
        raise access_error(
            ACCESS_LEGACY_BEARER_REJECTED,
            "Proof-of-Access requires Bastion access headers, not Authorization Bearer.",
            401,
        )
    session_token, canonical_pop = _extract_session_token(request)
    if not session_token:
        raise access_error(ACCESS_SESSION_MISSING, "A Device-bound PoP Session is required.", 401)

    signed_headers_present = all(_request_header(request, name) for name in _POP_HEADER_NAMES)
    if signed_headers_present:
        context = await _verify_signed_request(request, db, session_token=session_token)
    else:
        context = _context_from_session(session_token, request, db)
        if canonical_pop:
            raise access_error(
                ACCESS_SIGNATURE_REQUIRED, "A valid PoP request signature is required.", 401
            )
    if request.headers.get("x-bastion-intent-signature"):
        context = replace(
            context,
            is_step_up_verified=True,
            metadata={**context.metadata, "human_intent_present": True},
        )
    _check_revocation(context, db)
    _validate_unified_context(context, request)
    request.state.unified_access_context = context
    return context


_POP_HEADER_NAMES = ("timestamp", "nonce", "body_hash", "signature")


def _extract_session_token(request: Request) -> tuple[str | None, bool]:
    authorization = request.headers.get("authorization", "")
    if authorization.startswith("PoP "):
        token = authorization[4:].strip()
        if not token.startswith("sess_"):
            raise access_error(ACCESS_SESSION_INVALID, "PoP Session is invalid.", 401)
        return token, True
    return request.headers.get("x-bastion-session"), False


def _request_header(request: Request, field: str) -> str | None:
    suffix = field.replace("_", "-")
    return request.headers.get(f"bastion-request-{suffix}") or request.headers.get(
        f"x-bastion-{suffix}"
    )


async def _verify_signed_request(
    request: Request, db: Session, *, session_token: str
) -> AccessContext:
    if REQUEST_SIGNATURE_VERIFIER is not None:
        result = REQUEST_SIGNATURE_VERIFIER(request, db)
        return await result if hasattr(result, "__await__") else result
    try:
        from app.services.access.request_verifier import AccessRequestVerifier

        body = await request.body()
        server_pepper = os.getenv("ACCESS_SERVER_PEPPER", "")
        if not server_pepper:
            raise RuntimeError("Access request verifier is not configured")
        headers = dict(request.headers)
        headers.update(
            {
                "x-bastion-session": session_token,
                "x-bastion-timestamp": _request_header(request, "timestamp") or "",
                "x-bastion-nonce": _request_header(request, "nonce") or "",
                "x-bastion-body-hash": _request_header(request, "body_hash") or "",
                "x-bastion-signature": _request_header(request, "signature") or "",
            }
        )
        verified = AccessRequestVerifier(server_pepper=server_pepper).verify(
            db,
            method=request.method,
            path=_canonical_request_target(request),
            body=body,
            headers=headers,
        )
        verified_plan = normalize_plan_code(verified.plan_code)
        overlay = build_entitlement_overlay(verified_plan)
        return AccessContext(
            session_id_hash=verified.session_hash,
            certificate_fingerprint=verified.certificate_fingerprint,
            pass_lookup_hash=verified.pass_lookup_hash,
            device_key_fingerprint=verified.device_key_fingerprint,
            plan_code=verified_plan,
            effective_scopes=set(verified.scopes),
            metric_entitlements={"groups": overlay["metric_groups"]},
            entitlement_status="active",
            session_expires_at=getattr(verified, "expires_at", None) or _far_future(),
            risk_level="low",
            request_id=getattr(request.state, "request_id", None),
            origin=request.headers.get("origin"),
            policy_mode="proof_of_possession",
            is_request_signature_verified=True,
            metadata={"request_digest": verified.request_digest, "requires_request_signing": True},
        )
    except AppError:
        raise
    except Exception as exc:
        raise access_error(
            ACCESS_SIGNATURE_INVALID, "Access request signature is invalid.", 401
        ) from exc


def _context_from_session(session_token: str, request: Request, db: Session) -> AccessContext:
    try:
        session_context = (
            SESSION_CONTEXT_RESOLVER(session_token, db)
            if SESSION_CONTEXT_RESOLVER is not None
            else _default_session_context(session_token, db)
        )
    except Exception as exc:
        code = ACCESS_SESSION_EXPIRED if "expired" in str(exc).lower() else ACCESS_SESSION_INVALID
        raise access_error(code, "Proof-of-Access session is invalid.", 401) from exc
    plan = normalize_plan_code(session_context.plan_code)
    overlay = build_entitlement_overlay(plan)
    return AccessContext(
        session_id_hash=session_context.session_hash,
        certificate_fingerprint=session_context.certificate_fingerprint,
        pass_lookup_hash=session_context.pass_lookup_hash,
        device_key_fingerprint=session_context.device_key_fingerprint,
        plan_code=plan,
        effective_scopes=set(session_context.scopes),
        metric_entitlements={"groups": overlay["metric_groups"]},
        entitlement_status="active",
        session_expires_at=session_context.expires_at or _far_future(),
        risk_level=session_context.risk_level,
        request_id=getattr(request.state, "request_id", None),
        origin=request.headers.get("origin"),
        policy_mode=session_context.policy_mode
        if hasattr(session_context, "policy_mode")
        else "proof_of_access",
        is_request_signature_verified=False,
        metadata={
            "requires_request_signing": getattr(session_context, "requires_request_signing", True),
            "principal_status": getattr(session_context, "principal_status", "active"),
            "device_status": getattr(session_context, "device_status", "active"),
            "session_status": getattr(session_context, "session_status", "active"),
        },
        principal_hash=getattr(session_context, "principal_hash", None),
        principal_type=getattr(session_context, "principal_type", None),
        parent_principal_hash=getattr(session_context, "parent_principal_hash", None),
        auth_method=getattr(session_context, "auth_method", None),
        verification_strength=getattr(session_context, "verification_strength", "standard"),
        device_id_hash=getattr(session_context, "device_id_hash", None),
        subscription_status=getattr(session_context, "subscription_status", "active"),
        business_role=getattr(session_context, "business_role", None),
        payregister_device_hash=getattr(session_context, "payregister_device_hash", None),
        offline_mode=bool(getattr(session_context, "offline_mode", False)),
        sovereign_mode=bool(getattr(session_context, "sovereign_mode", False)),
        last_wallet_proof_at=getattr(session_context, "last_wallet_proof_at", None),
        last_step_up_at=getattr(session_context, "last_step_up_at", None),
        access_integrity_score=getattr(session_context, "access_integrity_score", None),
        policy_epoch=int(getattr(session_context, "policy_epoch", 1)),
        crypto_epoch=int(getattr(session_context, "crypto_epoch", 1)),
    )


def _default_session_context(session_token: str, db: Session) -> Any:
    from app.services.access.session_service import AccessSessionService

    server_pepper = os.getenv("ACCESS_SERVER_PEPPER", "")
    if not server_pepper:
        raise RuntimeError("Access session service is not configured")
    return AccessSessionService(db, server_pepper=server_pepper).validate_session(
        session_token=session_token
    )


def _check_revocation(context: AccessContext, db: Session) -> None:
    if REVOCATION_CHECKER is not None:
        result = REVOCATION_CHECKER(context, db)
    else:
        try:
            from app.services.access.revocation_registry import RevocationRegistry

            result = RevocationRegistry().check_access_material(
                db,
                pass_lookup_hash=context.pass_lookup_hash,
                certificate_fingerprint=context.certificate_fingerprint,
                device_key_fingerprint=context.device_key_fingerprint,
                session_hash=context.session_id_hash,
            )
        except Exception as exc:
            raise access_error(
                ACCESS_REVOCATION_UNAVAILABLE,
                "Revocation state could not be verified.",
                503,
            ) from exc
    if result.get("allowed") is False or result.get("revoked_targets"):
        raise access_error(ACCESS_SESSION_REVOKED, "Access material has been revoked.", 403)


def _canonical_request_target(request: Request) -> str:
    from urllib.parse import quote

    pairs = sorted(request.query_params.multi_items(), key=lambda item: (item[0], item[1]))
    if not pairs:
        return request.url.path
    query = "&".join(f"{quote(key, safe='')}={quote(value, safe='')}" for key, value in pairs)
    return f"{request.url.path}?{query}"


def _validate_unified_context(context: AccessContext, request: Request) -> None:
    expires_at = context.session_expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=UTC)
    if expires_at <= datetime.now(UTC):
        raise access_error(ACCESS_SESSION_EXPIRED, "PoP Session has expired.", 401)
    if context.metadata.get("session_status", "active") != "active":
        raise access_error(ACCESS_SESSION_INVALID, "PoP Session is inactive.", 401)
    principal_status = context.metadata.get("principal_status", "active")
    if principal_status == "recovery_locked":
        raise access_error(ACCESS_RECOVERY_REQUIRED, "Principal recovery is required.", 403)
    if principal_status != "active":
        raise access_error(ACCESS_SESSION_REVOKED, "Principal is inactive.", 403)
    if context.metadata.get("device_status", "active") != "active":
        raise access_error(ACCESS_SESSION_REVOKED, "Device Binding is inactive.", 403)
    if context.metadata.get("lockdown_state") == "active":
        raise access_error(ACCESS_LOCKDOWN_ACTIVE, "Emergency Lockdown is active.", 423)
    claimed_principal = request.headers.get("bastion-principal")
    if claimed_principal and (
        context.principal_hash is None or claimed_principal != context.principal_hash
    ):
        raise access_error(
            ACCESS_PRINCIPAL_MISMATCH,
            "PoP Session principal does not match the request.",
            401,
        )


@classified(RouteClassification.PROTECTED)
async def require_access_session(
    context: Annotated[AccessContext, Depends(get_access_context)],
) -> AccessContext:
    if context.entitlement_status not in {"active", "grace"}:
        raise access_error(ACCESS_SESSION_INVALID, "Access entitlement is inactive.", 403)
    return context


def require_scope(scope: str) -> Any:
    async def dependency(
        context: AccessContext = Depends(require_access_session),
    ) -> AccessContext:
        if scope not in context.effective_scopes:
            raise access_error(ACCESS_SCOPE_MISSING, "Required Access scope is missing.", 403)
        return require_policy_decision(context, requested_scope=scope)

    return dependency


def require_any_plan(plan_codes: list[PlanCode | str]) -> Any:
    required_plans = [normalize_plan_code(plan) for plan in plan_codes]
    minimum = min(required_plans, key=plan_rank)

    async def dependency(
        context: AccessContext = Depends(require_access_session),
    ) -> AccessContext:
        if context.plan_code not in required_plans and plan_rank(context.plan_code) < plan_rank(
            minimum
        ):
            raise access_error(
                ACCESS_UPGRADE_REQUIRED, "One of the required Access plans is needed.", 402
            )
        if context.plan_code not in required_plans and plan_rank(context.plan_code) >= plan_rank(
            minimum
        ):
            return require_policy_decision(context)
        return require_policy_decision(context)

    return dependency


def require_plan(plan_code: PlanCode | str) -> Any:
    required = normalize_plan_code(plan_code)

    async def dependency(
        context: AccessContext = Depends(require_access_session),
    ) -> AccessContext:
        if plan_rank(context.plan_code) < plan_rank(required):
            raise access_error(
                ACCESS_UPGRADE_REQUIRED, f"Access plan {required.value} is required.", 402
            )
        return require_policy_decision(context)

    return dependency


def require_metric_entitlement(metric_group: str) -> Any:
    async def dependency(
        context: AccessContext = Depends(require_access_session),
    ) -> AccessContext:
        groups = set(context.metric_entitlements.get("groups", []))
        if metric_group not in groups:
            required_plan = required_plan_for_metric_group(metric_group)
            code = (
                ACCESS_UPGRADE_REQUIRED
                if required_plan and plan_rank(required_plan) > plan_rank(context.plan_code)
                else ACCESS_METRIC_NOT_ALLOWED
            )
            raise access_error(
                code,
                "Metric entitlement is not available for this Access plan.",
                402 if code == ACCESS_UPGRADE_REQUIRED else 403,
            )
        return require_policy_decision(context, requested_metric_group=metric_group)

    return dependency


def require_policy_decision(
    access_context: AccessContext | str | None = None,
    *,
    requested_scope: str | None = None,
    requested_metric_group: str | None = None,
    requested_object_type: str | None = None,
    requested_object_id_hash: str | None = None,
    action: str | None = None,
    risk_level: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> AccessContext | Any:
    if not isinstance(access_context, AccessContext):
        declared_action = access_context if isinstance(access_context, str) else action

        async def dependency(
            context: AccessContext = Depends(require_access_session),
        ) -> AccessContext:
            return require_policy_decision(
                context,
                requested_scope=requested_scope,
                requested_metric_group=requested_metric_group,
                requested_object_type=requested_object_type,
                requested_object_id_hash=requested_object_id_hash,
                action=declared_action,
                risk_level=risk_level,
                metadata=metadata,
            )

        classified(RouteClassification.PROTECTED)(dependency)
        return dependency

    policy_context = AccessPolicyContext(
        actor_type=access_context.principal_type,
        actor_hash=access_context.principal_hash,
        principal_hash=access_context.principal_hash,
        principal_type=str(access_context.principal_type)
        if access_context.principal_type is not None
        else None,
        parent_actor_hash=access_context.parent_principal_hash,
        auth_methods=frozenset({access_context.auth_method})
        if access_context.auth_method is not None
        else frozenset(),
        primary_auth_method=access_context.auth_method,
        authentication_assurance=access_context.verification_strength,
        actor_status=str(access_context.metadata.get("principal_status", "active")),
        requested_action=action,
        policy_epoch=access_context.policy_epoch,
        access_integrity_score=access_context.access_integrity_score,
        access_certificate_fingerprint=access_context.certificate_fingerprint or None,
        certificate_fingerprint=access_context.certificate_fingerprint,
        pass_lookup_hash=access_context.pass_lookup_hash,
        plan_code=access_context.plan_code,
        effective_scopes=access_context.effective_scopes,
        requested_scope=requested_scope,
        requested_metric_group=requested_metric_group,
        requested_object_type=requested_object_type,
        requested_object_id_hash=requested_object_id_hash,
        request_risk_level=risk_level or access_context.risk_level,
        session_id_hash=access_context.session_id_hash,
        session_status="active",
        session_expires_at=access_context.session_expires_at,
        device_id=access_context.device_id_hash,
        device_status=str(access_context.metadata.get("device_status", "active")),
        entitlement_status=access_context.entitlement_status,
        metric_entitlements=access_context.metric_entitlements,
        revocation_state={"allowed": True, "revoked_targets": []},
        offline_mode=access_context.offline_mode or bool((metadata or {}).get("offline_mode")),
        business_role=access_context.business_role,
        recovery_state=str(access_context.metadata.get("recovery_state", "normal")),
        is_critical_action=bool(action in CRITICAL_ACTIONS),
        step_up_present=access_context.is_step_up_verified
        or access_context.is_request_signature_verified,
        human_intent_verified=access_context.is_step_up_verified,
        metadata={**access_context.metadata, **(metadata or {}), "action": action}
        if action
        else {**access_context.metadata, **(metadata or {})},
    )
    decision = POLICY_ENGINE_FACTORY().evaluate(policy_context)
    if decision.allowed:
        return access_context
    raise _policy_error(decision.decision, decision.reason_code, decision.human_reason)


def require_signed_request_for_critical_action(action: str) -> Any:
    async def dependency(
        context: AccessContext = Depends(require_access_session),
    ) -> AccessContext:
        if not context.is_request_signature_verified:
            raise access_error(
                ACCESS_SIGNATURE_REQUIRED,
                "Critical Access action requires signed Bastion request headers.",
                403,
            )
        return require_policy_decision(context, action=action, risk_level="high")

    return dependency


def require_human_intent(action: str) -> Any:
    async def dependency(
        context: AccessContext = Depends(require_signed_request_for_critical_action(action)),
    ) -> AccessContext:
        if not context.is_step_up_verified:
            raise access_error(
                ACCESS_STEP_UP_REQUIRED,
                "Critical Access action requires Human Intent Signature.",
                403,
            )
        return require_policy_decision(
            context, action=action, risk_level="high", metadata={"human_intent_required": True}
        )

    return dependency


def require_business_role(role: str) -> Any:
    async def dependency(
        context: AccessContext = Depends(require_access_session),
    ) -> AccessContext:
        roles = context.metadata.get("business_roles", [])
        if role not in roles and "owner" not in roles:
            raise access_error(
                ACCESS_BUSINESS_ROLE_REQUIRED, "Required business role is missing.", 403
            )
        return require_policy_decision(context, metadata={"business_role_required": role})

    return dependency


def require_business_policy(action: str, *, roles: tuple[str, ...] = ("owner", "admin")) -> Any:
    async def dependency(
        context: AccessContext = Depends(require_access_session),
    ) -> AccessContext:
        effective_roles = set(context.metadata.get("business_roles", ()))
        if context.business_role:
            effective_roles.add(context.business_role)
        if not effective_roles.intersection(roles):
            raise access_error(
                ACCESS_BUSINESS_ROLE_REQUIRED, "Business policy role is not available.", 403
            )
        return require_policy_decision(
            context,
            action=action,
            metadata={"business_role": sorted(effective_roles)[0]},
        )

    classified(RouteClassification.BUSINESS)(dependency)
    return dependency


def require_payregister_device(action: str = "payregister_terminal_operation") -> Any:
    async def dependency(
        context: AccessContext = Depends(require_access_session),
    ) -> AccessContext:
        if not context.payregister_device_hash:
            raise access_error(
                ACCESS_BUSINESS_ROLE_REQUIRED, "An active PayRegister Device is required.", 403
            )
        if context.metadata.get("payregister_device_status", "active") != "active":
            raise access_error(ACCESS_SESSION_REVOKED, "PayRegister Device is inactive.", 403)
        return require_policy_decision(
            context,
            action=action,
            requested_object_type="payregister_device",
            requested_object_id_hash=context.payregister_device_hash,
        )

    classified(RouteClassification.BUSINESS)(dependency)
    return dependency


_OFFLINE_FORBIDDEN_ACTIONS = frozenset(
    {
        "treasury_policy_change",
        "add_device",
        "device_add",
        "recovery_change",
        "recovery_complete",
        "lockdown_release",
        "business_role_assignment",
        "increase_scope",
        "create_api_key",
        "create_delegated_pass",
        "enterprise_policy_change",
    }
)


def require_offline_policy(action: str, *, required_scope: str | None = None) -> Any:
    async def dependency(
        context: AccessContext = Depends(require_access_session),
    ) -> AccessContext:
        if not context.offline_mode:
            return require_policy_decision(context, action=action, requested_scope=required_scope)
        offline_scopes = set(context.metadata.get("offline_scopes", ()))
        if action in _OFFLINE_FORBIDDEN_ACTIONS or (
            required_scope is not None and required_scope not in offline_scopes
        ):
            raise access_error(ACCESS_POLICY_DENIED, "Operation is not permitted offline.", 403)
        if not context.metadata.get("offline_pack_verified", False):
            raise access_error(ACCESS_POLICY_DENIED, "Offline Validity Pack is invalid.", 403)
        return require_policy_decision(
            context,
            action=action,
            requested_scope=required_scope,
            metadata={"offline_mode": True},
        )

    classified(RouteClassification.PROTECTED)(dependency)
    return dependency


def require_withdraw_authorization(
    *, action: str = "valuable_lnurl_withdraw", max_age_seconds: int = 300
) -> Any:
    async def dependency(
        context: AccessContext = Depends(require_access_session),
    ) -> AccessContext:
        _validate_fresh_step_up(context, action, max_age_seconds=max_age_seconds)
        roles = set(context.metadata.get("business_roles", ()))
        if context.business_role:
            roles.add(context.business_role)
        if not roles.intersection({"owner", "admin", "operator"}):
            raise access_error(
                ACCESS_BUSINESS_ROLE_REQUIRED, "Withdraw authorization role is required.", 403
            )
        return require_policy_decision(context, action=action, risk_level="high")

    classified(RouteClassification.HIGH_RISK)(dependency)
    return dependency


def require_enterprise_policy(permission: str) -> Any:
    async def dependency(
        context: AccessContext = Depends(require_plan(PlanCode.ENTERPRISE)),
    ) -> AccessContext:
        permissions = context.metadata.get("enterprise_permissions", [])
        if (
            permission not in permissions
            and "enterprise:policy:custom" not in context.effective_scopes
        ):
            raise access_error(
                ACCESS_ENTERPRISE_POLICY_REQUIRED,
                "Required enterprise policy permission is missing.",
                403,
            )
        return require_policy_decision(
            context,
            requested_scope="enterprise:policy:custom",
            metadata={"enterprise_permission": permission},
        )

    return dependency


def require_step_up_for_critical_action(action: str) -> Any:
    async def dependency(
        context: AccessContext = Depends(require_access_session),
    ) -> AccessContext:
        if not context.is_request_signature_verified:
            raise access_error(
                ACCESS_SIGNATURE_REQUIRED,
                "Critical Access action requires signed Bastion request headers.",
                403,
            )
        _validate_fresh_step_up(context, action, max_age_seconds=300)
        return require_policy_decision(context, action=action, risk_level="high")

    return dependency


def require_step_up_for_action(action: str) -> Any:
    """Centralized step-up dependency; endpoints declare only the action."""
    return require_step_up_for_critical_action(action)


def require_fresh_lnurl_auth(action: str) -> Any:
    async def dependency(context: AccessContext = Depends(require_access_session)) -> AccessContext:
        _validate_fresh_step_up(
            context, action, max_age_seconds=300, accepted_methods={"lnurl_auth"}
        )
        return require_policy_decision(context, action=action, risk_level="high", metadata={"required_step_up_method": "fresh_lnurl_auth"})

    return dependency


def require_fresh_bip322(action: str) -> Any:
    async def dependency(context: AccessContext = Depends(require_access_session)) -> AccessContext:
        _validate_fresh_step_up(
            context, action, max_age_seconds=300, accepted_methods={"bip322"}
        )
        return require_policy_decision(context, action=action, risk_level="high", metadata={"required_step_up_method": "fresh_bip322"})

    return dependency


def require_dual_method(action: str) -> Any:
    async def dependency(context: AccessContext = Depends(require_access_session)) -> AccessContext:
        return require_policy_decision(context, action=action, risk_level="high", metadata={"required_step_up_method": "dual_method"})

    return dependency


def require_quorum(action: str) -> Any:
    async def dependency(context: AccessContext = Depends(require_access_session)) -> AccessContext:
        return require_policy_decision(context, action=action, risk_level="critical", metadata={"required_step_up_method": "multi_wallet_quorum"})

    return dependency


def require_fresh_wallet_step_up(action: str, max_age_seconds: int = 300) -> Any:
    async def dependency(
        context: AccessContext = Depends(require_access_session),
    ) -> AccessContext:
        _validate_fresh_step_up(context, action, max_age_seconds=max_age_seconds)
        return require_policy_decision(context, action=action, risk_level="high")

    classified(RouteClassification.HIGH_RISK)(dependency)
    return dependency


def _validate_fresh_step_up(
    context: AccessContext,
    action: str,
    *,
    max_age_seconds: int,
    accepted_methods: set[str] | None = None,
) -> None:
    evidence = context.metadata.get("step_up_evidence")
    if (
        not isinstance(evidence, dict)
        and context.principal_type is None
        and context.metadata.get("human_intent_present")
    ):
        # Access v1 certificate compatibility only. Wallet/LNURL principals
        # always require persisted action-bound evidence.
        evidence = {
            "action": action,
            "intent_hash": "legacy-access-v1-intent",
            "method": "access_certificate",
            "verified_at": datetime.now(UTC),
            "status": "active",
        }
    if not isinstance(evidence, dict) or not context.is_step_up_verified:
        raise access_error(ACCESS_STEP_UP_REQUIRED, "Fresh action-bound step-up is required.", 403)
    if evidence.get("action") != action or not evidence.get("intent_hash"):
        raise access_error(ACCESS_STEP_UP_REQUIRED, "Step-up does not match this action.", 403)
    method = str(evidence.get("method", ""))
    if accepted_methods is not None and method not in accepted_methods:
        raise access_error(ACCESS_STEP_UP_REQUIRED, "Step-up assurance is insufficient.", 403)
    if evidence.get("status", "active") != "active" or evidence.get("revoked", False):
        raise access_error(ACCESS_STEP_UP_REQUIRED, "Step-up is inactive.", 403)
    verified_at = evidence.get("verified_at") or context.last_step_up_at
    if isinstance(verified_at, str):
        try:
            verified_at = datetime.fromisoformat(verified_at.replace("Z", "+00:00"))
        except ValueError as exc:
            raise access_error(ACCESS_STEP_UP_REQUIRED, "Step-up freshness is invalid.", 403) from exc
    if not isinstance(verified_at, datetime):
        raise access_error(ACCESS_STEP_UP_REQUIRED, "Step-up freshness is unavailable.", 403)
    if verified_at.tzinfo is None:
        verified_at = verified_at.replace(tzinfo=UTC)
    age = (datetime.now(UTC) - verified_at.astimezone(UTC)).total_seconds()
    if age < 0 or age > max_age_seconds:
        raise access_error(ACCESS_STEP_UP_REQUIRED, "Step-up has expired.", 403)


def _policy_error(decision: str, reason_code: str, message: str) -> AppError:
    mapping = {
        "upgrade_required": (ACCESS_UPGRADE_REQUIRED, 402),
        "step_up_required": (ACCESS_STEP_UP_REQUIRED, 403),
        "quota_exceeded": (ACCESS_QUOTA_EXCEEDED, 429),
        "metric_not_allowed": (ACCESS_METRIC_NOT_ALLOWED, 403),
        "revoked": (ACCESS_SESSION_REVOKED, 403),
        "expired": (ACCESS_SESSION_EXPIRED, 401),
        "recovery_required": (ACCESS_RECOVERY_REQUIRED, 403),
        "online_check_required": (ACCESS_POLICY_DENIED, 403),
    }
    code, status_code = mapping.get(
        decision,
        (ACCESS_POLICY_DENIED if reason_code != "scope_not_allowed" else ACCESS_SCOPE_MISSING, 403),
    )
    return access_error(code, message, status_code)


def _far_future() -> Any:
    from datetime import UTC, datetime, timedelta

    return datetime.now(UTC) + timedelta(minutes=15)
