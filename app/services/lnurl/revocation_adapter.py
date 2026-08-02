"""LNURL adapter for the authoritative Access revocation registry.

K1 lifecycle remains in :mod:`app.services.lnurl.k1_registry`, whose repository
implements atomic compare-and-set consumption. This adapter adds Access-layer
revocation/audit semantics without creating another source of truth.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.services.access.revocation_registry import RevocationRegistry, RevocationStatus
from app.services.lnurl.k1_registry import LNURLK1RegistryService


class LNURLRevocationAdapter:
    def __init__(
        self, *, registry: RevocationRegistry, k1_registry: LNURLK1RegistryService
    ) -> None:
        self.registry = registry
        self.k1_registry = k1_registry

    def consume_k1(self, db: Session, raw_k1: str, **expected: str | None) -> Any:
        """Fail a registry-revoked k1, then atomically consume in the K1 repository."""
        k1_hash = self.k1_registry._lookup_hash(raw_k1)  # noqa: SLF001 - adapter boundary
        if self.registry.is_revoked(db, target_type="lnurl_k1", target_hash=k1_hash).revoked:
            raise ValueError("lnurl_k1_revoked")
        try:
            return self.k1_registry.consume_k1(raw_k1, **expected)
        except Exception:
            # The K1 service emits its protocol audit/metric; the Access registry
            # stores replay evidence only when the service confirms replay.
            status = self.k1_registry.get_k1_status(raw_k1)
            if str(status.status) in {"consumed", "used", "replay_detected"}:
                self.mark_k1_replay_detected(db, k1_hash=k1_hash)
            raise

    def revoke_k1(
        self, db: Session, *, raw_k1: str, actor_hash: str | None = None
    ) -> RevocationStatus:
        k1_hash = self.k1_registry._lookup_hash(raw_k1)  # noqa: SLF001 - adapter boundary
        self.k1_registry.revoke_k1(
            raw_k1=raw_k1, reason_code="administratively_revoked", actor_hash=actor_hash
        )
        return self.registry.revoke_target(
            db,
            target_type="lnurl_k1",
            target_hash=k1_hash,
            reason="user_requested",
            actor_hash=actor_hash,
        )

    def mark_k1_replay_detected(
        self, db: Session, *, k1_hash: str, actor_hash: str | None = None
    ) -> RevocationStatus:
        status = self.registry.revoke_target(
            db,
            target_type="lnurl_k1",
            target_hash=k1_hash,
            reason="lnurl_k1_reuse_detected",
            actor_hash=actor_hash,
            metadata={"k1_state": "replay_detected"},
        )
        self.registry._emit_named_target_event(
            "lnurl_k1_replay_detected", status=status, actor_hash=actor_hash
        )  # noqa: SLF001
        return status
