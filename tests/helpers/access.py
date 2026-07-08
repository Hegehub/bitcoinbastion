"""Test-only Proof-of-Access fixtures for protected API contract checks.

These helpers intentionally use redacted fingerprints and synthetic session
material. They never contain raw Access Passes, session tokens, recovery phrases,
Bitcoin seeds, or private keys.
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from app.api import access_dependencies as access_deps
from app.domain.access.context import AccessContext
from app.domain.access.plans import PlanCode
from app.domain.access.scopes import ACCESS_SCOPES

ACCESS_HEADERS: dict[str, str] = {"X-Bastion-Session": "test-pop-session"}
SIGNED_ACCESS_HEADERS: dict[str, str] = {
    **ACCESS_HEADERS,
    "X-Bastion-Timestamp": "2026-07-08T00:00:00Z",
    "X-Bastion-Nonce": "test-nonce-contract-suite",
    "X-Bastion-Body-Hash": "sha256:test-body-hash",
    "X-Bastion-Signature": "test-request-signature",
    "X-Bastion-Intent-Signature": "test-human-intent-signature",
}


@dataclass(slots=True)
class TestSessionContext:
    session_hash: str = "sha256:test-session"
    certificate_fingerprint: str = "sha256:test-certificate"
    pass_lookup_hash: str = "hmac-sha256:test-pass"
    device_key_fingerprint: str = "sha256:test-device"
    plan_code: PlanCode = PlanCode.ENTERPRISE
    scopes: frozenset[str] = ACCESS_SCOPES
    expires_at: datetime = field(default_factory=lambda: datetime.now(UTC) + timedelta(minutes=30))
    risk_level: str = "low"
    policy_mode: str = "proof_of_access"
    requires_request_signing: bool = False


def access_context(*, signed: bool = True) -> AccessContext:
    return AccessContext(
        session_id_hash="sha256:test-session",
        certificate_fingerprint="sha256:test-certificate",
        pass_lookup_hash="hmac-sha256:test-pass",
        device_key_fingerprint="sha256:test-device",
        plan_code=PlanCode.ENTERPRISE,
        effective_scopes=set(ACCESS_SCOPES),
        metric_entitlements={
            "groups": [
                "market.price",
                "market.ohlcv",
                "market.volatility",
                "market.intelligence",
                "market.regime",
                "market.liquidity",
                "signals.lite",
                "signals.standard",
                "signals.advanced",
                "trace.lite",
                "trace.standard",
                "trace.advanced",
                "treasury.read",
                "api.keys",
                "webhooks.manage",
                "policy.management",
            ]
        },
        entitlement_status="active",
        session_expires_at=datetime.now(UTC) + timedelta(minutes=30),
        risk_level="low",
        origin="https://app.example.test",
        policy_mode="proof_of_possession" if signed else "proof_of_access",
        is_request_signature_verified=signed,
        is_step_up_verified=signed,
        metadata={
            "business_roles": ["owner", "admin"],
            "enterprise_permissions": ["enterprise:policy:custom"],
            "human_intent_present": signed,
        },
    )


@contextmanager
def proof_of_access_overrides() -> Iterator[None]:
    old_resolver = access_deps.SESSION_CONTEXT_RESOLVER
    old_verifier = access_deps.REQUEST_SIGNATURE_VERIFIER
    old_revocation = access_deps.REVOCATION_CHECKER
    try:
        access_deps.SESSION_CONTEXT_RESOLVER = lambda _token, _db: TestSessionContext()
        access_deps.REQUEST_SIGNATURE_VERIFIER = lambda _request, _db: access_context(signed=True)
        access_deps.REVOCATION_CHECKER = lambda _context, _db: {
            "allowed": True,
            "revoked_targets": [],
        }
        yield
    finally:
        access_deps.SESSION_CONTEXT_RESOLVER = old_resolver
        access_deps.REQUEST_SIGNATURE_VERIFIER = old_verifier
        access_deps.REVOCATION_CHECKER = old_revocation
