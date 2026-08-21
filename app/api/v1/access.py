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

from fastapi import APIRouter, Body, Depends, Header, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.models.access import AccessCertificate, AccessCheckoutSession, AccessDevice, AccessIssuedGrant, AccessPaymentIntent, ChildApiKey, DelegatedPass, SubscriptionEntitlement
from app.db.session import get_db
from app.domain.access.plans import PlanCode, normalize_plan_code
from app.schemas.access_intent import HumanIntentCreateRequest, HumanIntentResponse, HumanIntentSignatureRequest, HumanIntentVerificationResult
from app.schemas.access import (
    AccessCertificateIssueRequest,
    AccessCertificateIssueResponse,
    AccessChallengeCreate,
    AccessChallengeResponse,
    AccessLimitsResponse,
    AccessLockdownRequest,
    AccessLockdownResponse,
    AccessMeResponse,
    AccessPaymentIntentCreate,
    AccessPaymentIntentResponse,
    AccessPaymentIntentStatusResponse,
    AccessSessionCreate,
    AccessSessionResponse,
    ChildApiKeyCreate,
    ChildApiKeyCreateResponse,
    ChildApiKeyPublic,
    DelegatedPassCreate,
    DelegatedPassCreateResponse,
    DelegatedPassPublic,
    RecoveryCancelRequest,
    RecoveryCompleteRequest,
    RecoveryCompleteResponse,
    RecoveryFactorSubmitRequest,
    RecoveryFactorSubmitResponse,
    RecoveryRotateRequest,
    RecoveryRotateResponse,
    RecoverySetupRequest,
    RecoverySetupResponse,
    RecoveryStartRequest,
    RecoveryStartResponse,
    RecoveryStatusResponse,
    SubscriptionEntitlementResponse,
)
from app.schemas.access_checkout import (
    AccessIssueRequest,
    AccessOfferOut,
    CheckoutCreateRequest,
    CheckoutOut,
    IssuanceChallengeCreateRequest,
    IssuanceChallengeOut,
    IssuedAccessOut,
)
from app.services.access.checkout_service import AccessCheckoutService
from app.services.access.offer_catalog import PLAN_PRICES_SATS, get_offer, list_offers
from app.services.access.issuance_service import AccessIssuanceService
from app.services.access.metric_catalog import list_locked_metric_groups
from app.services.access.policy_context import AccessPolicyContext
from app.services.access.policy_engine import AccessPolicyEngine
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



def get_recovery_service(db: Annotated[Session, Depends(get_db)]) -> Any:
    from app.services.access.recovery_service import AccessRecoveryService

    settings = get_settings()
    server_pepper = os.getenv("ACCESS_SERVER_PEPPER", settings.access_server_pepper)
    if not server_pepper:
        raise _http_error("recovery_service_unavailable", status.HTTP_503_SERVICE_UNAVAILABLE, "Access recovery service is not configured")
    return AccessRecoveryService(
        db,
        server_pepper=server_pepper,
        cooldown_seconds=settings.access_recovery_cooldown_seconds,
        max_attempts_per_hour=settings.access_recovery_max_attempts_per_hour,
    )


def get_child_key_service(db: Annotated[Session, Depends(get_db)]) -> Any:
    from app.services.access.child_api_keys import ChildApiKeyService

    settings = get_settings()
    server_pepper = os.getenv("ACCESS_SERVER_PEPPER", settings.access_server_pepper)
    if not server_pepper:
        raise _http_error("child_key_service_unavailable", status.HTTP_503_SERVICE_UNAVAILABLE, "Access child key service is not configured")
    return ChildApiKeyService(db, server_pepper=server_pepper)


def get_delegated_pass_service(db: Annotated[Session, Depends(get_db)]) -> Any:
    from app.services.access.delegated_passes import DelegatedPassService

    settings = get_settings()
    server_pepper = os.getenv("ACCESS_SERVER_PEPPER", settings.access_server_pepper)
    if not server_pepper:
        raise _http_error("delegated_pass_service_unavailable", status.HTTP_503_SERVICE_UNAVAILABLE, "Access delegated pass service is not configured")
    return DelegatedPassService(db, server_pepper=server_pepper)

