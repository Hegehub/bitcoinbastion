"""Human Intent Signature service for critical Proof-of-Access actions."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.access import AccessDevice, AccessHumanIntent
from app.schemas.access_intent import (
    HumanIntentAction,
    HumanIntentCreateRequest,
    HumanIntentManifest,
    HumanIntentResponse,
    HumanIntentRiskLevel,
    HumanIntentVerificationResult,
)
from app.services.access.audit_chain import AccessAuditChain
from app.services.access.crypto.hashing import canonical_json, secure_nonce_hex, sha256_prefixed
from app.services.access.crypto.signatures import SignatureSuiteRegistry

CRITICAL_HUMAN_INTENT_ACTIONS = frozenset(action.value for action in HumanIntentAction)
INTENT_STATUS_CREATED = "created"
INTENT_STATUS_VERIFIED = "verified"
INTENT_STATUS_USED = "used"
INTENT_STATUS_EXPIRED = "expired"
INTENT_STATUS_REJECTED = "rejected"


class HumanIntentError(ValueError):
    pass


@dataclass(frozen=True)
class HumanIntentContext:
    actor_fingerprint: str
    certificate_fingerprint: str
    session_fingerprint: str | None
    device_key_fingerprint: str
    plan_code: str
    granted_scopes: list[str]
    origin: str
    policy_decision_ref: str | None = None
    request_hash: str | None = None


class HumanIntentService:
    def __init__(self, db: Session, *, audit_chain: AccessAuditChain | None = None, ttl_seconds: int = 300) -> None:
        self.db = db
        self.audit_chain = audit_chain or AccessAuditChain(db)
        self.ttl_seconds = ttl_seconds
        self.signatures = SignatureSuiteRegistry()

    def build_manifest(
        self,
        *,
        action: str | HumanIntentAction,
        actor_fingerprint: str,
        certificate_fingerprint: str,
        session_fingerprint: str | None,
        origin: str,
        requested_scopes: list[str],
        granted_scopes: list[str],
        cannot_access: list[str],
        target_resource_type: str | None,
        target_resource_hash: str | None,
        plan_code: str,
        risk_level: str | HumanIntentRiskLevel,
        human_summary: str,
        consequences: list[str],
        policy_decision_ref: str | None = None,
        request_hash: str | None = None,
        created_at: datetime | None = None,
        expires_at: datetime | None = None,
        nonce: str | None = None,
    ) -> HumanIntentManifest:
        created = _aware(created_at or datetime.now(UTC))
        expires = _aware(expires_at or (created + timedelta(seconds=self.ttl_seconds)))
        manifest = HumanIntentManifest(
            action=HumanIntentAction(action),
            actor_fingerprint=actor_fingerprint,
            certificate_fingerprint=certificate_fingerprint,
            session_fingerprint=session_fingerprint,
            origin=origin,
            requested_scopes=sorted(set(requested_scopes)),
            granted_scopes=sorted(set(granted_scopes)),
            cannot_access=sorted(set(cannot_access)),
            target_resource_type=target_resource_type,
            target_resource_hash=target_resource_hash,
            plan_code=plan_code,
            risk_level=HumanIntentRiskLevel(risk_level),
            created_at=created,
            expires_at=expires,
            nonce=nonce or secure_nonce_hex(16),
            human_summary=human_summary,
            consequences=list(consequences),
            policy_decision_ref=policy_decision_ref,
            request_hash=request_hash,
        )
        self.validate_action_requirements(manifest)
        return manifest

    def canonicalize_manifest(self, manifest: HumanIntentManifest | dict[str, Any]) -> str:
        payload = manifest.model_dump(mode="json") if isinstance(manifest, HumanIntentManifest) else manifest
        return canonical_json(payload)

    def hash_manifest(self, manifest: HumanIntentManifest | dict[str, Any]) -> str:
        return sha256_prefixed(self.canonicalize_manifest(manifest))

    def create_intent(self, context: HumanIntentContext, request: HumanIntentCreateRequest, *, risk_level: str = "high") -> HumanIntentResponse:
        target_hash = request.target_resource_hash or (sha256_prefixed(request.target_resource_id) if request.target_resource_id else None)
        manifest = self.build_manifest(
            action=request.action,
            actor_fingerprint=context.actor_fingerprint,
            certificate_fingerprint=context.certificate_fingerprint,
            session_fingerprint=context.session_fingerprint,
            origin=request.origin or context.origin,
            requested_scopes=request.requested_scopes,
            granted_scopes=context.granted_scopes,
            cannot_access=request.cannot_access,
            target_resource_type=request.target_resource_type,
            target_resource_hash=target_hash,
            plan_code=context.plan_code,
            risk_level=risk_level,
            human_summary=request.human_summary,
            consequences=request.consequences,
            policy_decision_ref=context.policy_decision_ref,
            request_hash=context.request_hash,
        )
        intent_hash = self.hash_manifest(manifest)
        row = AccessHumanIntent(
            intent_hash=intent_hash,
            action=manifest.action.value,
            certificate_fingerprint=manifest.certificate_fingerprint,
            device_key_fingerprint=context.device_key_fingerprint,
            status=INTENT_STATUS_CREATED,
            expires_at=manifest.expires_at,
            canonical_manifest_json=manifest.model_dump(mode="json"),
            signature_hash=None,
            created_at=manifest.created_at,
            updated_at=datetime.now(UTC),
        )
        self.db.add(row)
        self.db.flush()
        self._audit("human_intent_created", row, decision="created")
        return HumanIntentResponse(
            intent_id=intent_hash,
            manifest=manifest,
            canonical_manifest_hash=intent_hash,
            expires_at=manifest.expires_at,
            signing_instructions="Review the human_summary, consequences, scopes, origin, and cannot_access fields, then sign the canonical_manifest_hash with your bound device key.",
        )

    def verify_intent_signature(self, *, intent_id: str, signature: str, signature_alg: str, device_key_fingerprint: str) -> HumanIntentVerificationResult:
        row = self._get_intent(intent_id)
        recomputed_hash = self.hash_manifest(row.canonical_manifest_json)
        now = datetime.now(UTC)
        if row.intent_hash != recomputed_hash:
            return self._reject(row, recomputed_hash, "manifest_tampered")
        if row.status == INTENT_STATUS_USED:
            return self._invalid(row, "intent_already_used")
        if _aware(row.expires_at) <= now:
            row.status = INTENT_STATUS_EXPIRED
            self.db.flush()
            self._audit("human_intent_expired", row, decision="expired")
            return self._invalid(row, "intent_expired")
        if row.device_key_fingerprint and row.device_key_fingerprint != device_key_fingerprint:
            return self._reject(row, recomputed_hash, "wrong_device_key")
        device = self.db.execute(select(AccessDevice).where(AccessDevice.device_key_fingerprint == device_key_fingerprint)).scalar_one_or_none()
        if device is None:
            return self._reject(row, recomputed_hash, "device_key_not_found")
        try:
            suite = self.signatures.get(signature_alg)
            verified = suite.verify(recomputed_hash, "human_intent", device.device_public_key, signature)
        except Exception:
            verified = None
        if verified is None or not verified.valid:
            return self._reject(row, recomputed_hash, "signature_invalid")
        row.status = INTENT_STATUS_VERIFIED
        row.device_key_fingerprint = device_key_fingerprint
        row.signature_hash = sha256_prefixed(signature)
        row.updated_at = now
        self.db.flush()
        self._audit("human_intent_signed", row, decision="verified")
        return HumanIntentVerificationResult(valid=True, decision="verified", manifest_hash=recomputed_hash, verified_at=now)

    def require_valid_intent(
        self,
        *,
        intent_id: str | None,
        action: str,
        origin: str | None = None,
        requested_scopes: list[str] | None = None,
        cannot_access: list[str] | None = None,
    ) -> AccessHumanIntent:
        if not intent_id:
            raise HumanIntentError("human_intent_required")
        row = self._get_intent(intent_id)
        if row.status != INTENT_STATUS_VERIFIED:
            raise HumanIntentError("human_intent_not_verified")
        if _aware(row.expires_at) <= datetime.now(UTC):
            row.status = INTENT_STATUS_EXPIRED
            self.db.flush()
            raise HumanIntentError("human_intent_expired")
        manifest = HumanIntentManifest(**row.canonical_manifest_json)
        if manifest.action.value != action:
            raise HumanIntentError("human_intent_action_mismatch")
        if origin is not None and manifest.origin != origin:
            raise HumanIntentError("human_intent_origin_mismatch")
        if requested_scopes is not None and sorted(set(manifest.requested_scopes)) != sorted(set(requested_scopes)):
            raise HumanIntentError("human_intent_scope_mismatch")
        if cannot_access is not None and sorted(set(manifest.cannot_access)) != sorted(set(cannot_access)):
            raise HumanIntentError("human_intent_cannot_access_mismatch")
        return row

    def mark_intent_used(self, intent_id: str) -> None:
        row = self._get_intent(intent_id)
        if row.status == INTENT_STATUS_USED:
            raise HumanIntentError("human_intent_replay")
        if row.status != INTENT_STATUS_VERIFIED:
            raise HumanIntentError("human_intent_not_verified")
        row.status = INTENT_STATUS_USED
        row.used_at = datetime.now(UTC)
        row.updated_at = row.used_at
        self.db.flush()
        self._audit("human_intent_used", row, decision="used")

    def is_critical_action(self, action: str) -> bool:
        return action in CRITICAL_HUMAN_INTENT_ACTIONS

    def validate_action_requirements(self, manifest: HumanIntentManifest) -> None:
        # Pydantic validates field-level requirements; this hook keeps service callers explicit.
        if self.is_critical_action(manifest.action.value) and not manifest.human_summary.strip():
            raise HumanIntentError("human_summary_required")

    def get_intent_response(self, intent_id: str) -> HumanIntentResponse:
        row = self._get_intent(intent_id)
        manifest = HumanIntentManifest(**row.canonical_manifest_json)
        manifest_hash = self.hash_manifest(manifest)
        return HumanIntentResponse(
            intent_id=row.intent_hash,
            manifest=manifest,
            canonical_manifest_hash=manifest_hash,
            expires_at=manifest.expires_at,
            signing_instructions="Intent status endpoint; sign only if status is created and all manifest fields match the action you expect.",
        )

    def _get_intent(self, intent_id: str) -> AccessHumanIntent:
        row = self.db.execute(select(AccessHumanIntent).where(AccessHumanIntent.intent_hash == intent_id)).scalar_one_or_none()
        if row is None:
            raise HumanIntentError("human_intent_not_found")
        return row

    def _invalid(self, row: AccessHumanIntent, reason: str) -> HumanIntentVerificationResult:
        return HumanIntentVerificationResult(valid=False, decision="rejected", reason=reason, manifest_hash=row.intent_hash, verified_at=None)

    def _reject(self, row: AccessHumanIntent, manifest_hash: str, reason: str) -> HumanIntentVerificationResult:
        row.status = INTENT_STATUS_REJECTED
        row.updated_at = datetime.now(UTC)
        self.db.flush()
        self._audit("human_intent_rejected", row, decision="rejected", reason=reason)
        return HumanIntentVerificationResult(valid=False, decision="rejected", reason=reason, manifest_hash=manifest_hash, verified_at=None)

    def _audit(self, event_type: str, row: AccessHumanIntent, *, decision: str, reason: str | None = None) -> None:
        manifest = row.canonical_manifest_json or {}
        self.audit_chain.record_event(
            event_type=event_type,
            object_hash=row.intent_hash,
            certificate_fingerprint=row.certificate_fingerprint,
            device_key_fingerprint=row.device_key_fingerprint,
            metadata={
                "intent_hash": row.intent_hash,
                "action": row.action,
                "target_resource_hash": manifest.get("target_resource_hash"),
                "risk_level": manifest.get("risk_level"),
                "decision": decision,
                "reason": reason,
            },
        )


def _aware(value: datetime) -> datetime:
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)
