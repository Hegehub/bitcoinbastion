"""Safe audit collector for Merchant Lightning Address lifecycle events."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.services.access.crypto.hashing import hash_canonical_json_prefixed


MERCHANT_ADDRESS_AUDIT_EVENTS = frozenset(
    {
        "merchant_ln_domain_created",
        "merchant_ln_domain_verification_started",
        "merchant_ln_domain_verified",
        "merchant_ln_domain_verification_failed",
        "merchant_ln_domain_suspended",
        "merchant_ln_domain_revoked",
        "merchant_ln_address_created",
        "merchant_ln_address_activated",
        "merchant_ln_address_updated",
        "merchant_ln_address_suspended",
        "merchant_ln_address_revoked",
        "merchant_ln_address_resolved",
        "merchant_ln_address_resolution_failed",
        "merchant_ln_address_target_rotated",
        "merchant_ln_invoice_issued",
        "merchant_ln_payment_settled",
        "merchant_ln_payment_failed",
    }
)


@dataclass(slots=True)
class InMemoryMerchantAddressAudit:
    events: list[dict[str, Any]] = field(default_factory=list)

    def emit(self, event_type: str, payload: dict[str, Any]) -> str:
        safe_payload = {k: v for k, v in payload.items() if "token" not in k and "secret" not in k and "raw" not in k}
        event_hash = hash_canonical_json_prefixed({"event_type": event_type, **safe_payload, "index": len(self.events)})
        self.events.append({"event_type": event_type, "event_hash": event_hash, **safe_payload})
        return event_hash