def get_human_intent_service(db: Annotated[Session, Depends(get_db)]) -> Any:
    from app.services.access.human_intent import HumanIntentService

    return HumanIntentService(db)

def get_lockdown_service(db: Annotated[Session, Depends(get_db)]) -> Any:
    from app.services.access.lockdown_service import LockdownService

    return LockdownService(db)

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
        amount_sats = PLAN_PRICES_SATS[plan]
        if request.amount_sats is not None and request.amount_sats != amount_sats:
            raise ValueError("caller_amount_mismatch")
        intent = service.create_payment_intent(plan, request.payment_method, amount_sats, _safe_metadata(request.metadata))
        _commit_service(service)
    except (ValueError, ManualGrantsDisabledError, PaymentProviderDisabledError, PaymentProviderNotConfiguredError) as exc:
        raise _http_error("payment_provider_unavailable", status.HTTP_400_BAD_REQUEST, str(exc)) from exc
    return _payment_intent_response(intent, certificate_available=False)


def _offer_out(offer: Any) -> AccessOfferOut:
    return AccessOfferOut(**asdict(offer))


def _checkout_out(checkout: Any) -> CheckoutOut:
    return CheckoutOut(
        checkout_id=checkout.id, offer_id=checkout.offer_id,
        offer_revision_id=checkout.offer_revision_id, plan_code=checkout.plan_code,
        capability=checkout.capability, scopes=tuple(checkout.scopes_json),
        amount_sats=checkout.amount_sats, price_unit=checkout.price_unit,
        duration_days=checkout.duration_days, terms_version=checkout.terms_version,
        status=checkout.status,
        issuance_eligible=checkout.status == "eligible",
        eligibility_reason=checkout.eligibility_reason,
        payment_intent_id=checkout.payment_intent_id,
        created_at=checkout.created_at, expires_at=checkout.expires_at,
    )


@router.get("/offers", response_model=list[AccessOfferOut], summary="List active server-owned Access Offers.")
def get_access_offers() -> list[AccessOfferOut]:
    return [_offer_out(offer) for offer in list_offers() if offer.availability == "active"]


@router.get("/offers/{offer_id}", response_model=AccessOfferOut, summary="Read an exact current Access Offer revision.")
def get_access_offer(offer_id: str) -> AccessOfferOut:
    try:
        return _offer_out(get_offer(offer_id))
    except ValueError as exc:
        raise _http_error("offer_not_found", status.HTTP_404_NOT_FOUND) from exc


@router.post("/checkouts", response_model=CheckoutOut, status_code=status.HTTP_201_CREATED, summary="Create an idempotent Checkout from server-owned Offer terms.")
def create_access_checkout(
    request: CheckoutCreateRequest,
    db: Annotated[Session, Depends(get_db)],
    payment_service: Annotated[Any, Depends(get_payment_intent_service)],
) -> CheckoutOut:
    service = AccessCheckoutService(db, payment_service)
    try:
        checkout = service.create(request.offer_id, request.payment_method, request.idempotency_key)
        db.commit()
        return _checkout_out(checkout)
    except Exception as exc:
        db.rollback()
        raise _http_error(_safe_error_code(exc), status.HTTP_400_BAD_REQUEST) from exc


@router.get("/checkouts/{checkout_id}", response_model=CheckoutOut, summary="Read authoritative Checkout and issuance eligibility.")
def get_access_checkout(checkout_id: str, db: Annotated[Session, Depends(get_db)]) -> CheckoutOut:
    service = AccessCheckoutService(db, get_payment_intent_service(db))
    try:
        checkout = service.get(checkout_id)
        db.commit()
        return _checkout_out(checkout)
    except ValueError as exc:
        db.rollback()
        raise _http_error(str(exc), status.HTTP_404_NOT_FOUND) from exc


