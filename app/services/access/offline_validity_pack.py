"""Canonical Offline Validity Pack v1 issuer and reconciliation service.

Repository audit found no prior pack writer/verifier; only entitlement flags,
revocation targets and action constants existed. This module is therefore the
single canonical pack format. Local queues are projections bound to this pack,
not competing authorization sources.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
import secrets
from typing import Any, Protocol

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.access import (
    OfflinePackLocalEvent,
    OfflinePackReconciliation,
    OfflineValidityPack,
)
from app.domain.access.plans import PlanCode, normalize_plan_code, plan_rank
from app.services.access.audit_chain import AccessAuditChain
from app.services.access.crypto.hashing import (
    canonical_json,
    reject_forbidden_secret_keys,
    sha256_prefixed,
)
from app.services.access.crypto.issuer_envelope import (
    BastionIssuedObjectType,
    build_classical_issuer_envelope,
)
from app.services.access.crypto.migration_policy import SignatureRequirementPolicy
from app.services.access.crypto.signatures import sign_offline_validity_pack
from app.services.access.offline_policy import (
    FORBIDDEN_OFFLINE_ACTIONS,
    PROFILE_RULES,
    OfflineProfile,
)
from app.services.access.policy_context import AccessPolicyContext
from app.services.access.policy_engine import AccessPolicyEngine, POLICY_DECISION_ALLOW

PACK_TYPE = "bastion_offline_validity_pack"
PACK_VERSION = 1
PACK_SCHEMA_EPOCH = 1
SAFETY_WARNING = "This offline pack is limited, device-bound and time-bound. It does not authorize Bitcoin transactions, treasury administration, recovery completion or unrestricted API access."


class OfflinePackError(ValueError):
    pass


class OfflinePackPolicy(Protocol):
    def evaluate_offline_pack(self, request: "OfflinePackIssueRequest") -> Mapping[str, Any]: ...


class OfflinePackRevocations(Protocol):
    def check_offline_pack_targets(self, **targets: str | None) -> Mapping[str, object]: ...


class AccessPolicyEngineOfflinePackPolicy:
    """Keep the online Access Policy Engine authoritative at pack issuance."""

    def __init__(
        self,
        engine: AccessPolicyEngine,
        context_factory: Callable[["OfflinePackIssueRequest"], AccessPolicyContext],
    ) -> None:
        self.engine, self.context_factory = engine, context_factory

    def evaluate_offline_pack(self, request: "OfflinePackIssueRequest") -> Mapping[str, Any]:
        decision = self.engine.evaluate(self.context_factory(request))
        return {
            "decision": "allow" if decision.decision == POLICY_DECISION_ALLOW else "deny",
            "reason_code": decision.reason_code,
            "policy_hash": decision.policy_hash,
            "allowed_scopes": decision.metadata.get("allowed_scopes", ()),
            "allowed_metric_groups": decision.metadata.get("allowed_metric_groups", ()),
        }


@dataclass(frozen=True, slots=True)
class OfflinePackIssueRequest:
    principal_hash: str
    principal_type: str
    proof_method: str
    verification_strength: str
    device_key_fingerprint: str
    device_class: str
    entitlement_fingerprint: str
    plan: str
    entitlement_scopes: frozenset[str]
    entitlement_metric_groups: frozenset[str]
    entitlement_expires_at: datetime
    profile: OfflineProfile
    requested_scopes: frozenset[str]
    requested_metric_groups: frozenset[str]
    requested_expires_at: datetime
    revocation_epoch: int
    policy_epoch: int
    crypto_epoch: int
    entitlement_epoch: int
    pop_verified: bool
    human_intent_verified: bool
    step_up_verified: bool = False
    access_certificate_fingerprint: str | None = None
    access_certificate_expires_at: datetime | None = None
    certificate_active: bool = False
    stable_auth_domain_verified: bool = False
    maximum_value_limits: Mapping[str, int] | None = None
    object_constraints: Mapping[str, str] | None = None
    idempotency_key_hash: str | None = None


@dataclass(frozen=True, slots=True)
class OfflinePackIssueResult:
    pack_fingerprint: str
    export_pack: dict[str, Any]
    expires_at: datetime
    warning: str = SAFETY_WARNING
    idempotent_replay: bool = False


class OfflineValidityPackService:
    def __init__(
        self,
        db: Session,
        *,
        issuer_private_key: str,
        issuer_key_id: str,
        policy: OfflinePackPolicy,
        revocations: OfflinePackRevocations,
        crypto_epoch: int = 1,
        audit_chain: AccessAuditChain | None = None,
        clock: Callable[[], datetime] | None = None,
        enabled: bool = False,
        reconciliation_grace_seconds: int = 900,
        metric_emitter: Callable[[str, Mapping[str, str]], None] | None = None,
    ) -> None:
        self.db, self.private_key, self.key_id = db, issuer_private_key, issuer_key_id
        self.policy, self.revocations, self.crypto_epoch = policy, revocations, crypto_epoch
        self.audit, self.clock = (
            audit_chain or AccessAuditChain(db),
            clock or (lambda: datetime.now(UTC)),
        )
        self.enabled, self.reconciliation_grace_seconds = enabled, reconciliation_grace_seconds
        self.metric_emitter = metric_emitter

    def issue_pack(self, request: OfflinePackIssueRequest) -> OfflinePackIssueResult:
        if not self.enabled:
            raise OfflinePackError("offline_packs_disabled")
        self._validate_issue(request)
        self._audit(
            "offline_pack_requested",
            request.principal_hash,
            request.device_key_fingerprint,
            request.profile.value,
        )
        existing = self._idempotent(request)
        if existing:
            return OfflinePackIssueResult(
                existing.pack_fingerprint,
                dict(existing.signed_pack_json),
                _utc(existing.expires_at),
                idempotent_replay=True,
            )
        decision = self.policy.evaluate_offline_pack(request)
        if decision.get("decision") != "allow":
            self._audit(
                "offline_pack_policy_denied",
                request.principal_hash,
                request.device_key_fingerprint,
                str(decision.get("reason_code", "policy_denied")),
            )
            raise OfflinePackError(str(decision.get("reason_code", "policy_denied")))
        self._audit(
            "offline_pack_policy_allowed",
            request.principal_hash,
            request.device_key_fingerprint,
            str(decision.get("reason_code", "allowed")),
        )
        rule = PROFILE_RULES[request.profile]
        allowed_scopes = (
            request.requested_scopes
            & request.entitlement_scopes
            & frozenset(decision.get("allowed_scopes", ()))
        )
        allowed_metrics = (
            request.requested_metric_groups
            & request.entitlement_metric_groups
            & frozenset(decision.get("allowed_metric_groups", ()))
        )
        if allowed_scopes != request.requested_scopes:
            raise OfflinePackError("scope_not_allowed")
        if allowed_metrics != request.requested_metric_groups:
            raise OfflinePackError("metric_not_allowed")
        now = self.clock()
        expiry_bounds = [
            request.requested_expires_at,
            request.entitlement_expires_at,
            now + timedelta(seconds=int(rule["max_ttl"])),
        ]
        if request.access_certificate_expires_at:
            expiry_bounds.append(request.access_certificate_expires_at)
        expires_at = min(_utc(value) for value in expiry_bounds)
        if expires_at <= now:
            raise OfflinePackError("entitlement_expired")
        self._check_revocations(request)
        pack_id = f"ovp_{secrets.token_urlsafe(24)}"
        pack_id_hash = sha256_prefixed(pack_id)
        reconcile_before = expires_at + timedelta(seconds=self.reconciliation_grace_seconds)
        payload: dict[str, Any] = {
            "type": PACK_TYPE,
            "version": PACK_VERSION,
            "schema_epoch": PACK_SCHEMA_EPOCH,
            "pack_id": pack_id,
            "principal": {
                "principal_type": request.principal_type,
                "principal_hash": request.principal_hash,
            },
            "device_binding": {
                "device_key_fingerprint": request.device_key_fingerprint,
                "device_class": request.device_class,
                "binding_required": True,
            },
            "access_certificate": {
                "required": bool(rule["certificate_required"]),
                "certificate_fingerprint": request.access_certificate_fingerprint,
            },
            "subscription": {
                "entitlement_fingerprint": request.entitlement_fingerprint,
                "plan": request.plan,
                "valid_until": _iso(request.entitlement_expires_at),
            },
            "offline_policy": {
                "profile": request.profile.value,
                "allowed_actions": sorted(rule["allowed_actions"]),
                "allowed_scopes": sorted(allowed_scopes),
                "allowed_metric_groups": sorted(allowed_metrics),
                "denied_actions": sorted(FORBIDDEN_OFFLINE_ACTIONS),
                "object_constraints": dict(request.object_constraints or {}),
                "quota": {"maximum_operations": int(rule["max_operations"])},
                "maximum_value_limits": dict(request.maximum_value_limits or {}),
            },
            "epochs": {
                "revocation_epoch": request.revocation_epoch,
                "policy_epoch": request.policy_epoch,
                "crypto_epoch": request.crypto_epoch,
                "entitlement_epoch": request.entitlement_epoch,
            },
            "validity": {
                "issued_at": _iso(now),
                "not_before": _iso(now),
                "expires_at": _iso(expires_at),
                "maximum_offline_seconds": int(rule["max_ttl"]),
            },
            "reconciliation": {
                "required": True,
                "reconcile_before": _iso(reconcile_before),
                "maximum_pending_events": int(rule["max_pending_events"]),
            },
        }
        fingerprint = sha256_prefixed(canonical_json(payload))
        signature = sign_offline_validity_pack(
            payload, self.private_key, self.key_id, self.crypto_epoch
        )
        issuer_envelope = build_classical_issuer_envelope(
            payload,
            object_type=BastionIssuedObjectType.OFFLINE_VALIDITY_PACK,
            object_id_hash=pack_id_hash,
            object_fingerprint=fingerprint,
            issuer_key_id=self.key_id,
            issuer_private_key=self.private_key,
            crypto_epoch=self.crypto_epoch,
            policy_epoch=request.policy_epoch,
            schema_epoch=PACK_SCHEMA_EPOCH,
            expires_at=expires_at,
            requirement=SignatureRequirementPolicy.CLASSICAL_REQUIRED_PQ_OPTIONAL,
        )
        envelope_json = issuer_envelope.to_dict()
        exported = {
            **payload,
            "pack_fingerprint": fingerprint,
            "issuer": {
                "issuer_key_id": self.key_id,
                "signature_suite": signature.alg,
                "crypto_epoch": signature.crypto_epoch,
                "classical_signature": {"alg": signature.alg, "sig": signature.signature},
                "post_quantum_signature": None,
                "envelope": envelope_json,
            },
        }
        row = OfflineValidityPack(
            pack_id_hash=pack_id_hash,
            pack_fingerprint=fingerprint,
            principal_hash=request.principal_hash,
            principal_type=request.principal_type,
            device_key_fingerprint=request.device_key_fingerprint,
            access_certificate_fingerprint=request.access_certificate_fingerprint,
            entitlement_fingerprint=request.entitlement_fingerprint,
            profile=request.profile.value,
            policy_snapshot_json={
                **payload["offline_policy"],
                "_idempotency_key_hash": request.idempotency_key_hash,
            },
            signed_pack_json=exported,
            revocation_epoch=request.revocation_epoch,
            policy_epoch=request.policy_epoch,
            crypto_epoch=request.crypto_epoch,
            entitlement_epoch=request.entitlement_epoch,
            issued_at=now,
            not_before=now,
            expires_at=expires_at,
            reconcile_before=reconcile_before,
            status="active",
            issuer_key_id=self.key_id,
            signature_suite=signature.alg,
            issuer_envelope_json=envelope_json,
            issuer_envelope_hash=sha256_prefixed(canonical_json(envelope_json)),
            signature_requirement_policy=issuer_envelope.required_signature_policy.value,
            crypto_assurance=issuer_envelope.assurance_level.value,
            requires_reissue=False,
            created_at=now,
            updated_at=now,
        )
        self.db.add(row)
        self.db.flush()
        self._audit("offline_pack_issued", request.principal_hash, fingerprint, "issued")
        self._audit("offline_pack_exported", request.principal_hash, fingerprint, "exported")
        self._metric(
            "bastion_offline_packs_issued_total", request.profile.value, "success", "issued"
        )
        return OfflinePackIssueResult(fingerprint, exported, expires_at)

    def revoke_pack(self, pack_fingerprint: str, reason_code: str = "revoked") -> None:
        row = self._row(pack_fingerprint)
        if row.status == "revoked":
            return
        row.status, row.revoked_at, row.updated_at = "revoked", self.clock(), self.clock()
        self._audit("offline_pack_revoked", row.principal_hash, row.pack_fingerprint, reason_code)
        self._metric("bastion_offline_packs_revoked_total", row.profile, "revoked", reason_code)

    def get_pack(self, pack_fingerprint: str) -> OfflineValidityPack:
        return self._row(pack_fingerprint)

    def list_active_packs(self, principal_hash: str) -> list[OfflineValidityPack]:
        return list(
            self.db.execute(
                select(OfflineValidityPack).where(
                    OfflineValidityPack.principal_hash == principal_hash,
                    OfflineValidityPack.status == "active",
                    OfflineValidityPack.expires_at > self.clock(),
                )
            ).scalars()
        )

    def expire_pack(self, pack_fingerprint: str) -> None:
        row = self._row(pack_fingerprint)
        if row.status != "active":
            return
        row.status, row.updated_at = "expired", self.clock()
        self._audit("offline_pack_expired", row.principal_hash, row.pack_fingerprint, "expired")

    def queue_local_event(
        self,
        pack_fingerprint: str,
        event_type: str,
        safe_details: Mapping[str, Any],
    ) -> OfflinePackLocalEvent:
        """Persist an append-only local event so the queue survives application restart."""
        reject_forbidden_secret_keys(dict(safe_details))
        row = self._row(pack_fingerprint)
        if row.status != "active":
            raise OfflinePackError("pack_revoked")
        events = list(
            self.db.execute(
                select(OfflinePackLocalEvent)
                .where(OfflinePackLocalEvent.pack_id == row.id)
                .order_by(OfflinePackLocalEvent.sequence_number)
                .with_for_update()
            ).scalars()
        )
        maximum = int(row.policy_snapshot_json.get("quota", {}).get("maximum_operations", 0))
        pending_limit = int(
            row.signed_pack_json.get("reconciliation", {}).get("maximum_pending_events", 0)
        )
        if len(events) >= min(maximum, pending_limit):
            raise OfflinePackError("queue_limit_reached")
        occurred_at = self.clock()
        event = append_local_event(
            [
                {
                    "sequence": item.sequence_number,
                    "previous_event_hash": item.previous_event_hash,
                    "event_hash": item.event_hash,
                    "event_type": item.event_type,
                    "occurred_at": _iso(item.occurred_at),
                    "safe_details": item.safe_details_json,
                }
                for item in events
            ],
            event_type,
            safe_details,
            occurred_at,
        )
        stored = OfflinePackLocalEvent(
            pack_id=row.id,
            sequence_number=event["sequence"],
            previous_event_hash=event["previous_event_hash"],
            event_hash=event["event_hash"],
            event_type=event_type,
            safe_details_json=dict(safe_details),
            occurred_at=occurred_at,
        )
        self.db.add(stored)
        self.db.flush()
        self._audit("offline_operation_queued", row.principal_hash, stored.event_hash, event_type)
        return stored

    def reconcile_pack(
        self,
        pack_fingerprint: str,
        events: list[dict[str, Any]],
        *,
        current_revocation_epoch: int,
        current_policy_epoch: int,
        entitlement_active: bool = True,
    ) -> dict[str, Any]:
        row = self._row(pack_fingerprint)
        try:
            root = verify_local_event_chain(events)
        except OfflinePackError:
            self._audit(
                "offline_event_chain_invalid",
                row.principal_hash,
                row.pack_fingerprint,
                "event_chain_invalid",
            )
            raise
        existing = self.db.execute(
            select(OfflinePackReconciliation).where(
                OfflinePackReconciliation.pack_id == row.id,
                OfflinePackReconciliation.event_chain_root == root,
            )
        ).scalar_one_or_none()
        if existing:
            return dict(existing.result_json)
        if row.status == "revoked":
            outcome = "pack_revoked"
        elif not entitlement_active:
            outcome = "entitlement_changed"
        elif current_revocation_epoch > row.revocation_epoch:
            outcome = "pack_revoked"
        elif current_policy_epoch != row.policy_epoch:
            outcome = "policy_changed"
        else:
            outcome = "reconciled"
        result = {"outcome": outcome, "event_count": len(events), "event_chain_root": root}
        rec = OfflinePackReconciliation(
            pack_id=row.id,
            event_chain_root=root,
            event_count=len(events),
            reconciliation_status=outcome,
            reconciled_at=self.clock(),
            result_json=result,
        )
        self.db.add(rec)
        self.db.flush()
        self._audit(
            "offline_pack_reconciled"
            if outcome == "reconciled"
            else "offline_pack_reconciliation_failed",
            row.principal_hash,
            root,
            outcome,
        )
        self._metric("bastion_offline_pack_reconciliations_total", row.profile, outcome, outcome)
        return result

    def _validate_issue(self, request: OfflinePackIssueRequest) -> None:
        if request.principal_type not in {"bitcoin_wallet_principal", "lightning_wallet_principal"}:
            raise OfflinePackError("unsupported_principal")
        if not request.pop_verified or not request.human_intent_verified:
            raise OfflinePackError("human_intent_required")
        rule = PROFILE_RULES[request.profile]
        if plan_rank(normalize_plan_code(request.plan)) < plan_rank(
            normalize_plan_code(str(rule["minimum_plan"]))
        ):
            raise OfflinePackError("plan_not_allowed")
        if request.device_class not in rule["device_classes"]:
            raise OfflinePackError("device_not_allowed")
        if rule["certificate_required"] and (
            not request.certificate_active or not request.access_certificate_fingerprint
        ):
            raise OfflinePackError("certificate_required")
        if (
            request.plan in {PlanCode.PRO.value, PlanCode.BUSINESS.value, PlanCode.ENTERPRISE.value}
            and not request.step_up_verified
        ):
            raise OfflinePackError("step_up_required")
        if request.proof_method == "legacy_message_signature" and request.profile not in {
            OfflineProfile.READ_ONLY
        }:
            raise OfflinePackError("proof_too_weak")
        if (
            request.principal_type == "lightning_wallet_principal"
            and not request.stable_auth_domain_verified
        ):
            raise OfflinePackError("proof_too_weak")
        if request.profile is OfflineProfile.PAYREGISTER_CASHIER_SHIFT:
            constraints = request.object_constraints or {}
            required = {
                "workspace_hash",
                "merchant_hash",
                "terminal_hash",
                "cashier_role_hash",
                "shift_hash",
            }
            if not required <= constraints.keys():
                raise OfflinePackError("payregister_constraints_required")
            limits = request.maximum_value_limits or {}
            if int(limits.get("payregister_invoice_create", 0)) <= 0:
                raise OfflinePackError("payregister_value_limit_required")
        if request.requested_scopes >= request.entitlement_scopes and request.requested_scopes:
            raise OfflinePackError("offline_scope_must_be_strict_subset")

    def _check_revocations(self, request: OfflinePackIssueRequest) -> None:
        states = self.revocations.check_offline_pack_targets(
            principal=request.principal_hash,
            device=request.device_key_fingerprint,
            entitlement=request.entitlement_fingerprint,
            access_certificate=request.access_certificate_fingerprint,
        )
        if any(bool(value) for value in states.values()):
            raise OfflinePackError("revoked")

    def _idempotent(self, request: OfflinePackIssueRequest) -> OfflineValidityPack | None:
        if not request.idempotency_key_hash:
            return None
        for row in self.db.execute(
            select(OfflineValidityPack).where(OfflineValidityPack.status == "active")
        ).scalars():
            if (row.policy_snapshot_json or {}).get(
                "_idempotency_key_hash"
            ) == request.idempotency_key_hash:
                if (
                    row.principal_hash != request.principal_hash
                    or row.device_key_fingerprint != request.device_key_fingerprint
                ):
                    raise OfflinePackError("idempotency_conflict")
                return row
        return None

    def _row(self, fingerprint: str) -> OfflineValidityPack:
        row = self.db.execute(
            select(OfflineValidityPack)
            .where(OfflineValidityPack.pack_fingerprint == fingerprint)
            .with_for_update()
        ).scalar_one_or_none()
        if row is None:
            raise OfflinePackError("pack_not_found")
        return row

    def _audit(self, event: str, actor: str, obj: str, reason: str) -> None:
        self.audit.record_event(
            event_type=event, actor_hash=actor, object_hash=obj, metadata={"reason_code": reason}
        )

    def _metric(self, name: str, profile: str, result: str, reason_code: str) -> None:
        if self.metric_emitter is None:
            return
        try:
            self.metric_emitter(
                name,
                {"profile": profile, "result": result, "reason_code": reason_code},
            )
        except Exception:
            # Metrics are operational projections and never block authorization state.
            return


def append_local_event(
    events: list[dict[str, Any]],
    event_type: str,
    safe_details: Mapping[str, Any],
    occurred_at: datetime,
) -> dict[str, Any]:
    previous = events[-1]["event_hash"] if events else "GENESIS"
    payload = {
        "sequence": len(events) + 1,
        "previous_event_hash": previous,
        "event_type": event_type,
        "occurred_at": _iso(occurred_at),
        "safe_details": dict(safe_details),
    }
    payload["event_hash"] = sha256_prefixed(canonical_json(payload))
    events.append(payload)
    return payload


def verify_local_event_chain(events: list[dict[str, Any]]) -> str:
    previous = "GENESIS"
    for sequence, event in enumerate(events, 1):
        if event.get("sequence") != sequence or event.get("previous_event_hash") != previous:
            raise OfflinePackError("event_chain_invalid")
        expected = sha256_prefixed(
            canonical_json({k: v for k, v in event.items() if k != "event_hash"})
        )
        if event.get("event_hash") != expected:
            raise OfflinePackError("event_chain_invalid")
        previous = expected
    return previous


def _utc(value: datetime) -> datetime:
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)


def _iso(value: datetime) -> str:
    return _utc(value).isoformat().replace("+00:00", "Z")
