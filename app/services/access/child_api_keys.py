"""Scoped Child API Key service for Proof-of-Access Auth."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from types import SimpleNamespace
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.access import ChildApiKey
from app.services.access.audit_chain import AccessAuditChain
from app.services.access.crypto.hashing import constant_time_equal, hmac_sha256_prefixed, secure_nonce_hex, sha256_prefixed
from app.services.access.key_constraints import ParentAccessContext, validate_child_key_constraints
from app.services.access.key_redaction import assert_no_raw_secret_in_payload


@dataclass(frozen=True)
class ChildApiKeyCreateResult:
    key_id: str
    raw_child_api_key: str
    scopes: list[str]
    limits: dict[str, Any]
    expires_at: datetime
    warning: str


class ChildApiKeyError(ValueError):
    pass


class ChildApiKeyService:
    def __init__(self, db: Session, *, server_pepper: str, audit_chain: AccessAuditChain | None = None) -> None:
        if not server_pepper:
            raise ChildApiKeyError("child_key_pepper_required")
        self.db = db
        self.server_pepper = server_pepper
        self.audit_chain = audit_chain or AccessAuditChain(db)

    def create_child_key(self, parent_context: ParentAccessContext, request: Any, human_intent_signature: str | None = None) -> ChildApiKeyCreateResult:
        scopes = list(request.scopes)
        existing_count = self._active_count(parent_context.pass_lookup_hash)
        constraint_request = SimpleNamespace(**request.model_dump() if hasattr(request, "model_dump") else vars(request))
        constraint_request.human_intent_verified = bool(human_intent_signature)
        validate_child_key_constraints(parent_context, constraint_request, existing_count)
        key_id = secure_nonce_hex(16)
        secret = secure_nonce_hex(32)
        raw_key = f"bbk_live_{key_id}_{secret}"
        key_id_hash = hmac_sha256_prefixed(self.server_pepper, key_id)
        key_secret_hash = hmac_sha256_prefixed(self.server_pepper, raw_key)
        metadata = {
            "description": getattr(request, "description", None),
            "metric_entitlements": getattr(request, "metric_entitlements", {}) or {},
            "denied_scopes": getattr(request, "denied_scopes", []) or [],
            "created_by_session_hash": parent_context.session_hash,
            "created_by_device_fingerprint": parent_context.device_key_fingerprint,
            "requires_request_signing": getattr(request, "requires_request_signing", True),
            "can_delegate": getattr(request, "can_delegate", False),
            "risk_level": "medium" if getattr(request, "can_delegate", False) else "low",
            "audit_fingerprint": sha256_prefixed(key_secret_hash),
        }
        assert_no_raw_secret_in_payload({"metadata": metadata})
        persisted_limits = {
            **(getattr(request, "limits", {}) or {}),
            "requires_request_signing": metadata["requires_request_signing"],
            "can_delegate": metadata["can_delegate"],
            "risk_level": metadata["risk_level"],
            "audit_fingerprint": metadata["audit_fingerprint"],
        }
        row = ChildApiKey(
            parent_pass_lookup_hash=parent_context.pass_lookup_hash,
            key_id_hash=key_id_hash,
            key_secret_hash=key_secret_hash,
            name=request.name,
            scopes_json=scopes,
            limits_json=persisted_limits,
            cannot_access_json=metadata["denied_scopes"],
            status="active",
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            expires_at=request.expires_at,
            last_used_at=None,
        )
        self.db.add(row)
        self.db.flush()
        self._audit("child_api_key_created", parent_context, row.key_secret_hash, scopes, "created")
        return ChildApiKeyCreateResult(
            key_id=key_id,
            raw_child_api_key=raw_key,
            scopes=scopes,
            limits=row.limits_json or {},
            expires_at=row.expires_at,
            warning="Store this key now. It will not be shown again.",
        )

    def list_child_keys(self, parent_context: ParentAccessContext) -> list[ChildApiKey]:
        return list(self.db.execute(select(ChildApiKey).where(ChildApiKey.parent_pass_lookup_hash == parent_context.pass_lookup_hash)).scalars())

    def get_child_key(self, parent_context: ParentAccessContext, key_id: str) -> ChildApiKey:
        key_id_hash = hmac_sha256_prefixed(self.server_pepper, key_id)
        row = self.db.execute(select(ChildApiKey).where(ChildApiKey.parent_pass_lookup_hash == parent_context.pass_lookup_hash, ChildApiKey.key_id_hash == key_id_hash)).scalar_one_or_none()
        if row is None:
            raise ChildApiKeyError("child_key_not_found")
        return row

    def revoke_child_key(self, parent_context: ParentAccessContext, key_id: str, reason: str) -> None:
        row = self.get_child_key(parent_context, key_id)
        row.status = "revoked"
        row.revoked_at = datetime.now(UTC)
        row.updated_at = datetime.now(UTC)
        row.limits_json = {**(row.limits_json or {}), "revoked_reason": reason}
        self.db.flush()
        self._audit("child_api_key_revoked", parent_context, row.key_secret_hash, [str(scope) for scope in (row.scopes_json or [])], reason)

    def freeze_child_key(self, key_id: str, reason: str) -> None:
        key_id_hash = hmac_sha256_prefixed(self.server_pepper, key_id)
        row = self.db.execute(select(ChildApiKey).where(ChildApiKey.key_id_hash == key_id_hash)).scalar_one_or_none()
        if row is None:
            raise ChildApiKeyError("child_key_not_found")
        row.status = "frozen"
        row.updated_at = datetime.now(UTC)
        row.limits_json = {**(row.limits_json or {}), "frozen_reason": reason}
        self.db.flush()
        self.audit_chain.record_event(event_type="child_api_key_frozen", object_hash=row.key_secret_hash, pass_lookup_hash=row.parent_pass_lookup_hash, metadata={"reason": reason})

    def rotate_child_key(self, parent_context: ParentAccessContext, key_id: str, human_intent_signature: str | None = None) -> ChildApiKeyCreateResult:
        if not human_intent_signature:
            raise ChildApiKeyError("human_intent_required")
        old = self.get_child_key(parent_context, key_id)
        old.status = "rotated"
        old.revoked_at = datetime.now(UTC)
        old.updated_at = datetime.now(UTC)
        request = SimpleNamespace(name=old.name or "rotated child key", description=None, scopes=list(old.scopes_json or []), denied_scopes=list(old.cannot_access_json or []), metric_entitlements={}, limits=old.limits_json or {}, expires_at=old.expires_at, requires_request_signing=True, can_delegate=False)
        result = self.create_child_key(parent_context, request, human_intent_signature=human_intent_signature)
        self.audit_chain.record_event(event_type="child_api_key_rotated", object_hash=old.key_secret_hash, pass_lookup_hash=parent_context.pass_lookup_hash, metadata={"new_key_id": result.key_id})
        return result

    def verify_child_key(self, raw_key: str, requested_scope: str, request_context: Any | None = None) -> ChildApiKey:
        parts = raw_key.split("_")
        if len(parts) < 4 or not raw_key.startswith("bbk_live_"):
            raise ChildApiKeyError("child_key_invalid")
        key_id = parts[2]
        key_id_hash = hmac_sha256_prefixed(self.server_pepper, key_id)
        row = self.db.execute(select(ChildApiKey).where(ChildApiKey.key_id_hash == key_id_hash)).scalar_one_or_none()
        if row is None or not constant_time_equal(row.key_secret_hash, hmac_sha256_prefixed(self.server_pepper, raw_key)):
            raise ChildApiKeyError("child_key_invalid")
        if row.status != "active":
            raise ChildApiKeyError("child_key_revoked")
        expires_at = row.expires_at.replace(tzinfo=UTC) if row.expires_at.tzinfo is None else row.expires_at
        if expires_at <= datetime.now(UTC):
            raise ChildApiKeyError("child_key_expired")
        if requested_scope not in set(row.scopes_json or []):
            raise ChildApiKeyError("child_key_scope_missing")
        self.mark_child_key_used(row.key_id_hash)
        return row

    def mark_child_key_used(self, key_id_hash: str) -> None:
        row = self.db.execute(select(ChildApiKey).where(ChildApiKey.key_id_hash == key_id_hash)).scalar_one_or_none()
        if row is not None:
            row.last_used_at = datetime.now(UTC)
            self.db.flush()

    def freeze_invalid_children_after_downgrade(self, parent_pass_lookup_hash: str, new_entitlement: Any) -> int:
        allowed_scopes = set(getattr(new_entitlement, "scopes_json", []) or [])
        frozen = 0
        for row in self.db.execute(select(ChildApiKey).where(ChildApiKey.parent_pass_lookup_hash == parent_pass_lookup_hash, ChildApiKey.status == "active")).scalars():
            if not set(row.scopes_json or []).issubset(allowed_scopes):
                row.status = "frozen"
                row.updated_at = datetime.now(UTC)
                frozen += 1
        self.db.flush()
        return frozen

    def revoke_children_for_parent(self, parent_pass_lookup_hash: str, reason: str) -> int:
        count = 0
        for row in self.db.execute(select(ChildApiKey).where(ChildApiKey.parent_pass_lookup_hash == parent_pass_lookup_hash, ChildApiKey.status == "active")).scalars():
            row.status = "revoked"
            row.revoked_at = datetime.now(UTC)
            row.updated_at = datetime.now(UTC)
            count += 1
        self.db.flush()
        return count

    def _active_count(self, parent_pass_lookup_hash: str) -> int:
        return len(list(self.db.execute(select(ChildApiKey.id).where(ChildApiKey.parent_pass_lookup_hash == parent_pass_lookup_hash, ChildApiKey.status == "active")).scalars()))

    def _audit(self, event_type: str, parent_context: ParentAccessContext, object_hash: str, scopes: list[str], reason: str) -> None:
        self.audit_chain.record_event(event_type=event_type, actor_hash=parent_context.session_hash, object_hash=object_hash, pass_lookup_hash=parent_context.pass_lookup_hash, certificate_fingerprint=parent_context.certificate_fingerprint, metadata={"scopes": scopes, "reason": reason})