@router.post("/issuance/challenges", response_model=IssuanceChallengeOut, summary="Create a device-bound challenge for one eligible Checkout.")
def create_issuance_challenge(
    request: IssuanceChallengeCreateRequest,
    db: Annotated[Session, Depends(get_db)],
    issuer: Annotated[Any, Depends(get_certificate_issuer)],
) -> IssuanceChallengeOut:
    service = AccessIssuanceService(db, issuer)
    try:
        challenge = service.create_challenge(request.checkout_id, request.device_public_key)
        db.commit()
        return IssuanceChallengeOut(
            challenge_id=challenge.id, checkout_id=challenge.checkout_id,
            canonical_payload=service.canonical_payload(challenge),
            protocol_version=challenge.protocol_version, algorithm="Ed25519",
            expires_at=challenge.expires_at,
        )
    except Exception as exc:
        db.rollback()
        raise _http_error(_safe_error_code(exc), status.HTTP_403_FORBIDDEN) from exc


@router.post("/issuance", response_model=IssuedAccessOut, summary="Atomically verify device PoP and issue Access from frozen Checkout terms.")
def issue_access(
    request: AccessIssueRequest,
    db: Annotated[Session, Depends(get_db)],
    issuer: Annotated[Any, Depends(get_certificate_issuer)],
) -> IssuedAccessOut:
    service = AccessIssuanceService(db, issuer)
    try:
        grant = service.verify_and_issue(request.checkout_id, request.challenge_id, request.signature)
        db.commit()
        return _grant_out(grant)
    except Exception as exc:
        db.rollback()
        raise _http_error(_safe_error_code(exc), status.HTTP_403_FORBIDDEN) from exc


@router.get("/issued/{grant_id}", response_model=IssuedAccessOut, summary="Read a non-secret issued Access summary.")
def get_issued_access(
    grant_id: str,
    db: Annotated[Session, Depends(get_db)],
) -> IssuedAccessOut:
    grant = db.get(AccessIssuedGrant, grant_id)
    if grant is None:
        raise _http_error("grant_not_found", status.HTTP_404_NOT_FOUND)
    return _grant_out(grant)


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
        payment_intent = db.get(AccessPaymentIntent, request.payment_intent_id)
        checkout = db.get(AccessCheckoutSession, payment_intent.checkout_id) if payment_intent and payment_intent.checkout_id else None
        duration_days = checkout.duration_days if checkout else request.subscription_period_days
        entitlement = entitlement_service.issue_entitlement(
            pass_lookup_hash=certificate.pass_lookup_hash,
            certificate_fingerprint=certificate.certificate_fingerprint,
            plan_code=certificate.plan_code,
            valid_from=valid_from,
            valid_until=valid_from + timedelta(days=duration_days),
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
    request: Annotated[AccessLockdownRequest, Body(default_factory=AccessLockdownRequest)],
    context: Annotated[Any, Depends(get_access_session_context)],
    service: Annotated[Any, Depends(get_lockdown_service)],
) -> AccessLockdownResponse:
    try:
        result = service.start_lockdown(context, request)
        _commit_service(service)
        return AccessLockdownResponse(**asdict(result))
    except Exception as exc:
        code = "access_step_up_required" if "step_up" in str(exc) or "human_intent" in str(exc) else "access_lockdown_denied"
        raise _http_error(code, status.HTTP_403_FORBIDDEN, str(exc)) from exc


@router.post("/recovery/setup", response_model=RecoverySetupResponse, summary="Create Bastion Recovery Seed setup material; this is not a Bitcoin wallet seed.")
def setup_recovery(request: RecoverySetupRequest, service: Annotated[Any, Depends(get_recovery_service)]) -> RecoverySetupResponse:
    try:
        result = service.setup_recovery(**request.model_dump())
        _commit_service(service)
        return RecoverySetupResponse(
            recovery_factor_id=result.recovery_factor_id,
            bastion_recovery_phrase=result.phrase_words,
            word_count=result.word_count,
            warning=result.warning,
            display_once=result.display_once,
        )
    except Exception as exc:
        raise _http_error(_recovery_error_code(exc), status.HTTP_400_BAD_REQUEST) from exc


