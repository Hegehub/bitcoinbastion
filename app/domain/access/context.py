"""Request-local Proof-of-Access context objects.

AccessContext intentionally contains only hashes, fingerprints, plan/scope state,
and request metadata. It never carries raw Access Passes, raw session tokens,
recovery phrases, private keys, Bitcoin seeds, or server pepper values.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from app.domain.access.plans import PlanCode


class AccessPrincipalType(str, Enum):
    BITCOIN_WALLET_PRINCIPAL = "bitcoin_wallet_principal"
    LIGHTNING_WALLET_PRINCIPAL = "lightning_wallet_principal"
    ACCESS_CERTIFICATE = "access_certificate"
    CHILD_API_KEY = "child_api_key"
    DELEGATED_PASS = "delegated_pass"
    BUSINESS_ROLE = "business_role"
    PAYREGISTER_DEVICE = "payregister_device"
    BOT = "bot"


class AccessAuthMethod(str, Enum):
    BIP322 = "bip322"
    LNURL_AUTH = "lnurl_auth"
    LEGACY_MESSAGE_SIGNATURE = "legacy_message_signature"
    HARDWARE_WALLET = "hardware_wallet"
    AIR_GAPPED = "air_gapped"
    MULTISIG_QUORUM = "multisig_quorum"
    ACCESS_CERTIFICATE = "access_certificate"
    DELEGATED_PASS = "delegated_pass"
    CHILD_API_KEY = "child_api_key"
    RECOVERY_CAPSULE = "recovery_capsule"


@dataclass(frozen=True, slots=True)
class AccessContext:
    session_id_hash: str
    certificate_fingerprint: str
    pass_lookup_hash: str
    device_key_fingerprint: str
    plan_code: PlanCode
    effective_scopes: set[str]
    metric_entitlements: dict[str, Any]
    entitlement_status: str
    session_expires_at: datetime
    risk_level: str = "low"
    request_id: str | None = None
    origin: str | None = None
    policy_mode: str = "proof_of_access"
    is_request_signature_verified: bool = False
    is_step_up_verified: bool = False
    is_recovery_limited: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)
    principal_hash: str | None = None
    principal_type: AccessPrincipalType | str | None = None
    parent_principal_hash: str | None = None
    auth_method: AccessAuthMethod | str | None = None
    verification_strength: str = "standard"
    device_id_hash: str | None = None
    session_type: str = "pop"
    subscription_status: str = "active"
    business_role: str | None = None
    payregister_device_hash: str | None = None
    offline_mode: bool = False
    sovereign_mode: bool = False
    last_wallet_proof_at: datetime | None = None
    last_step_up_at: datetime | None = None
    access_integrity_score: int | None = None
    policy_epoch: int = 1
    crypto_epoch: int = 1


# Wallet/LNURL v2 and legacy Access routes deliberately share one immutable
# request context rather than maintaining parallel authorization models.
UnifiedAccessContext = AccessContext
