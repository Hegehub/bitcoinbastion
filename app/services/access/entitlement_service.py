"""Subscription Entitlement Overlay service for Bastion Proof-of-Access Auth.

Entitlements define the active commercial and technical access surface for an
Access Certificate. They are versioned overlays: renewal, upgrade, downgrade,
freeze, and revocation do not reissue the base Access Certificate.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.db.models.access import SubscriptionEntitlement
from app.domain.access.decisions import AccessDecision, PolicyDecision
from app.domain.access.plans import PlanCode, normalize_plan_code, plan_rank
from app.domain.access.scopes import ACCESS_SCOPES, FORBIDDEN_SCOPES
from app.services.access.crypto.hashing import canonical_json, reject_forbidden_secret_keys
from app.services.access.crypto.signatures import sign_subscription_entitlement, verify_subscription_entitlement_signature
from app.services.access.metric_catalog import get_metric_definition, get_metric_group_for_metric
from app.services.access.metric_costs import get_metric_cost
from app.services.access.plan_entitlements import (
    build_entitlement_overlay,
    required_plan_for_metric_group,
    validate_history_range_allowed,
    validate_interval_allowed,
)

ENTITLEMENT_TYPE = "bastion_subscription_entitlement"
ENTITLEMENT_VERSION = 1
ENTITLEMENT_STATUS_PENDING = "pending"
ENTITLEMENT_STATUS_ACTIVE = "active"
ENTITLEMENT_STATUS_GRACE = "grace"
ENTITLEMENT_STATUS_EXPIRED = "expired"
ENTITLEMENT_STATUS_FROZEN = "frozen"
ENTITLEMENT_STATUS_REVOKED = "revoked"
ENTITLEMENT_STATUS_CANCELLED = "cancelled"
ENTITLEMENT_STATUS_UPGRADED = "upgraded"
ENTITLEMENT_STATUS_DOWNGRADED = "downgraded"
ACTIVE_ACCESS_STATUSES = {ENTITLEMENT_STATUS_ACTIVE, ENTITLEMENT_STATUS_GRACE, ENTITLEMENT_STATUS_CANCELLED}
DENY_ALL_STATUSES = {ENTITLEMENT_STATUS_EXPIRED, ENTITLEMENT_STATUS_REVOKED}
AuditEmitter = Callable[[str, dict[str, Any]], None]


class SubscriptionEntitlementError(RuntimeError):
    """Base class for safe entitlement service errors."""


class EntitlementNotFoundError(SubscriptionEntitlementError):
    """Raised when an entitlement cannot be found."""


class EntitlementIntegrityError(SubscriptionEntitlementError):
    """Raised when entitlement state would become ambiguous or unsafe."""


class EntitlementSignatureError(SubscriptionEntitlementError):
    """Raised when entitlement signing or verification cannot be completed."""


@dataclass(frozen=True, slots=True)
class MetricEntitlements:
    groups: set[str]
    daily_metric_credits: int | None
    monthly_metric_credits: int | None
    max_history_days: int | None
    min_interval: str | None


class SubscriptionEntitlementService:
    def __init__(
        self,
        db: Session,
        *,
        issuer_private_key: str,
        issuer_key_id: str,
        issuer_public_key: str | None = None,
        crypto_epoch: int = 1,
        audit_emitter: AuditEmitter | None = None,
    ) -> None:
        self.db = db
        self.issuer_private_key = issuer_private_key
        self.issuer_key_id = issuer_key_id
        self.issuer_public_key = issuer_public_key
        self.crypto_epoch = crypto_epoch
        self.audit_emitter = audit_emitter

    def issue_entitlement(
        self,
        *,
        pass_lookup_hash: str,
        certificate_fingerprint: str,
        plan_code: PlanCode | str,
        valid_from: datetime,
        valid_until: datetime,
        grace_until: datetime | None = None,
        payment_intent_id: int | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> SubscriptionEntitlement:
        plan = normalize_plan_code(plan_code)
        self._validate_issue_inputs(pass_lookup_hash, certificate_fingerprint, valid_from, valid_until)
        if self.get_current_entitlement(pass_lookup_hash=pass_lookup_hash, include_restricted=False) is not None:
            raise EntitlementIntegrityError("Active entitlement already exists and must be replaced explicitly")
        return self._create_entitlement(
            pass_lookup_hash=pass_lookup_hash,
            certificate_fingerprint=certificate_fingerprint,
            plan=plan,
            status=ENTITLEMENT_STATUS_ACTIVE,
            valid_from=valid_from,
            valid_until=valid_until,
            grace_until=grace_until,
            previous=None,
            metadata={**(metadata or {}), "payment_intent_id": payment_intent_id},
            audit_event="entitlement_issued",
        )

    def get_current_entitlement(
        self,
        *,
        pass_lookup_hash: str | None = None,
        certificate_fingerprint: str | None = None,
        include_restricted: bool = False,
    ) -> SubscriptionEntitlement | None:
        if not pass_lookup_hash and not certificate_fingerprint:
            raise ValueError("pass_lookup_hash or certificate_fingerprint is required")
        now = datetime.now(UTC).replace(tzinfo=None)
        criteria = []
        if pass_lookup_hash:
            criteria.append(SubscriptionEntitlement.pass_lookup_hash == pass_lookup_hash)
        if certificate_fingerprint:
            criteria.append(SubscriptionEntitlement.certificate_fingerprint == certificate_fingerprint)
        statement = select(SubscriptionEntitlement).where(or_(*criteria)).order_by(
            SubscriptionEntitlement.valid_from.desc(), SubscriptionEntitlement.id.desc()
        )
        for entitlement in self.db.execute(statement).scalars():
            if not include_restricted and entitlement.status not in ACTIVE_ACCESS_STATUSES:
                continue
            if not include_restricted and _naive_utc(entitlement.valid_until) <= now:
                continue
            if not include_restricted and entitlement.status == ENTITLEMENT_STATUS_CANCELLED and _naive_utc(entitlement.valid_until) <= now:
                continue
            return entitlement
        return None

    def renew_entitlement(
        self,
        entitlement: SubscriptionEntitlement,
        *,
        valid_from: datetime,
        valid_until: datetime,
        grace_until: datetime | None = None,
        payment_intent_id: int | None = None,
    ) -> SubscriptionEntitlement:
        return self._replace_entitlement(
            entitlement,
            plan=normalize_plan_code(entitlement.plan_code),
            valid_from=valid_from,
            valid_until=valid_until,
            grace_until=grace_until,
            audit_event="entitlement_renewed",
            metadata={"payment_intent_id": payment_intent_id, "renewal": True},
        )

    def upgrade_entitlement(
        self,
        entitlement: SubscriptionEntitlement,
        *,
        new_plan_code: PlanCode | str,
        valid_from: datetime,
        valid_until: datetime,
        payment_intent_id: int | None = None,
    ) -> SubscriptionEntitlement:
        new_plan = normalize_plan_code(new_plan_code)
        if plan_rank(new_plan) <= plan_rank(normalize_plan_code(entitlement.plan_code)):
            raise EntitlementIntegrityError("Upgrade requires a higher plan")
        return self._replace_entitlement(
            entitlement,
            plan=new_plan,
            valid_from=valid_from,
            valid_until=valid_until,
            grace_until=None,
            audit_event="entitlement_upgraded",
            metadata={"payment_intent_id": payment_intent_id, "child_keys_not_modified": True},
            previous_status=ENTITLEMENT_STATUS_UPGRADED,
            upgrade_from_plan=entitlement.plan_code,
        )

    def downgrade_entitlement(
        self,
        entitlement: SubscriptionEntitlement,
        *,
        new_plan_code: PlanCode | str,
        valid_from: datetime,
        valid_until: datetime,
    ) -> SubscriptionEntitlement:
        new_plan = normalize_plan_code(new_plan_code)
        if plan_rank(new_plan) >= plan_rank(normalize_plan_code(entitlement.plan_code)):
            raise EntitlementIntegrityError("Downgrade requires a lower plan")
        return self._replace_entitlement(
            entitlement,
            plan=new_plan,
            valid_from=valid_from,
            valid_until=valid_until,
            grace_until=None,
            audit_event="entitlement_downgraded",
            metadata={"child_key_review_required": True, "delegated_pass_review_required": True},
            previous_status=ENTITLEMENT_STATUS_DOWNGRADED,
            downgrade_from_plan=entitlement.plan_code,
        )

    def freeze_entitlement(self, entitlement: SubscriptionEntitlement, reason: str = "frozen") -> SubscriptionEntitlement:
        entitlement.status = ENTITLEMENT_STATUS_FROZEN
        entitlement.frozen_at = datetime.now(UTC)
        entitlement.metadata_json = {**(entitlement.metadata_json or {}), "freeze_reason": reason}
        entitlement.updated_at = datetime.now(UTC)
        self._refresh_signature(entitlement)
        self.db.flush()
        self._emit_audit("entitlement_frozen", entitlement)
        return entitlement

    def expire_entitlement(self, entitlement: SubscriptionEntitlement) -> SubscriptionEntitlement:
        entitlement.status = ENTITLEMENT_STATUS_EXPIRED
        entitlement.updated_at = datetime.now(UTC)
        self._refresh_signature(entitlement)
        self.db.flush()
        self._emit_audit("entitlement_expired", entitlement)
        return entitlement

    def revoke_entitlement(self, entitlement: SubscriptionEntitlement, reason: str = "revoked") -> SubscriptionEntitlement:
        entitlement.status = ENTITLEMENT_STATUS_REVOKED
        entitlement.revoked_at = datetime.now(UTC)
        entitlement.metadata_json = {**(entitlement.metadata_json or {}), "revocation_reason": reason}
        entitlement.updated_at = datetime.now(UTC)
        self._refresh_signature(entitlement)
        self.db.flush()
        self._emit_audit("entitlement_revoked", entitlement)
        return entitlement

    def calculate_effective_scopes(self, entitlement: SubscriptionEntitlement) -> set[str]:
        if not self._status_allows_access(entitlement):
            return set()
        scopes = {scope for scope in (entitlement.scopes_json or []) if isinstance(scope, str)}
        return scopes - set(FORBIDDEN_SCOPES)

    def calculate_effective_limits(self, entitlement: SubscriptionEntitlement) -> dict[str, Any]:
        if entitlement.status == ENTITLEMENT_STATUS_GRACE:
            limits = dict(entitlement.limits_json or {})
            if isinstance(limits.get("requests_per_minute"), int):
                limits["requests_per_minute"] = max(1, limits["requests_per_minute"] // 2)
            return limits
        if not self._status_allows_access(entitlement):
            return {}
        return dict(entitlement.limits_json or {})

    def calculate_metric_entitlements(self, entitlement: SubscriptionEntitlement) -> MetricEntitlements:
        if not self._status_allows_access(entitlement):
            return MetricEntitlements(set(), 0, 0, 0, None)
        metric_json = entitlement.metric_entitlements_json or {}
        return MetricEntitlements(
            groups=set(metric_json.get("groups") or []),
            daily_metric_credits=metric_json.get("daily_metric_credits"),
            monthly_metric_credits=metric_json.get("monthly_metric_credits"),
            max_history_days=metric_json.get("max_history_days"),
            min_interval=metric_json.get("min_interval"),
        )

    def validate_entitlement_for_metric(
        self,
        entitlement: SubscriptionEntitlement,
        metric_group: str,
        metric_name: str | None = None,
        interval: str | None = None,
        history_days: int | None = None,
        estimated_cost: int | None = None,
    ) -> AccessDecision:
        status_decision = self._status_decision(entitlement)
        if status_decision is not None:
            return status_decision
        metrics = self.calculate_metric_entitlements(entitlement)
        if metric_group not in metrics.groups:
            required_plan = required_plan_for_metric_group(metric_group)
            return AccessDecision(
                decision=PolicyDecision.UPGRADE_REQUIRED if required_plan else PolicyDecision.METRIC_NOT_ALLOWED,
                reason="metric_group_not_allowed",
                required_plan=required_plan,
                current_plan=normalize_plan_code(entitlement.plan_code),
                requested_metric_group=metric_group,
                upgrade_available=required_plan is not None,
            )
        if metric_name is not None:
            definition = get_metric_definition(metric_name)
            if definition is None or get_metric_group_for_metric(metric_name) != metric_group:
                return AccessDecision(PolicyDecision.METRIC_NOT_ALLOWED, "unknown_metric", requested_metric_group=metric_group)
            estimated_cost = estimated_cost if estimated_cost is not None else get_metric_cost(metric_name)
        if estimated_cost is not None and metrics.daily_metric_credits is not None and estimated_cost > metrics.daily_metric_credits:
            return AccessDecision(PolicyDecision.QUOTA_EXCEEDED, "metric_credit_quota_exceeded", requested_metric_group=metric_group)
        if interval is not None and not self.validate_entitlement_for_interval(entitlement, interval).decision == PolicyDecision.ALLOW:
            return self.validate_entitlement_for_interval(entitlement, interval)
        if history_days is not None and not self.validate_entitlement_for_history_range(entitlement, history_days).decision == PolicyDecision.ALLOW:
            return self.validate_entitlement_for_history_range(entitlement, history_days)
        return AccessDecision(PolicyDecision.ALLOW, "metric_allowed", current_plan=normalize_plan_code(entitlement.plan_code), requested_metric_group=metric_group)

    def validate_entitlement_for_scope(self, entitlement: SubscriptionEntitlement, requested_scope: str) -> AccessDecision:
        status_decision = self._status_decision(entitlement)
        if status_decision is not None:
            return status_decision
        if requested_scope in FORBIDDEN_SCOPES or requested_scope not in ACCESS_SCOPES:
            return AccessDecision(PolicyDecision.DENY, "scope_denied", requested_scope=requested_scope)
        if requested_scope not in self.calculate_effective_scopes(entitlement):
            return AccessDecision(PolicyDecision.INSUFFICIENT_SCOPE, "insufficient_scope", requested_scope=requested_scope)
        return AccessDecision(PolicyDecision.ALLOW, "scope_allowed", requested_scope=requested_scope)

    def validate_entitlement_for_interval(self, entitlement: SubscriptionEntitlement, interval: str) -> AccessDecision:
        status_decision = self._status_decision(entitlement)
        if status_decision is not None:
            return status_decision
        if not validate_interval_allowed(normalize_plan_code(entitlement.plan_code), interval):
            return AccessDecision(PolicyDecision.DENY, "interval_not_allowed")
        return AccessDecision(PolicyDecision.ALLOW, "interval_allowed")

    def validate_entitlement_for_history_range(self, entitlement: SubscriptionEntitlement, history_days: int) -> AccessDecision:
        status_decision = self._status_decision(entitlement)
        if status_decision is not None:
            return status_decision
        if history_days < 0 or not validate_history_range_allowed(normalize_plan_code(entitlement.plan_code), history_days):
            return AccessDecision(PolicyDecision.DENY, "history_range_not_allowed")
        return AccessDecision(PolicyDecision.ALLOW, "history_range_allowed")

    def build_entitlement_payload(
        self,
        *,
        pass_lookup_hash: str,
        certificate_fingerprint: str,
        plan: PlanCode,
        status: str,
        valid_from: datetime,
        valid_until: datetime,
        grace_until: datetime | None,
    ) -> dict[str, Any]:
        overlay = build_entitlement_overlay(plan)
        limits = dict(overlay["limits"])
        metric_entitlements = {
            "groups": overlay["metric_groups"],
            "daily_metric_credits": limits.get("daily_metric_credits"),
            "monthly_metric_credits": limits.get("monthly_metric_credits"),
            "max_history_days": limits.get("max_history_days"),
            "min_interval": limits.get("min_interval"),
        }
        return {
            "type": ENTITLEMENT_TYPE,
            "version": ENTITLEMENT_VERSION,
            "pass_lookup_hash": pass_lookup_hash,
            "certificate_fingerprint": certificate_fingerprint,
            "plan": plan.value,
            "status": status,
            "valid_from": _isoformat(valid_from),
            "valid_until": _isoformat(valid_until),
            "grace_until": _isoformat(grace_until) if grace_until else None,
            "metric_entitlements": metric_entitlements,
            "limits": limits,
            "scopes": overlay["allowed_scopes"],
            "crypto_epoch": self.crypto_epoch,
            "issuer_key_id": self.issuer_key_id,
        }

    def verify_entitlement_signature(self, entitlement: SubscriptionEntitlement, public_key: str | None = None) -> bool:
        signature = (entitlement.issuer_signature_json or {}).get("signature")
        if not isinstance(signature, str):
            return False
        payload = self._payload_from_entitlement(entitlement)
        verification_key = public_key or self.issuer_public_key
        if verification_key is None:
            raise EntitlementSignatureError("Issuer public key is required for entitlement verification")
        return verify_subscription_entitlement_signature(payload, verification_key, signature).valid

    def to_public_response(self, entitlement: SubscriptionEntitlement) -> dict[str, Any]:
        return {
            "plan_code": entitlement.plan_code,
            "status": entitlement.status,
            "valid_from": entitlement.valid_from,
            "valid_until": entitlement.valid_until,
            "grace_until": entitlement.grace_until,
            "metric_groups": sorted((entitlement.metric_entitlements_json or {}).get("groups") or []),
            "scopes": sorted(entitlement.scopes_json or []),
            "limits": dict(entitlement.limits_json or {}),
            "crypto_epoch": entitlement.crypto_epoch,
            "issuer_key_id": entitlement.issuer_key_id,
            "created_at": entitlement.created_at,
        }

    def _replace_entitlement(
        self,
        previous: SubscriptionEntitlement,
        *,
        plan: PlanCode,
        valid_from: datetime,
        valid_until: datetime,
        grace_until: datetime | None,
        audit_event: str,
        metadata: dict[str, Any],
        previous_status: str = ENTITLEMENT_STATUS_EXPIRED,
        upgrade_from_plan: str | None = None,
        downgrade_from_plan: str | None = None,
    ) -> SubscriptionEntitlement:
        new_entitlement = self._create_entitlement(
            pass_lookup_hash=previous.pass_lookup_hash,
            certificate_fingerprint=previous.certificate_fingerprint or "",
            plan=plan,
            status=ENTITLEMENT_STATUS_ACTIVE,
            valid_from=valid_from,
            valid_until=valid_until,
            grace_until=grace_until,
            previous=previous,
            metadata=metadata,
            audit_event=audit_event,
            upgrade_from_plan=upgrade_from_plan,
            downgrade_from_plan=downgrade_from_plan,
        )
        previous.status = previous_status
        previous.replaced_by_entitlement_id = new_entitlement.id
        previous.updated_at = datetime.now(UTC)
        self.db.flush()
        return new_entitlement

    def _create_entitlement(
        self,
        *,
        pass_lookup_hash: str,
        certificate_fingerprint: str,
        plan: PlanCode,
        status: str,
        valid_from: datetime,
        valid_until: datetime,
        grace_until: datetime | None,
        previous: SubscriptionEntitlement | None,
        metadata: dict[str, Any],
        audit_event: str,
        upgrade_from_plan: str | None = None,
        downgrade_from_plan: str | None = None,
    ) -> SubscriptionEntitlement:
        self._validate_issue_inputs(pass_lookup_hash, certificate_fingerprint, valid_from, valid_until)
        payload = self.build_entitlement_payload(
            pass_lookup_hash=pass_lookup_hash,
            certificate_fingerprint=certificate_fingerprint,
            plan=plan,
            status=status,
            valid_from=valid_from,
            valid_until=valid_until,
            grace_until=grace_until,
        )
        signature = sign_subscription_entitlement(payload, self.issuer_private_key, self.issuer_key_id, self.crypto_epoch)
        signature_json = {
            "alg": signature.alg,
            "key_id": signature.key_id,
            "crypto_epoch": signature.crypto_epoch,
            "signature": signature.signature,
            "public_key_fingerprint": signature.public_key_fingerprint,
        }
        limits = dict(payload["limits"])
        metric_entitlements = dict(payload["metric_entitlements"])
        now = datetime.now(UTC)
        entitlement = SubscriptionEntitlement(
            pass_lookup_hash=pass_lookup_hash,
            certificate_fingerprint=certificate_fingerprint,
            plan_code=plan.value,
            status=status,
            metric_entitlements_json=metric_entitlements,
            limits_json=limits,
            scopes_json=payload["scopes"],
            issuer_key_id=self.issuer_key_id,
            issuer_signature_json=signature_json,
            crypto_epoch=self.crypto_epoch,
            valid_from=valid_from,
            valid_until=valid_until,
            grace_until=grace_until,
            previous_entitlement_id=previous.id if previous else None,
            upgrade_from_plan=upgrade_from_plan,
            downgrade_from_plan=downgrade_from_plan,
            metadata_json=metadata,
            created_at=now,
            updated_at=now,
        )
        self.db.add(entitlement)
        self.db.flush()
        self._emit_audit(audit_event, entitlement)
        return entitlement

    def _payload_from_entitlement(self, entitlement: SubscriptionEntitlement) -> dict[str, Any]:
        return {
            "type": ENTITLEMENT_TYPE,
            "version": ENTITLEMENT_VERSION,
            "pass_lookup_hash": entitlement.pass_lookup_hash,
            "certificate_fingerprint": entitlement.certificate_fingerprint,
            "plan": entitlement.plan_code,
            "status": entitlement.status,
            "valid_from": _isoformat(entitlement.valid_from),
            "valid_until": _isoformat(entitlement.valid_until),
            "grace_until": _isoformat(entitlement.grace_until) if entitlement.grace_until else None,
            "metric_entitlements": entitlement.metric_entitlements_json,
            "limits": entitlement.limits_json,
            "scopes": entitlement.scopes_json,
            "crypto_epoch": entitlement.crypto_epoch,
            "issuer_key_id": entitlement.issuer_key_id,
        }

    def _status_allows_access(self, entitlement: SubscriptionEntitlement) -> bool:
        now = datetime.now(UTC).replace(tzinfo=None)
        if entitlement.status in DENY_ALL_STATUSES or _naive_utc(entitlement.valid_until) <= now:
            return False
        return entitlement.status in ACTIVE_ACCESS_STATUSES

    def _status_decision(self, entitlement: SubscriptionEntitlement) -> AccessDecision | None:
        now = datetime.now(UTC).replace(tzinfo=None)
        if entitlement.status == ENTITLEMENT_STATUS_REVOKED:
            return AccessDecision(PolicyDecision.REVOKED, "entitlement_revoked", current_plan=normalize_plan_code(entitlement.plan_code))
        if entitlement.status == ENTITLEMENT_STATUS_FROZEN:
            return AccessDecision(PolicyDecision.FROZEN, "entitlement_frozen", current_plan=normalize_plan_code(entitlement.plan_code))
        if entitlement.status == ENTITLEMENT_STATUS_EXPIRED or _naive_utc(entitlement.valid_until) <= now:
            return AccessDecision(PolicyDecision.EXPIRED, "entitlement_expired", current_plan=normalize_plan_code(entitlement.plan_code))
        if self.issuer_public_key is not None and not self.verify_entitlement_signature(entitlement):
            return AccessDecision(PolicyDecision.INVALID_SIGNATURE, "entitlement_signature_invalid", current_plan=normalize_plan_code(entitlement.plan_code))
        return None

    def _refresh_signature(self, entitlement: SubscriptionEntitlement) -> None:
        payload = self._payload_from_entitlement(entitlement)
        signature = sign_subscription_entitlement(payload, self.issuer_private_key, self.issuer_key_id, self.crypto_epoch)
        entitlement.issuer_signature_json = {
            "alg": signature.alg,
            "key_id": signature.key_id,
            "crypto_epoch": signature.crypto_epoch,
            "signature": signature.signature,
            "public_key_fingerprint": signature.public_key_fingerprint,
        }

    def _validate_issue_inputs(self, pass_lookup_hash: str, certificate_fingerprint: str, valid_from: datetime, valid_until: datetime) -> None:
        if not pass_lookup_hash.startswith("hmac-sha256:"):
            raise EntitlementIntegrityError("pass_lookup_hash must be HMAC-SHA256 output")
        if not certificate_fingerprint.startswith("sha256:"):
            raise EntitlementIntegrityError("certificate_fingerprint must be SHA-256 prefixed")
        if valid_until <= valid_from:
            raise EntitlementIntegrityError("valid_until must be later than valid_from")

    def _emit_audit(self, event_type: str, entitlement: SubscriptionEntitlement) -> None:
        if self.audit_emitter is None:
            return
        payload = {
            "entitlement_id": entitlement.id,
            "certificate_fingerprint": entitlement.certificate_fingerprint,
            "plan_code": entitlement.plan_code,
            "status": entitlement.status,
            "issuer_key_id": entitlement.issuer_key_id,
            "crypto_epoch": entitlement.crypto_epoch,
            "created_at": _isoformat(entitlement.created_at),
        }
        reject_forbidden_secret_keys(payload)
        self.audit_emitter(event_type, payload)


def _isoformat(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


def _naive_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value
    return value.astimezone(UTC).replace(tzinfo=None)


def canonical_entitlement_payload(payload: Mapping[str, Any]) -> str:
    return canonical_json(payload)