@router.post("/recovery/start", response_model=RecoveryStartResponse, summary="Start a policy-bounded Access recovery attempt.")
def start_recovery(request: RecoveryStartRequest, service: Annotated[Any, Depends(get_recovery_service)]) -> RecoveryStartResponse:
    try:
        result = service.start_recovery(**request.model_dump())
        _commit_service(service)
        return RecoveryStartResponse(**asdict(result))
    except Exception as exc:
        raise _http_error(_recovery_error_code(exc), status.HTTP_403_FORBIDDEN) from exc


@router.post("/recovery/factors", response_model=RecoveryFactorSubmitResponse, summary="Submit one recovery factor without exposing raw recovery material.")
def submit_recovery_factor(request: RecoveryFactorSubmitRequest, service: Annotated[Any, Depends(get_recovery_service)]) -> RecoveryFactorSubmitResponse:
    try:
        result = service.verify_recovery_factor(**request.model_dump())
        _commit_service(service)
        return RecoveryFactorSubmitResponse(**asdict(result))
    except Exception as exc:
        raise _http_error(_recovery_error_code(exc), status.HTTP_403_FORBIDDEN) from exc


@router.get("/recovery/status/{recovery_attempt_id}", response_model=RecoveryStatusResponse, summary="Read recovery quorum status without leaking factor details.")
def recovery_status(recovery_attempt_id: str, service: Annotated[Any, Depends(get_recovery_service)]) -> RecoveryStatusResponse:
    try:
        result = service.get_recovery_status(recovery_attempt_id=recovery_attempt_id)
        return RecoveryStatusResponse(**asdict(result))
    except Exception as exc:
        raise _http_error(_recovery_error_code(exc), status.HTTP_404_NOT_FOUND) from exc


@router.post("/recovery/complete", response_model=RecoveryCompleteResponse, summary="Complete recovery after quorum and cooldown policy pass.")
def complete_recovery(request: RecoveryCompleteRequest, service: Annotated[Any, Depends(get_recovery_service)]) -> RecoveryCompleteResponse:
    try:
        result = service.complete_recovery(**request.model_dump())
        _commit_service(service)
        return RecoveryCompleteResponse(**asdict(result))
    except Exception as exc:
        raise _http_error(_recovery_error_code(exc), status.HTTP_403_FORBIDDEN) from exc


@router.post("/recovery/rotate", response_model=RecoveryRotateResponse, summary="Rotate Bastion recovery material after a protected Access ceremony.")
def rotate_recovery(request: RecoveryRotateRequest, service: Annotated[Any, Depends(get_recovery_service)]) -> RecoveryRotateResponse:
    try:
        result = service.rotate_recovery(**request.model_dump())
        _commit_service(service)
        return RecoveryRotateResponse(
            recovery_factor_id=result.recovery_factor_id,
            bastion_recovery_phrase=result.phrase_words,
            word_count=result.word_count,
            warning=result.warning,
            display_once=result.display_once,
        )
    except Exception as exc:
        raise _http_error(_recovery_error_code(exc), status.HTTP_403_FORBIDDEN) from exc


@router.post("/recovery/cancel", response_model=RecoveryStatusResponse, summary="Cancel an active Access recovery attempt.")
def cancel_recovery(request: RecoveryCancelRequest, service: Annotated[Any, Depends(get_recovery_service)]) -> RecoveryStatusResponse:
    try:
        result = service.cancel_recovery(**request.model_dump())
        _commit_service(service)
        return RecoveryStatusResponse(**asdict(result))
    except Exception as exc:
        raise _http_error(_recovery_error_code(exc), status.HTTP_403_FORBIDDEN) from exc



