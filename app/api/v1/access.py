"""Proof-of-Access API router.

This router exposes the Bastion Access lifecycle without accepting passwords,
email ownership, Bitcoin seeds/private keys, or bearer Access Pass semantics.
Route handlers intentionally orchestrate services only; cryptographic and policy
logic stays inside the Access service layer.
"""

from __future__ import annotations

import os
from datetime import UTC, datetime, timedelta
from dataclasses import asdict
from typing import Annotated, Any, cast

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.models.access import AccessCertificate, AccessDevice, AccessPaymentIntent, SubscriptionEntitlement
from app.db.session import get_db
from app.domain.access.plans import PlanCode, normalize_plan_code
from app.schemas.access import (
    AccessCertificateIssueRequest,
    AccessCertificateIssueResponse,
    AccessChallengeCreate,
    AccessChallengeResponse,
    AccessLimitsResponse,
    AccessLockdownResponse,
    AccessMeResponse,
    AccessPaymentIntentCreate,
    AccessPaymentIntentResponse,
    AccessPaymentIntentStatusResponse,
    AccessSessionCreate,
    AccessSessionResponse,
    SubscriptionEntitlementResponse,
)
from app.services.access.metric_catalog import list_locked_metric_groups
from app.services.access.plan_entitlements import build_entitlement_overlay
from app.services.access.payments.base import (
    PAYMENT_STATUS_PAID,
    ManualGrantsDisabledError,
    PaymentIntentNotFoundError,
    PaymentProviderDisabledError,
    PaymentProviderNotConfiguredError,
)
from app.services.access.payments.manual import ManualGrantProvider

router = APIRouter(prefix="/access", tags=["proof-of-access"])

_PLAN_PRICES_SATS: dict[PlanCode, int] = {
    PlanCode.LITE: 1_000,
    PlanCode.BASIC: 10_000,
    PlanCode.PLUS: 50_000,
    PlanCode.PRO: 250_000,
    PlanCode.BUSINESS: 1_000_000,
    PlanCode.ENTERPRISE: 5_000_000,
}


def _http_error(code: str, http_status: int, detail: str | None = None) -> HTTPException:
    return HTTPException(status_code=http_status, detail={"code": code, "message": detail or code})


def _safe_metadata(metadata: dict[str, Any] | None) -> dict[str, Any]:
    forbidden = {"password", "email", "bitcoin_seed", "bitcoin_private_key", "seed_phrase", "private_key", "raw_access_pass", "session_token"}
    data = metadata or {}
    if forbidden & {key.lower() for key in data}:
        raise _http_error("unsafe_metadata", status.HTTP_400_BAD_REQUEST, "Access metadata contains forbidden secret fields")
    return data


def _payment_providers() -> dict[str, Any]:
    settings = get_settings()
    providers: dict[str, Any] = {
        "manual": ManualGrantProvider(
            allow_manual_grants=settings.access_allow_manual_grants,
            environment=settings.environment,
            invoice_ttl_seconds=settings.access_payment_intent_ttl_seconds,
        )
    }
    if settings.access_btcpay_enabled:
        from app.services.access.payments.btcpay import BTCPayAccessPaymentProvider

        btcpay = BTCPayAccessPaymentProvider(
            enabled=settings.access_btcpay_enabled,
            base_url=settings.access_btcpay_base_url,
            api_key=settings.access_btcpay_api_key,
            store_id=settings.access_btcpay_store_id,
            webhook_secret=settings.access_btcpay_webhook_secret,
            default_currency=settings.access_btcpay_default_currency,
            checkout_expiry_minutes=settings.access_btcpay_checkout_expiry_minutes,
            http_timeout_seconds=settings.access_btcpay_http_timeout_seconds,
            webhook_tolerance_seconds=settings.access_btcpay_webhook_tolerance_seconds,
        )
        providers["btcpay"] = btcpay
        providers["bitcoin_lightning"] = btcpay
    return providers


def get_payment_intent_service(db: Annotated[Session, Depends(get_db)]) -> Any:
    from app.services.access.payment_intent_service import PaymentIntentService

    return PaymentIntentService(db, _payment_providers())


