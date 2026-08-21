"""Versioned server configuration is the canonical Access Offer authority."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256

from app.domain.access.plans import PlanCode
from app.services.access.plan_entitlements import build_entitlement_overlay

TERMS_VERSION = "access-terms-v1"
OFFER_DURATION_DAYS = 30
PLAN_PRICES_SATS: dict[PlanCode, int] = {
    PlanCode.LITE: 1_000,
    PlanCode.BASIC: 10_000,
    PlanCode.PLUS: 50_000,
    PlanCode.PRO: 250_000,
    PlanCode.BUSINESS: 1_000_000,
    PlanCode.ENTERPRISE: 5_000_000,
}


@dataclass(frozen=True, slots=True)
class AccessOffer:
    offer_id: str
    revision_id: str
    plan_code: PlanCode
    capability: str
    scopes: tuple[str, ...]
    amount_sats: int
    price_unit: str
    duration_days: int
    terms_version: str
    availability: str
    limitations: tuple[str, ...]


def _offer(plan: PlanCode) -> AccessOffer:
    scopes = tuple(build_entitlement_overlay(plan)["allowed_scopes"])
    offer_id = f"access-{plan.value}"
    material = f"{offer_id}|{PLAN_PRICES_SATS[plan]}|sats|{OFFER_DURATION_DAYS}|{TERMS_VERSION}|{','.join(scopes)}"
    revision = sha256(material.encode()).hexdigest()[:24]
    return AccessOffer(
        offer_id=offer_id,
        revision_id=f"{offer_id}:{revision}",
        plan_code=plan,
        capability=plan.value,
        scopes=scopes,
        amount_sats=PLAN_PRICES_SATS[plan],
        price_unit="sats",
        duration_days=OFFER_DURATION_DAYS,
        terms_version=TERMS_VERSION,
        availability="active",
        limitations=("Payment settlement and issuance remain separate.",),
    )


OFFER_CATALOG = {_offer(plan).offer_id: _offer(plan) for plan in PlanCode}


def list_offers() -> tuple[AccessOffer, ...]:
    return tuple(OFFER_CATALOG[key] for key in sorted(OFFER_CATALOG))


def get_offer(offer_id: str) -> AccessOffer:
    try:
        return OFFER_CATALOG[offer_id]
    except KeyError as exc:
        raise ValueError("offer_not_found") from exc