@router.post("/intents", response_model=HumanIntentResponse, summary="Create a Human Intent manifest for a critical Access action.")
def create_human_intent(
    request: HumanIntentCreateRequest,
    context: Annotated[Any, Depends(get_access_session_context)],
    service: Annotated[Any, Depends(get_human_intent_service)],
) -> HumanIntentResponse:
    try:
        risk_level = "critical" if str(request.action) == "lockdown_disable" else "high"
        result = service.create_intent(_human_intent_context(context, request.origin), request, risk_level=risk_level)
        _commit_service(service)
        return cast(HumanIntentResponse, result)
    except Exception as exc:
        raise _http_error("human_intent_rejected", status.HTTP_403_FORBIDDEN, str(exc)) from exc


@router.post("/intents/{intent_id}/verify", response_model=HumanIntentVerificationResult, summary="Verify a Human Intent signature without executing the action.")
def verify_human_intent(
    intent_id: str,
    request: HumanIntentSignatureRequest,
    context: Annotated[Any, Depends(get_access_session_context)],
    service: Annotated[Any, Depends(get_human_intent_service)],
) -> HumanIntentVerificationResult:
    try:
        result = service.verify_intent_signature(
            intent_id=intent_id,
            signature=request.signature,
            signature_alg=request.signature_alg,
            device_key_fingerprint=request.device_key_fingerprint,
        )
        _commit_service(service)
        return cast(HumanIntentVerificationResult, result)
    except Exception as exc:
        raise _http_error("human_intent_rejected", status.HTTP_403_FORBIDDEN, str(exc)) from exc


@router.get("/intents/{intent_id}", response_model=HumanIntentResponse, summary="Read safe Human Intent manifest status without exposing signatures.")
def get_human_intent(intent_id: str, context: Annotated[Any, Depends(get_access_session_context)], service: Annotated[Any, Depends(get_human_intent_service)]) -> HumanIntentResponse:
    try:
        return cast(HumanIntentResponse, service.get_intent_response(intent_id))
    except Exception as exc:
        raise _http_error("human_intent_not_found", status.HTTP_404_NOT_FOUND, str(exc)) from exc

@router.post("/api-keys", response_model=ChildApiKeyCreateResponse, summary="Create a scoped Child API Key; raw key is shown once.")
def create_child_api_key(
    request: ChildApiKeyCreate,
    context: Annotated[Any, Depends(get_access_session_context)],
    service: Annotated[Any, Depends(get_child_key_service)],
    human_intent_signature: Annotated[str | None, Header(alias="X-Bastion-Intent-Signature")] = None,
) -> ChildApiKeyCreateResponse:
    try:
        _enforce_key_policy(context, requested_scope="api:keys:manage", action="create_api_key", human_intent_signature=human_intent_signature)
        result = service.create_child_key(_parent_context_from_session(context), request, human_intent_signature=human_intent_signature)
        _commit_service(service)
        return ChildApiKeyCreateResponse(**asdict(result))
    except Exception as exc:
        raise _http_error(_key_error_code(exc), status.HTTP_403_FORBIDDEN) from exc


@router.get("/api-keys", response_model=list[ChildApiKeyPublic], summary="List Child API Key metadata only; raw secrets are never returned.")
def list_child_api_keys(context: Annotated[Any, Depends(get_access_session_context)], service: Annotated[Any, Depends(get_child_key_service)]) -> list[ChildApiKeyPublic]:
    return [_child_key_public(row) for row in service.list_child_keys(_parent_context_from_session(context))]


@router.get("/api-keys/{key_id}", response_model=ChildApiKeyPublic, summary="Get Child API Key metadata only.")
def get_child_api_key(key_id: str, context: Annotated[Any, Depends(get_access_session_context)], service: Annotated[Any, Depends(get_child_key_service)]) -> ChildApiKeyPublic:
    try:
        return _child_key_public(service.get_child_key(_parent_context_from_session(context), key_id))
    except Exception as exc:
        raise _http_error(_key_error_code(exc), status.HTTP_404_NOT_FOUND) from exc


