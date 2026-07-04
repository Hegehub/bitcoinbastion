"""Secure Access Pass generation helpers.

Raw Access Pass values are generated with cryptographically secure randomness,
returned only by the issuance flow, and must never be stored or accepted as
bearer credentials.
"""

from __future__ import annotations

import secrets

from app.domain.access.plans import PlanCode, normalize_plan_code
from app.services.access.crypto.hashing import secure_token_urlsafe

_HUMAN_PREFIXES: dict[PlanCode, str] = {
    PlanCode.LITE: "BBP-LITE",
    PlanCode.BASIC: "BBP-BASIC",
    PlanCode.PLUS: "BBP-PLUS",
    PlanCode.PRO: "BBP-PRO",
    PlanCode.BUSINESS: "BBP-BUSINESS",
    PlanCode.ENTERPRISE: "BBP-ENTERPRISE",
}
_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"


def generate_machine_pass() -> str:
    """Return the preferred high-entropy machine Access Pass format."""

    return f"bbp_live_{secure_token_urlsafe(32)}"


def generate_human_readable_pass(plan_code: PlanCode | str) -> str:
    """Return a human-readable Access Pass for a plan.

    Human-readable passes are still secrets and must never be logged or stored.
    """

    plan = normalize_plan_code(plan_code)
    return f"{_HUMAN_PREFIXES[plan]}-{_chunk()}-{_chunk()}"


def generate_raw_access_pass(plan_code: PlanCode | str) -> str:
    """Return a raw Access Pass for one-time display during issuance."""

    normalize_plan_code(plan_code)
    return generate_machine_pass()


def _chunk(length: int = 4) -> str:
    return "".join(secrets.choice(_ALPHABET) for _ in range(length))
