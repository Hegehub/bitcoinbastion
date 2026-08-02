from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime, timedelta

import pytest

from app.api import access_dependencies as deps
from app.domain.access.context import AccessAuthMethod, AccessContext, AccessPrincipalType
from app.domain.access.plans import PlanCode


def context(**changes: object) -> AccessContext:
    base = AccessContext(
        session_id_hash="sha256:session",
        certificate_fingerprint="sha256:certificate",
        pass_lookup_hash="hmac-sha256:pass",
        device_key_fingerprint="sha256:device-key",
        plan_code=PlanCode.PRO,
        effective_scopes={"market:intelligence:read", "lnurl:withdraw:create"},
        metric_entitlements={"groups": ["market.intelligence"]},
        entitlement_status="active",
        session_expires_at=datetime.now(UTC) + timedelta(minutes=5),
        is_request_signature_verified=True,
        principal_hash="sha256:principal",
        principal_type=AccessPrincipalType.BITCOIN_WALLET_PRINCIPAL,
        auth_method=AccessAuthMethod.BIP322,
        device_id_hash="sha256:device",
    )
    return replace(base, **changes)


def test_unified_context_supports_bitcoin_and_lightning_principals() -> None:
    bitcoin = context()
    lightning = context(
        principal_type=AccessPrincipalType.LIGHTNING_WALLET_PRINCIPAL,
        auth_method=AccessAuthMethod.LNURL_AUTH,
    )
    assert bitcoin.auth_method == AccessAuthMethod.BIP322
    assert lightning.principal_type == AccessPrincipalType.LIGHTNING_WALLET_PRINCIPAL


def test_context_is_immutable() -> None:
    with pytest.raises(AttributeError):
        context().principal_hash = "changed"  # type: ignore[misc]


def test_action_bound_fresh_step_up_accepts_bip322_and_lnurl() -> None:
    now = datetime.now(UTC)
    for method in ("bip322", "lnurl_auth"):
        value = context(
            is_step_up_verified=True,
            last_step_up_at=now,
            metadata={
                "step_up_evidence": {
                    "action": "create_api_key",
                    "intent_hash": "sha256:intent",
                    "method": method,
                    "verified_at": now,
                    "status": "active",
                }
            },
        )
        deps._validate_fresh_step_up(value, "create_api_key", max_age_seconds=300)


def test_wrong_action_and_compatibility_step_up_are_rejected() -> None:
    value = context(
        is_step_up_verified=True,
        metadata={
            "step_up_evidence": {
                "action": "read_metrics",
                "intent_hash": "sha256:intent",
                "method": "legacy_message_signature",
                "verified_at": datetime.now(UTC),
                "status": "active",
            }
        },
    )
    with pytest.raises(Exception):
        deps._validate_fresh_step_up(value, "create_api_key", max_age_seconds=300)


def test_access_certificate_does_not_bypass_policy() -> None:
    class Deny:
        def evaluate(self, _context: object) -> object:
            return type("Decision", (), {"allowed": False, "decision": "deny", "reason_code": "policy_denied", "human_reason": "Denied."})()

    old = deps.POLICY_ENGINE_FACTORY
    deps.POLICY_ENGINE_FACTORY = Deny
    try:
        with pytest.raises(Exception):
            deps.require_policy_decision(context(verification_strength="high_assurance"), action="read")
    finally:
        deps.POLICY_ENGINE_FACTORY = old