@router.delete("/api-keys/{key_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Revoke a Child API Key.")
def revoke_child_api_key(key_id: str, context: Annotated[Any, Depends(get_access_session_context)], service: Annotated[Any, Depends(get_child_key_service)]) -> None:
    try:
        service.revoke_child_key(_parent_context_from_session(context), key_id, "parent_requested")
        _commit_service(service)
    except Exception as exc:
        raise _http_error(_key_error_code(exc), status.HTTP_404_NOT_FOUND) from exc


@router.post("/api-keys/{key_id}/rotate", response_model=ChildApiKeyCreateResponse, summary="Rotate a Child API Key; new raw key is shown once.")
def rotate_child_api_key(key_id: str, context: Annotated[Any, Depends(get_access_session_context)], service: Annotated[Any, Depends(get_child_key_service)], human_intent_signature: Annotated[str | None, Header(alias="X-Bastion-Intent-Signature")] = None) -> ChildApiKeyCreateResponse:
    try:
        _enforce_key_policy(context, requested_scope="api:keys:manage", action="create_api_key", human_intent_signature=human_intent_signature)
        result = service.rotate_child_key(_parent_context_from_session(context), key_id, human_intent_signature=human_intent_signature)
        _commit_service(service)
        return ChildApiKeyCreateResponse(**asdict(result))
    except Exception as exc:
        raise _http_error(_key_error_code(exc), status.HTTP_403_FORBIDDEN) from exc


@router.post("/api-keys/{key_id}/freeze", status_code=status.HTTP_204_NO_CONTENT, summary="Freeze a Child API Key without deleting audit history.")
def freeze_child_api_key(key_id: str, service: Annotated[Any, Depends(get_child_key_service)]) -> None:
    try:
        service.freeze_child_key(key_id, "parent_requested")
        _commit_service(service)
    except Exception as exc:
        raise _http_error(_key_error_code(exc), status.HTTP_404_NOT_FOUND) from exc


@router.post("/delegated-passes", response_model=DelegatedPassCreateResponse, summary="Create a temporary narrower Delegated Pass; raw pass is shown once.")
def create_delegated_pass(
    request: DelegatedPassCreate,
    context: Annotated[Any, Depends(get_access_session_context)],
    service: Annotated[Any, Depends(get_delegated_pass_service)],
    human_intent_signature: Annotated[str | None, Header(alias="X-Bastion-Intent-Signature")] = None,
) -> DelegatedPassCreateResponse:
    try:
        _enforce_key_policy(context, requested_scope="delegated_pass:create", action="create_delegated_pass", human_intent_signature=human_intent_signature)
        result = service.create_delegated_pass(_parent_context_from_session(context), request, human_intent_signature=human_intent_signature)
        _commit_service(service)
        return DelegatedPassCreateResponse(**asdict(result))
    except Exception as exc:
        raise _http_error(_key_error_code(exc), status.HTTP_403_FORBIDDEN) from exc


@router.get("/delegated-passes", response_model=list[DelegatedPassPublic], summary="List delegated pass metadata only.")
def list_delegated_passes(context: Annotated[Any, Depends(get_access_session_context)], service: Annotated[Any, Depends(get_delegated_pass_service)]) -> list[DelegatedPassPublic]:
    return [_delegated_pass_public(row) for row in service.list_delegated_passes(_parent_context_from_session(context))]


@router.get("/delegated-passes/{delegated_pass_id}", response_model=DelegatedPassPublic, summary="Get delegated pass metadata only.")
def get_delegated_pass(delegated_pass_id: str, context: Annotated[Any, Depends(get_access_session_context)], service: Annotated[Any, Depends(get_delegated_pass_service)]) -> DelegatedPassPublic:
    try:
        return _delegated_pass_public(service.get_delegated_pass(_parent_context_from_session(context), delegated_pass_id))
    except Exception as exc:
        raise _http_error(_key_error_code(exc), status.HTTP_404_NOT_FOUND) from exc