def get_certificate_issuer(db: Annotated[Session, Depends(get_db)]) -> Any:
    from app.services.access.certificate_issuer import AccessCertificateIssuer

    settings = get_settings()
    issuer_private_key = os.getenv("ACCESS_ISSUER_PRIVATE_KEY", "")
    issuer_key_id = os.getenv("ACCESS_ISSUER_KEY_ID", "access-issuer-v1")
    server_pepper = os.getenv("ACCESS_SERVER_PEPPER", "")
    if not issuer_private_key or not server_pepper:
        raise _http_error("issuer_key_unavailable", status.HTTP_503_SERVICE_UNAVAILABLE, "Access issuer is not configured")
    return AccessCertificateIssuer(
        db,
        server_pepper=server_pepper,
        issuer_private_key=issuer_private_key,
        issuer_key_id=issuer_key_id,
        issuer_public_key=os.getenv("ACCESS_ISSUER_PUBLIC_KEY") or None,
        crypto_epoch=int(os.getenv("ACCESS_CRYPTO_EPOCH", "1")),
        allow_manual_grants=settings.access_allow_manual_grants,
    )


def get_entitlement_service(db: Annotated[Session, Depends(get_db)]) -> Any:
    from app.services.access.entitlement_service import SubscriptionEntitlementService

    issuer_private_key = os.getenv("ACCESS_ISSUER_PRIVATE_KEY", "")
    issuer_key_id = os.getenv("ACCESS_ISSUER_KEY_ID", "access-issuer-v1")
    if not issuer_private_key:
        raise _http_error("issuer_key_unavailable", status.HTTP_503_SERVICE_UNAVAILABLE, "Access entitlement issuer is not configured")
    return SubscriptionEntitlementService(
        db,
        issuer_private_key=issuer_private_key,
        issuer_key_id=issuer_key_id,
        issuer_public_key=os.getenv("ACCESS_ISSUER_PUBLIC_KEY") or None,
        crypto_epoch=int(os.getenv("ACCESS_CRYPTO_EPOCH", "1")),
    )


def get_challenge_service(db: Annotated[Session, Depends(get_db)]) -> Any:
    from app.services.access.challenge_service import AccessChallengeService

    return AccessChallengeService(db, challenge_ttl_seconds=get_settings().access_challenge_ttl_seconds)


def get_session_service(db: Annotated[Session, Depends(get_db)]) -> Any:
    from app.services.access.session_service import AccessSessionService

    server_pepper = os.getenv("ACCESS_SERVER_PEPPER", "")
    if not server_pepper:
        raise _http_error("session_service_unavailable", status.HTTP_503_SERVICE_UNAVAILABLE, "Access session service is not configured")
    return AccessSessionService(db, server_pepper=server_pepper, session_ttl_seconds=get_settings().access_session_ttl_seconds)


def get_access_session_context(
    session_token: Annotated[str | None, Header(alias="X-Bastion-Session")] = None,
    db: Annotated[Session | None, Depends(get_db)] = None,
) -> Any:
    if not session_token:
        raise _http_error("session_required", status.HTTP_401_UNAUTHORIZED, "Proof-of-Access session is required")
    try:
        from app.services.access.session_service import AccessSessionService

        server_pepper = os.getenv("ACCESS_SERVER_PEPPER", "")
        if not server_pepper:
            raise RuntimeError("Access session service is not configured")
        if db is None:
            raise RuntimeError("Access database session is not available")
        return AccessSessionService(db, server_pepper=server_pepper, session_ttl_seconds=get_settings().access_session_ttl_seconds).validate_session(session_token=session_token)
    except Exception as exc:
        raise _http_error("session_expired", status.HTTP_401_UNAUTHORIZED, "Proof-of-Access session is invalid") from exc


@router.post(
    "/payment-intents",
    response_model=AccessPaymentIntentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create an Access payment intent; invoice creation is not proof of payment.",
)
def create_payment_intent(
    request: AccessPaymentIntentCreate,
    service: Annotated[Any, Depends(get_payment_intent_service)],
) -> AccessPaymentIntentResponse:
    try:
        plan = normalize_plan_code(request.plan_code)
        amount_sats = request.amount_sats or _PLAN_PRICES_SATS[plan]
        intent = service.create_payment_intent(plan, request.payment_method, amount_sats, _safe_metadata(request.metadata))
        _commit_service(service)
    except (ValueError, ManualGrantsDisabledError, PaymentProviderDisabledError, PaymentProviderNotConfiguredError) as exc:
        raise _http_error("payment_provider_unavailable", status.HTTP_400_BAD_REQUEST, str(exc)) from exc
    return _payment_intent_response(intent, certificate_available=False)


