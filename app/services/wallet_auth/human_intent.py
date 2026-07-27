"""Canonical Human Intent manifests for Wallet + LNURL step-up.

The manifest is audit-safe: it contains only hashes, fingerprints, policy data,
requested scopes, and user-visible semantics. It never carries raw wallet
addresses, raw LNURL linking keys, signatures, k1 values, session tokens,
private keys, recovery phrases, or Bitcoin seed material.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Any

from app.services.access.crypto.hashing import hash_canonical_json_prefixed

WALLET_STEP_UP_INTENT_TYPE = "bastion_wallet_step_up_intent"
WALLET_SIGNATURE_WARNING = "This signature does not authorize a Bitcoin transaction. This signature only approves the described Bastion access action."


@dataclass(frozen=True, slots=True)
class WalletStepUpHumanIntent:
    action: str
    purpose: str
    actor_type: str
    principal_hash: str
    device_key_fingerprint: str | None
    session_fingerprint: str | None
    origin: str | None
    domain: str | None
    requested_scopes: tuple[str, ...] = ()
    requested_object: str | None = None
    requested_expiry: str | None = None
    requested_amount_msat: int | None = None
    business_role: str | None = None
    cannot_access: tuple[str, ...] = ()
    risk_level: str = "high"
    policy_hash: str = "sha256:wallet-step-up-policy-v1"
    policy_epoch: int = 1
    challenge_id: str | None = None
    nonce: str | None = None
    issued_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    expires_at: datetime | None = None
    lnurl_internal_action_description: str | None = None
    version: int = 1

    def canonical_payload(self) -> dict[str, Any]:
        expires = self.expires_at or self.issued_at + timedelta(seconds=300)
        return {
            "type": WALLET_STEP_UP_INTENT_TYPE,
            "version": self.version,
            "action": self.action,
            "purpose": self.purpose,
            "actor_type": self.actor_type,
            "principal_hash": self.principal_hash,
            "device_key_fingerprint": self.device_key_fingerprint,
            "session_fingerprint": self.session_fingerprint,
            "origin": self.origin,
            "domain": self.domain,
            "requested_scopes": tuple(sorted(self.requested_scopes)),
            "requested_object": self.requested_object,
            "requested_expiry": self.requested_expiry,
            "requested_amount_msat": self.requested_amount_msat,
            "business_role": self.business_role,
            "cannot_access": tuple(sorted(self.cannot_access)),
            "risk_level": self.risk_level,
            "policy_hash": self.policy_hash,
            "policy_epoch": self.policy_epoch,
            "challenge_id": self.challenge_id,
            "nonce": self.nonce,
            "issued_at": _iso(self.issued_at),
            "expires_at": _iso(expires),
            "warning": WALLET_SIGNATURE_WARNING,
            "lnurl_internal_action_description": self.lnurl_internal_action_description,
        }

    @property
    def intent_hash(self) -> str:
        return hash_canonical_json_prefixed(self.canonical_payload())

    def with_hash(self) -> dict[str, Any]:
        payload = self.canonical_payload()
        payload["intent_hash"] = self.intent_hash
        return payload


def _iso(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return value.astimezone(UTC).isoformat()