@router.delete("/delegated-passes/{delegated_pass_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Revoke a delegated pass.")
def revoke_delegated_pass(delegated_pass_id: str, context: Annotated[Any, Depends(get_access_session_context)], service: Annotated[Any, Depends(get_delegated_pass_service)]) -> None:
    try:
        service.revoke_delegated_pass(_parent_context_from_session(context), delegated_pass_id, "parent_requested")
        _commit_service(service)
    except Exception as exc:
        raise _http_error(_key_error_code(exc), status.HTTP_404_NOT_FOUND) from exc


@router.post("/delegated-passes/{delegated_pass_id}/freeze", status_code=status.HTTP_204_NO_CONTENT, summary="Freeze a delegated pass.")
def freeze_delegated_pass(delegated_pass_id: str, context: Annotated[Any, Depends(get_access_session_context)], service: Annotated[Any, Depends(get_delegated_pass_service)]) -> None:
    try:
        row = service.get_delegated_pass(_parent_context_from_session(context), delegated_pass_id)
        service.freeze_delegated_pass(row.delegated_pass_hash, "parent_requested")
        _commit_service(service)
    except Exception as exc:
        raise _http_error(_key_error_code(exc), status.HTTP_404_NOT_FOUND) from exc


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



def _enforce_key_policy(context: Any, *, requested_scope: str, action: str, human_intent_signature: str | None) -> None:
    scopes = set(getattr(context, "effective_scopes", getattr(context, "scopes", set())) or set())
    decision = AccessPolicyEngine().evaluate(
        AccessPolicyContext(
            certificate_fingerprint=getattr(context, "certificate_fingerprint", None),
            pass_lookup_hash=getattr(context, "pass_lookup_hash", None),
            plan_code=normalize_plan_code(getattr(context, "plan_code")),
            effective_scopes=scopes,
            requested_scope=requested_scope,
            request_risk_level="medium",
            session_id_hash=getattr(context, "session_id_hash", getattr(context, "session_hash", None)),
            session_status="active",
            session_expires_at=getattr(context, "session_expires_at", getattr(context, "expires_at", None)),
            entitlement_status=getattr(context, "entitlement_status", "active"),
            entitlement_valid_until=getattr(context, "session_expires_at", getattr(context, "expires_at", None)),
            metric_entitlements=getattr(context, "metric_entitlements", {}),
            is_critical_action=True,
            step_up_present=bool(human_intent_signature) or bool(getattr(context, "is_request_signature_verified", False)),
            human_intent_verified=bool(human_intent_signature) or bool(getattr(context, "is_step_up_verified", False)),
            metadata={"action": action},
        )
    )
    if not decision.allowed:
        raise _http_error(decision.reason_code, status.HTTP_403_FORBIDDEN, decision.human_reason)

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



def _human_intent_context(context: Any, origin: str) -> Any:
    from app.services.access.human_intent import HumanIntentContext

    scopes = list(getattr(context, "effective_scopes", getattr(context, "scopes", [])) or [])
    return HumanIntentContext(
        actor_fingerprint=getattr(context, "device_key_fingerprint", "unknown-device"),
        certificate_fingerprint=context.certificate_fingerprint,
        session_fingerprint=getattr(context, "session_id_hash", getattr(context, "session_hash", None)),
        device_key_fingerprint=context.device_key_fingerprint,
        plan_code=str(normalize_plan_code(context.plan_code).value),
        granted_scopes=scopes,
        origin=origin,
        policy_decision_ref=None,
        request_hash=None,
    )