@router.get(
    "/payment-intents/{payment_intent_id}",
    response_model=AccessPaymentIntentStatusResponse,
    summary="Read payment intent status without issuing access.",
)
def get_payment_intent_status(payment_intent_id: int, service: Annotated[Any, Depends(get_payment_intent_service)]) -> AccessPaymentIntentStatusResponse:
    try:
        intent = service.get_payment_intent(payment_intent_id)
    except PaymentIntentNotFoundError as exc:
        raise _http_error("payment_intent_not_found", status.HTTP_404_NOT_FOUND) from exc
    if intent is None:
        raise _http_error("payment_intent_not_found", status.HTTP_404_NOT_FOUND)
    return AccessPaymentIntentStatusResponse(**_payment_intent_response(intent, certificate_available=intent.status == PAYMENT_STATUS_PAID).model_dump())


@router.post("/certificates", response_model=AccessCertificateIssueResponse, summary="Issue an Access Certificate after verified payment settlement.")
def issue_certificate(
    request: AccessCertificateIssueRequest,
    db: Annotated[Session, Depends(get_db)],
    issuer: Annotated[Any, Depends(get_certificate_issuer)],
    entitlement_service: Annotated[Any, Depends(get_entitlement_service)],
) -> AccessCertificateIssueResponse:
    try:
        result = issuer.issue_certificate_for_paid_intent(
            request.payment_intent_id,
            device_public_key=request.device_public_key,
            device_key_fingerprint=request.device_key_fingerprint,
            device_class=request.device_class,
        )
        certificate = db.execute(select(AccessCertificate).where(AccessCertificate.certificate_fingerprint == result.certificate_fingerprint)).scalar_one()
        _register_initial_device(db, certificate, request)
        valid_from = datetime.now(UTC)
        entitlement = entitlement_service.issue_entitlement(
            pass_lookup_hash=certificate.pass_lookup_hash,
            certificate_fingerprint=certificate.certificate_fingerprint,
            plan_code=certificate.plan_code,
            valid_from=valid_from,
            valid_until=valid_from + timedelta(days=request.subscription_period_days),
            payment_intent_id=request.payment_intent_id,
            metadata={"requested_origin": request.requested_origin} if request.requested_origin else None,
        )
        db.commit()
        return _certificate_response(result.raw_access_pass, result.access_certificate, certificate, entitlement, result.save_warning)
    except Exception as exc:
        db.rollback()
        if exc.__class__.__name__ == "PaymentNotSettledError":
            raise _http_error("payment_not_settled", status.HTTP_402_PAYMENT_REQUIRED) from exc
        if exc.__class__.__name__ == "CertificateAlreadyIssuedError":
            intent = db.get(AccessPaymentIntent, request.payment_intent_id)
            fingerprint = (intent.metadata_json or {}).get("access_certificate_fingerprint") if intent else None
            existing_certificate = db.execute(select(AccessCertificate).where(AccessCertificate.certificate_fingerprint == fingerprint)).scalar_one_or_none() if fingerprint else None
            if existing_certificate is None:
                raise _http_error("certificate_already_issued", status.HTTP_409_CONFLICT) from exc
            entitlement = db.execute(select(SubscriptionEntitlement).where(SubscriptionEntitlement.certificate_fingerprint == existing_certificate.certificate_fingerprint)).scalars().first()
            return _certificate_response(None, {}, existing_certificate, entitlement, "Access Pass was already shown once and cannot be returned again.")
        raise _http_error("certificate_issue_failed", status.HTTP_400_BAD_REQUEST, str(exc)) from exc


@router.post("/challenges", response_model=AccessChallengeResponse, summary="Create an origin-bound one-time Access challenge.")
def create_challenge(request: AccessChallengeCreate, service: Annotated[Any, Depends(get_challenge_service)]) -> AccessChallengeResponse:
    try:
        result = service.create_challenge(
            certificate_fingerprint=request.certificate_fingerprint,
            origin=request.origin,
            requested_scopes=request.requested_scopes,
            device_key_fingerprint=request.device_key_fingerprint,
        )
        _commit_service(service)
    except Exception as exc:
        raise _http_error(_safe_error_code(exc), status.HTTP_403_FORBIDDEN) from exc
    return AccessChallengeResponse(**asdict(result))


