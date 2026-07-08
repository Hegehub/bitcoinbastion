"""Temporary delegated passes for Proof-of-Access Auth."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from types import SimpleNamespace
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.access import DelegatedPass
from app.services.access.audit_chain import AccessAuditChain
from app.services.access.crypto.hashing import constant_time_equal, hmac_sha256_prefixed, secure_nonce_hex, sha256_prefixed
from app.services.access.key_constraints import ParentAccessContext, validate_delegated_pass_constraints
from app.services.access.key_redaction import assert_no_raw_secret_in_payload


@dataclass(frozen=True)
class DelegatedPassCreateResult:
    delegated_pass_id: str
    raw_delegated_pass: str
    scopes: list[str]
    constraints: dict[str, Any]
    expires_at: datetime
    warning: str


class DelegatedPassError(ValueError):
    pass


class DelegatedPassService:
    def __init__(self, db: Session, *, server_pepper: str, audit_chain: AccessAuditChain | None = None) -> None:
        if not server_pepper:
            raise DelegatedPassError("delegated_pass_pepper_required")
        self.db = db
        self.server_pepper = server_pepper
        self.audit_chain = audit_chain or AccessAuditChain(db)

    def create_delegated_pass(self, parent_context: ParentAccessContext, request: Any, human_intent_signature: str | None = None) -> DelegatedPassCreateResult:
        existing_count = self._active_count(parent_context.pass_lookup_hash)
        constraint_request = SimpleNamespace(**request.model_dump() if hasattr(request, "model_dump") else vars(request))
        validate_delegated_pass_constraints(parent_context, constraint_request, existing_count)
        delegation_id = secure_nonce_hex(16)
        secret = secure_nonce_hex(32)
        raw_pass = f"bbd_live_{delegation_id}_{secret}"
        delegated_pass_hash = hmac_sha256_prefixed(self.server_pepper, raw_pass)
        constraints = getattr(request, "constraints", {}) or {}
        metadata = {
            "name": request.name,
            "delegated_to_label": getattr(request, "delegated_to_label", None),
            "denied_scopes": getattr(request, "denied_scopes", []) or [],
            "metric_entitlements": getattr(request, "metric_entitlements", {}) or {},
            "requires_human_intent": bool(human_intent_signature),
            "can_create_child_keys": getattr(request, "can_create_child_keys", False),
            "can_delegate": getattr(request, "can_delegate", False),
            "audit_fingerprint": sha256_prefixed(delegated_pass_hash),
        }
        assert_no_raw_secret_in_payload({"metadata": metadata})
        now = datetime.now(UTC)
        row = DelegatedPass(
            parent_pass_lookup_hash=parent_context.pass_lookup_hash,
            delegated_pass_hash=delegated_pass_hash,
            delegated_to_hash=sha256_prefixed(str(getattr(request, "delegated_to_label", ""))) if getattr(request, "delegated_to_label", None) else None,
            scopes_json=list(request.scopes),
            constraints_json={**constraints, **metadata, "delegated_pass_id_hash": hmac_sha256_prefixed(self.server_pepper, delegation_id)},
            status="active",
            created_at=now,
            updated_at=now,
            valid_from=getattr(request, "valid_from", None) or now,
            valid_until=request.expires_at,
            revoked_at=None,
        )
        self.db.add(row)
        self.db.flush()
        self._audit("delegated_pass_created", parent_context, delegated_pass_hash, list(request.scopes), "created")
        return DelegatedPassCreateResult(
            delegated_pass_id=delegation_id,
            raw_delegated_pass=raw_pass,
            scopes=list(request.scopes),
            constraints=constraints,
            expires_at=row.valid_until,
            warning="Store this delegated pass now. It will not be shown again.",
        )

    def list_delegated_passes(self, parent_context: ParentAccessContext) -> list[DelegatedPass]:
        return list(self.db.execute(select(DelegatedPass).where(DelegatedPass.parent_pass_lookup_hash == parent_context.pass_lookup_hash)).scalars())

    def get_delegated_pass(self, parent_context: ParentAccessContext, delegated_pass_id: str) -> DelegatedPass:
        # Public IDs are not stored raw; compare only peppered lookup hashes.
        delegated_pass_id_hash = hmac_sha256_prefixed(self.server_pepper, delegated_pass_id)
        for row in self.list_delegated_passes(parent_context):
            if row.constraints_json.get("delegated_pass_id_hash") == delegated_pass_id_hash:
                return row
        raise DelegatedPassError("delegated_pass_not_found")

    def revoke_delegated_pass(self, parent_context: ParentAccessContext, delegated_pass_id: str, reason: str) -> None:
        row = self.get_delegated_pass(parent_context, delegated_pass_id)
        row.status = "revoked"
        row.revoked_at = datetime.now(UTC)
        row.updated_at = datetime.now(UTC)
        row.constraints_json = {**(row.constraints_json or {}), "revoked_reason": reason}
        self.db.flush()
        self._audit("delegated_pass_revoked", parent_context, row.delegated_pass_hash, [str(scope) for scope in (row.scopes_json or [])], reason)

    def freeze_delegated_pass(self, delegated_pass_hash: str, reason: str) -> None:
        row = self.db.execute(select(DelegatedPass).where(DelegatedPass.delegated_pass_hash == delegated_pass_hash)).scalar_one_or_none()
        if row is None:
            raise DelegatedPassError("delegated_pass_not_found")
        row.status = "frozen"
        row.updated_at = datetime.now(UTC)
        row.constraints_json = {**(row.constraints_json or {}), "frozen_reason": reason}
        self.db.flush()
        self.audit_chain.record_event(event_type="delegated_pass_frozen", object_hash=row.delegated_pass_hash, pass_lookup_hash=row.parent_pass_lookup_hash, metadata={"reason": reason})

    def verify_delegated_pass(self, raw_delegated_pass: str, requested_scope: str, request_context: Any | None = None) -> DelegatedPass:
        if not raw_delegated_pass.startswith("bbd_live_"):
            raise DelegatedPassError("delegated_pass_invalid")
        lookup = hmac_sha256_prefixed(self.server_pepper, raw_delegated_pass)
        row = self.db.execute(select(DelegatedPass).where(DelegatedPass.delegated_pass_hash == lookup)).scalar_one_or_none()
        if row is None or not constant_time_equal(row.delegated_pass_hash, lookup):
            raise DelegatedPassError("delegated_pass_invalid")
        now = datetime.now(UTC)
        if row.status != "active":
            raise DelegatedPassError("delegated_pass_revoked")
        valid_from = row.valid_from.replace(tzinfo=UTC) if row.valid_from.tzinfo is None else row.valid_from
        valid_until = row.valid_until.replace(tzinfo=UTC) if row.valid_until.tzinfo is None else row.valid_until
        if valid_from > now or valid_until <= now:
            raise DelegatedPassError("delegated_pass_expired")
        if requested_scope not in set(row.scopes_json or []):
            raise DelegatedPassError("delegated_pass_scope_missing")
        self.mark_delegated_pass_used(row.delegated_pass_hash)
        return row

    def mark_delegated_pass_used(self, delegated_pass_hash: str) -> None:
        row = self.db.execute(select(DelegatedPass).where(DelegatedPass.delegated_pass_hash == delegated_pass_hash)).scalar_one_or_none()
        if row is not None:
            row.constraints_json = {**(row.constraints_json or {}), "last_used_at": datetime.now(UTC).isoformat()}
            self.db.flush()

    def freeze_invalid_delegations_after_downgrade(self, parent_pass_lookup_hash: str, new_entitlement: Any) -> int:
        allowed_scopes = set(getattr(new_entitlement, "scopes_json", []) or [])
        frozen = 0
        for row in self.db.execute(select(DelegatedPass).where(DelegatedPass.parent_pass_lookup_hash == parent_pass_lookup_hash, DelegatedPass.status == "active")).scalars():
            if not set(row.scopes_json or []).issubset(allowed_scopes):
                row.status = "frozen"
                row.updated_at = datetime.now(UTC)
                frozen += 1
        self.db.flush()
        return frozen

    def revoke_delegations_for_parent(self, parent_pass_lookup_hash: str, reason: str) -> int:
        count = 0
        for row in self.db.execute(select(DelegatedPass).where(DelegatedPass.parent_pass_lookup_hash == parent_pass_lookup_hash, DelegatedPass.status == "active")).scalars():
            row.status = "revoked"
            row.revoked_at = datetime.now(UTC)
            row.updated_at = datetime.now(UTC)
            row.constraints_json = {**(row.constraints_json or {}), "revoked_reason": reason}
            count += 1
        self.db.flush()
        return count

    def _active_count(self, parent_pass_lookup_hash: str) -> int:
        return len(list(self.db.execute(select(DelegatedPass.id).where(DelegatedPass.parent_pass_lookup_hash == parent_pass_lookup_hash, DelegatedPass.status == "active")).scalars()))

    def _audit(self, event_type: str, parent_context: ParentAccessContext, object_hash: str, scopes: list[str], reason: str) -> None:
        self.audit_chain.record_event(event_type=event_type, actor_hash=parent_context.session_hash, object_hash=object_hash, pass_lookup_hash=parent_context.pass_lookup_hash, certificate_fingerprint=parent_context.certificate_fingerprint, metadata={"scopes": scopes, "reason": reason})
