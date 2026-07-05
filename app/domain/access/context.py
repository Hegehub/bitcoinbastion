"""Request-local Proof-of-Access context objects.

AccessContext intentionally contains only hashes, fingerprints, plan/scope state,
and request metadata. It never carries raw Access Passes, raw session tokens,
recovery phrases, private keys, Bitcoin seeds, or server pepper values.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from app.domain.access.plans import PlanCode


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