@router.post("/sessions", response_model=AccessSessionResponse, summary="Create a short-lived Proof-of-Possession session from a signed challenge.")
def create_session(request: AccessSessionCreate, service: Annotated[Any, Depends(get_session_service)]) -> AccessSessionResponse:
    try:
        result = service.create_session_from_challenge(**request.model_dump())
        _commit_service(service)
    except Exception as exc:
        raise _http_error(_safe_error_code(exc), status.HTTP_403_FORBIDDEN) from exc
    return AccessSessionResponse(**asdict(result))


@router.get("/me", response_model=AccessMeResponse, summary="Return the current Proof-of-Access subject state.")
def get_me(context: Annotated[Any, Depends(get_access_session_context)]) -> AccessMeResponse:
    return AccessMeResponse(
        certificate_fingerprint=context.certificate_fingerprint,
        plan_code=context.plan_code,
        entitlement_status="active",
        active_scopes=context.scopes,
        device_status="active",
        session_expires_at=context.expires_at,
        access_integrity_summary={"requires_request_signing": context.requires_request_signing, "risk_level": context.risk_level},
        recovery_status_summary={"configured": False, "recommended": True},
    )


@router.get("/me/entitlements", response_model=SubscriptionEntitlementResponse, summary="Return current Access subscription entitlements.")
def get_my_entitlements(
    context: Annotated[Any, Depends(get_access_session_context)],
    db: Annotated[Session, Depends(get_db)],
) -> SubscriptionEntitlementResponse:
    entitlement = db.get(SubscriptionEntitlement, context.entitlement_id) if context.entitlement_id is not None else None
    if entitlement is None:
        entitlement = db.execute(select(SubscriptionEntitlement).where(SubscriptionEntitlement.certificate_fingerprint == context.certificate_fingerprint)).scalars().first()
    if entitlement is None:
        raise _http_error("entitlement_expired", status.HTTP_403_FORBIDDEN)
    return _entitlement_response(entitlement)


@router.get("/me/limits", response_model=AccessLimitsResponse, summary="Return effective API and metric limits for the current Access Pass.")
def get_my_limits(context: Annotated[Any, Depends(get_access_session_context)]) -> AccessLimitsResponse:
    overlay = build_entitlement_overlay(context.plan_code)
    limits = overlay["limits"]
    return AccessLimitsResponse(plan_code=context.plan_code, limits=limits, offline_validity_status=limits.get("offline_validity_pack"))


@router.post("/lockdown", response_model=AccessLockdownResponse, summary="Start Emergency Lockdown Mode for the current Access Certificate.")
def lockdown(
    context: Annotated[Any, Depends(get_access_session_context)],
    service: Annotated[Any, Depends(get_session_service)],
) -> AccessLockdownResponse:
    frozen = service.freeze_sessions_for_certificate(certificate_fingerprint=context.certificate_fingerprint, reason="user_lockdown")
    _commit_service(service)
    return AccessLockdownResponse(status="locked_down", frozen_sessions=frozen, certificate_fingerprint=context.certificate_fingerprint)


@router.post("/payments/btcpay/webhook", status_code=status.HTTP_202_ACCEPTED, summary="Receive verified BTCPay payment webhooks without issuing certificates.")
async def btcpay_webhook(request: Request, service: Annotated[Any, Depends(get_payment_intent_service)]) -> dict[str, str]:
    providers = getattr(service, "providers", {})
    provider = providers.get("btcpay")
    if provider is None:
        raise _http_error("payment_provider_unavailable", status.HTTP_503_SERVICE_UNAVAILABLE)
    payload = await request.body()
    headers = dict(request.headers)
    if not provider.verify_webhook(payload, headers):
        raise _http_error("payment_webhook_invalid", status.HTTP_400_BAD_REQUEST)
    event = provider.parse_webhook_event(payload, headers)
    try:
        if event.settled:
            service.mark_paid_from_verified_event(event.provider, event.provider_invoice_id, event)
        elif event.expired:
            intent = service._get_by_provider_invoice(event.provider, event.provider_invoice_id)  # noqa: SLF001 - provider boundary endpoint
            service.expire_payment_intent(intent.id)
        elif event.invalid:
            service.mark_invalid_from_verified_event(event.provider, event.provider_invoice_id, event)
        _commit_service(service)
    except Exception as exc:
        raise _http_error("payment_event_ignored", status.HTTP_202_ACCEPTED, str(exc)) from exc
    return {"status": "accepted"}


