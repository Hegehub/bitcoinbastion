"""Types for Wallet-first challenge lifecycle services."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Any


class WalletChallengePurpose(StrEnum):
    REGISTER = "register"
    LOGIN = "login"
    LINK_WALLET = "link_wallet"
    NEW_DEVICE = "new_device"
    STEP_UP = "step_up"
    RECOVERY_START = "recovery_start"
    OWNERSHIP_PROOF = "ownership_proof"
    HARDWARE_WALLET_PROOF = "hardware_wallet_proof"
    ACCESS_CERTIFICATE_BRIDGE = "access_certificate_bridge"


class WalletChallengeStatus(StrEnum):
    PENDING = "pending"
    CONSUMED = "consumed"
    EXPIRED = "expired"
    REVOKED = "revoked"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class WalletChallengeRecord:
    challenge_id: str
    challenge_hash: str
    nonce_hash: str
    intent_hash: str
    purpose: str
    action: str
    network: str
    proof_type: str
    origin: str
    domain: str
    device_key_fingerprint: str
    policy_hash: str
    requested_scopes: tuple[str, ...]
    risk_level: str
    principal_hint_hash: str | None
    created_at: datetime
    expires_at: datetime
    consumed_at: datetime | None
    revoked_at: datetime | None
    failure_reason_code: str | None
    status: str
    schema_epoch: int
    policy_epoch: int
    crypto_epoch: int
    intent: dict[str, Any]
    signable_message: str


@dataclass(frozen=True, slots=True)
class WalletChallengeResult:
    challenge_id: str
    intent_hash: str
    canonical_intent: str
    signable_message: str
    nonce: str
    expires_at: datetime
    status: str
    requested_scopes: tuple[str, ...]