def _parent_context_from_session(context: Any) -> Any:
    from app.services.access.key_constraints import ParentAccessContext

    overlay = build_entitlement_overlay(normalize_plan_code(context.plan_code))
    entitlement_expires_at = getattr(context, "session_expires_at", getattr(context, "expires_at", None))
    if not isinstance(entitlement_expires_at, datetime):
        entitlement_expires_at = datetime.now(UTC) + timedelta(days=1)
    return ParentAccessContext(
        pass_lookup_hash=context.pass_lookup_hash,
        certificate_fingerprint=context.certificate_fingerprint,
        plan_code=normalize_plan_code(context.plan_code),
        effective_scopes=frozenset(getattr(context, "effective_scopes", getattr(context, "scopes", []))),
        metric_entitlements=frozenset(overlay["metric_groups"]),
        entitlement_expires_at=entitlement_expires_at,
        session_hash=getattr(context, "session_hash", None),
        device_key_fingerprint=context.device_key_fingerprint,
        can_delegate=normalize_plan_code(context.plan_code) in {PlanCode.PLUS, PlanCode.PRO, PlanCode.BUSINESS, PlanCode.ENTERPRISE},
    )


def _child_key_public(row: ChildApiKey) -> ChildApiKeyPublic:
    denied = [scope for scope in (row.cannot_access_json or []) if isinstance(scope, str)]
    limits = row.limits_json or {}
    return ChildApiKeyPublic(
        key_id=row.key_id_hash,
        name=row.name,
        scopes=[scope for scope in (row.scopes_json or []) if isinstance(scope, str)],
        denied_scopes=denied,
        limits=limits,
        status=row.status,
        created_at=row.created_at,
        expires_at=row.expires_at,
        last_used_at=row.last_used_at,
        requires_request_signing=bool(limits.get("requires_request_signing", True)),
        can_delegate=bool(limits.get("can_delegate", False)),
    )


def _delegated_pass_public(row: DelegatedPass) -> DelegatedPassPublic:
    constraints = row.constraints_json or {}
    return DelegatedPassPublic(
        delegated_pass_id=str(constraints.get("delegated_pass_id_hash", row.id)),
        name=str(constraints.get("name")) if constraints.get("name") else None,
        delegated_to_label=str(constraints.get("delegated_to_label")) if constraints.get("delegated_to_label") else None,
        scopes=[scope for scope in (row.scopes_json or []) if isinstance(scope, str)],
        constraints=constraints,
        status=row.status,
        valid_from=row.valid_from,
        expires_at=row.valid_until,
        last_used_at=constraints.get("last_used_at"),
        can_create_child_keys=bool(constraints.get("can_create_child_keys", False)),
        can_delegate=bool(constraints.get("can_delegate", False)),
    )


def _key_error_code(exc: Exception) -> str:
    text = str(exc) or exc.__class__.__name__
    lowered = text.lower()
    if any(secret in lowered for secret in ("bbk_live", "bbd_live", "secret", "private", "token", "raw")):
        return exc.__class__.__name__.replace("Error", "").lower()
    return text


def _recovery_error_code(exc: Exception) -> str:
    text = str(exc) or exc.__class__.__name__
    lowered = text.lower()
    if "bitcoin" in lowered and ("seed" in lowered or "private" in lowered):
        return "bitcoin_seed_input_rejected"
    if any(secret in lowered for secret in ("phrase", "factor", "pass", "token", "private", "seed")):
        return text if text.startswith("recovery_") or text.startswith("bitcoin_") else exc.__class__.__name__.replace("Error", "").lower()
    return text


def _safe_error_code(exc: Exception) -> str:
    text = str(exc) or exc.__class__.__name__
    if any(secret in text.lower() for secret in ("pass", "token", "private", "seed")):
        return exc.__class__.__name__.replace("Error", "").lower()
    return text


def _grant_out(grant: AccessIssuedGrant) -> IssuedAccessOut:
    return IssuedAccessOut(
        grant_id=grant.id,
        checkout_id=grant.checkout_id,
        offer_revision_id=grant.offer_revision_id,
        certificate_fingerprint=grant.certificate_fingerprint,
        device_key_fingerprint=grant.device_key_fingerprint,
        capability=grant.capability,
        scopes=tuple(grant.scopes_json),
        terms_version=grant.terms_version,
        status=grant.status,
        issued_at=grant.issued_at,
        expires_at=grant.expires_at,
    )