def _commit_service(service: Any) -> None:
    db = getattr(service, "db", None)
    if db is not None and hasattr(db, "commit"):
        db.commit()


def _payment_intent_response(intent: AccessPaymentIntent, *, certificate_available: bool) -> AccessPaymentIntentResponse:
    return AccessPaymentIntentResponse(
        payment_intent_id=intent.id,
        status=intent.status,
        provider=intent.provider,
        payment_method=intent.payment_method,
        amount_sats=intent.amount_sats,
        plan_code=normalize_plan_code(intent.plan_code),
        checkout_url=None,
        expires_at=intent.expires_at,
        certificate_available=certificate_available,
    )


def _register_initial_device(db: Session, certificate: AccessCertificate, request: AccessCertificateIssueRequest) -> AccessDevice:
    fingerprint = request.device_key_fingerprint or certificate.device_key_fingerprint
    if not fingerprint:
        raise _http_error("device_required", status.HTTP_400_BAD_REQUEST)
    existing = db.execute(select(AccessDevice).where(AccessDevice.device_key_fingerprint == fingerprint)).scalar_one_or_none()
    if existing is not None:
        return existing
    now = datetime.now(UTC)
    device = AccessDevice(
        certificate_fingerprint=certificate.certificate_fingerprint,
        device_key_fingerprint=fingerprint,
        device_public_key=request.device_public_key,
        device_class=request.device_class,
        attestation_type=request.device_attestation.get("type") if isinstance(request.device_attestation, dict) else None,
        status="active",
        first_seen_at=now,
        last_seen_at=now,
        risk_score=10,
        metadata_json={"registered_via": "access_certificate_issue"},
        created_at=now,
        updated_at=now,
    )
    db.add(device)
    db.flush()
    certificate.primary_device_id = device.id
    return device


def _certificate_response(
    raw_access_pass: str | None,
    access_certificate: dict[str, Any],
    certificate: AccessCertificate,
    entitlement: SubscriptionEntitlement | None,
    save_warning: str,
) -> AccessCertificateIssueResponse:
    return AccessCertificateIssueResponse(
        raw_access_pass=raw_access_pass,
        access_certificate=access_certificate,
        certificate_fingerprint=certificate.certificate_fingerprint,
        plan_code=normalize_plan_code(certificate.plan_code),
        expires_at=certificate.expires_at,
        save_warning=save_warning,
        subscription_entitlement=_entitlement_response(entitlement) if entitlement is not None else None,
        recovery_setup_recommended=True,
    )


def _entitlement_response(entitlement: SubscriptionEntitlement) -> SubscriptionEntitlementResponse:
    return SubscriptionEntitlementResponse(
        plan_code=normalize_plan_code(entitlement.plan_code),
        status=entitlement.status,
        valid_from=entitlement.valid_from,
        valid_until=entitlement.valid_until,
        grace_until=entitlement.grace_until,
        metric_groups=list((entitlement.metric_entitlements_json or {}).get("groups", [])),
        scopes=[scope for scope in (entitlement.scopes_json or []) if isinstance(scope, str)],
        limits=entitlement.limits_json or {},
        crypto_epoch=entitlement.crypto_epoch,
        issuer_key_id=entitlement.issuer_key_id,
        created_at=entitlement.created_at,
        locked_metric_groups=[_locked_metric_group_payload(item) for item in list_locked_metric_groups(normalize_plan_code(entitlement.plan_code))],
    )


def _locked_metric_group_payload(item: Any) -> dict[str, Any]:
    if hasattr(item, "model_dump"):
        return cast(dict[str, Any], item.model_dump())
    return {"group_code": item.group_code, "required_plan": item.required_plan, "reason": getattr(item, "reason", "upgrade_required")}


def _safe_error_code(exc: Exception) -> str:
    text = str(exc) or exc.__class__.__name__
    if any(secret in text.lower() for secret in ("pass", "token", "private", "seed")):
        return exc.__class__.__name__.replace("Error", "").lower()
    return text
