"""Deterministic advisory Access Integrity Score 2.0 engine."""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from typing import Any

from app.domain.access.integrity import AccessIntegrityBand as Band
from app.domain.access.integrity import AccessIntegrityContext, AccessIntegrityRecommendation as R
from app.domain.access.integrity import AccessIntegrityScore, AccessIntegritySignal as Signal
from app.domain.access.integrity import AccessIntegritySignalCategory as C
from app.domain.access.integrity import AccessIntegritySignalStatus as S
from app.services.access.crypto.hashing import hash_canonical_json_prefixed
from app.services.lnurl.integrity_signals import collect_lnurl_signals
from app.services.wallet_auth.integrity_signals import collect_wallet_signals

SCORE_VERSION = "2.0"
CATEGORY_WEIGHTS: dict[str, int] = {
    "wallet_proof": 15,
    "lnurl_auth": 10,
    "device": 15,
    "session": 15,
    "entitlement": 10,
    "policy_revocation": 10,
    "recovery": 10,
    "privacy": 5,
    "delegation_business": 5,
    "high_assurance": 5,
}
assert sum(CATEGORY_WEIGHTS.values()) == 100

AuditEmitter = Callable[[str, dict[str, Any]], None]
MetricEmitter = Callable[[str, dict[str, str]], None]


class AccessIntegrityEngine:
    def __init__(
        self,
        *,
        audit_emitter: AuditEmitter | None = None,
        metric_emitter: MetricEmitter | None = None,
    ) -> None:
        self.audit_emitter, self.metric_emitter = audit_emitter, metric_emitter

    def calculate(self, context: AccessIntegrityContext) -> AccessIntegrityScore:
        self._reject_secret_evidence(context.evidence)
        now = context.calculated_at or datetime.now(UTC)
        signals = self.collect_signals(context, now)
        applicable = [s for s in signals if s.status is not S.NOT_APPLICABLE]
        maximum = sum(s.maximum_points for s in applicable) or 100
        weighted = round(sum(max(0.0, s.score_delta) for s in applicable) * 100 / maximum)
        caps = [s.hard_cap for s in signals if s.hard_cap is not None]
        score = max(0, min(100, min([weighted, *caps])))
        band = self.classify_band(score)
        recommendations = self.build_recommendations(signals, band)
        hints = self.build_policy_hints(band)
        fingerprint = hash_canonical_json_prefixed(
            {
                "version": SCORE_VERSION,
                "actor_type": context.actor_type,
                "signals": [
                    (s.signal_id, s.status.value, s.evidence_code, s.score_delta) for s in signals
                ],
                "policy_epoch": context.policy_epoch,
                "revocation_epoch": context.revocation_epoch,
            }
        )
        expiries = [s.expires_at for s in signals if s.expires_at]
        result = AccessIntegrityScore(
            SCORE_VERSION,
            context.principal_hash,
            context.actor_type,
            score,
            band,
            len(applicable) / len(signals) if signals else 0.0,
            now,
            min(expiries) if expiries else now + timedelta(minutes=5),
            tuple(signals),
            tuple(recommendations),
            tuple(hints),
            tuple(s.evidence_code for s in signals if s.hard_cap is not None),
            fingerprint,
            context.crypto_epoch,
            context.policy_epoch,
            context.schema_epoch,
        )
        self._emit(result, context.revocation_epoch)
        return result

    def collect_signals(
        self, context: AccessIntegrityContext, now: datetime | None = None
    ) -> list[Signal]:
        e, observed = context.evidence, now or context.calculated_at or datetime.now(UTC)
        signals = collect_wallet_signals(e, observed, CATEGORY_WEIGHTS["wallet_proof"])
        signals += collect_lnurl_signals(e, observed, CATEGORY_WEIGHTS["lnurl_auth"])
        signals += [
            self._state_signal(
                "device",
                C.DEVICE,
                CATEGORY_WEIGHTS["device"],
                e.get("device_status"),
                observed,
                unsafe={"revoked": ("device_revoked", 20)},
                healthy={"active": "device_active"},
                remedy=R.BIND_TRUSTED_DEVICE,
            )
        ]
        session = self._state_signal(
            "session",
            C.SESSION,
            CATEGORY_WEIGHTS["session"],
            e.get("session_status"),
            observed,
            unsafe={
                "revoked": ("session_revoked", 10),
                "frozen": ("session_frozen", 15),
                "bearer_only": ("bearer_only_protected_access", 25),
                "replay_accepted": ("session_replay_accepted", 15),
            },
            healthy={"active": "pop_session_active"},
            remedy=R.ROTATE_SESSION,
        )
        signals.append(session)
        entitlement_status = (
            "active"
            if e.get("entitlement_active")
            and (not e.get("payment_relevant") or e.get("settlement_verified"))
            else str(e.get("entitlement_status", "unavailable"))
        )
        signals.append(
            self._state_signal(
                "entitlement",
                C.ENTITLEMENT,
                CATEGORY_WEIGHTS["entitlement"],
                entitlement_status,
                observed,
                unsafe={
                    "signature_invalid_accepted": ("invalid_entitlement_signature_accepted", 20),
                    "revoked": ("entitlement_revoked", 20),
                },
                healthy={"active": "entitlement_active"},
                remedy=R.RENEW_SUBSCRIPTION,
            )
        )
        policy_state = (
            "bypass"
            if e.get("policy_bypass")
            else (
                "revoked"
                if e.get("principal_revoked")
                else (
                    "stale"
                    if e.get("revocation_stale")
                    else str(e.get("policy_state", "unavailable"))
                )
            )
        )
        signals.append(
            self._state_signal(
                "policy-revocation",
                C.POLICY,
                CATEGORY_WEIGHTS["policy_revocation"],
                policy_state,
                observed,
                unsafe={
                    "bypass": ("policy_engine_bypass", 10),
                    "revoked": ("principal_revoked", 10),
                },
                healthy={"current": "policy_and_revocation_current"},
                degraded={"stale": ("revocation_registry_stale", 54)},
                remedy=R.SYNCHRONIZE_REVOCATION_REGISTRY,
            )
        )
        recovery_state = (
            "unsafe"
            if e.get("support_only_recovery")
            else str(e.get("recovery_state", "unavailable"))
        )
        signals.append(
            self._state_signal(
                "recovery",
                C.RECOVERY,
                CATEGORY_WEIGHTS["recovery"],
                recovery_state,
                observed,
                unsafe={"unsafe": ("support_only_recovery", 29)},
                healthy={"configured": "recovery_configured"},
                remedy=R.CONFIGURE_RECOVERY_CAPSULE,
            )
        )
        privacy_state = (
            "global_id"
            if e.get("raw_address_global_user_id")
            else str(e.get("privacy_state", "unavailable"))
        )
        signals.append(
            self._state_signal(
                "privacy",
                C.PRIVACY,
                CATEGORY_WEIGHTS["privacy"],
                privacy_state,
                observed,
                unsafe={},
                healthy={"minimized": "privacy_identifiers_minimized"},
                degraded={"global_id": ("raw_address_global_user_id", 54)},
                remedy=R.USE_DEDICATED_AUTH_ADDRESS,
            )
        )
        signals.append(
            self._state_signal(
                "delegation-business",
                C.DELEGATION,
                CATEGORY_WEIGHTS["delegation_business"],
                e.get("delegation_state"),
                observed,
                unsafe={"child_exceeds_parent": ("child_scope_exceeds_parent", 29)},
                healthy={"bounded": "delegation_bounded"},
                remedy=R.REDUCE_CHILD_KEY_SCOPE,
            )
        )
        hardening = (
            "not_applicable"
            if e.get("access_certificate_required") is False
            else str(e.get("hardening_state", "unavailable"))
        )
        signals.append(
            self._state_signal(
                "high-assurance",
                C.ACCESS_CERTIFICATE,
                CATEGORY_WEIGHTS["high_assurance"],
                hardening,
                observed,
                unsafe={"bearer": ("access_certificate_bearer_behavior", 25)},
                healthy={"verified": "high_assurance_controls_verified"},
                remedy=R.REQUIRE_ACCESS_CERTIFICATE,
            )
        )
        if e.get("high_risk_compatibility_allowed"):
            signals.append(
                Signal(
                    "compatibility-high-risk",
                    C.POLICY,
                    S.UNSAFE,
                    0,
                    0,
                    "high_risk_action_allowed_with_compatibility_proof",
                    "Compatibility proof accepted for high-risk action.",
                    R.START_LOCKDOWN,
                    observed,
                    hard_cap=29,
                )
            )
        if e.get("raw_private_material_detected"):
            signals.append(
                Signal(
                    "private-material",
                    C.PRIVACY,
                    S.UNSAFE,
                    0,
                    0,
                    "raw_private_key_or_seed_detected",
                    "Forbidden private material handling was detected.",
                    R.START_LOCKDOWN,
                    observed,
                    hard_cap=0,
                )
            )
        return signals

    @staticmethod
    def _state_signal(
        signal_id: str,
        category: C,
        maximum: int,
        state: object,
        observed: datetime,
        *,
        unsafe: dict[str, tuple[str, int]],
        healthy: dict[str, str],
        remedy: R,
        degraded: dict[str, tuple[str, int]] | None = None,
    ) -> Signal:
        value = str(state or "unavailable")
        if value == "not_applicable":
            return Signal(
                signal_id,
                category,
                S.NOT_APPLICABLE,
                0,
                maximum,
                f"{signal_id}_not_applicable",
                "Signal is not applicable.",
                observed_at=observed,
            )
        if value in healthy:
            return Signal(
                signal_id,
                category,
                S.HEALTHY,
                maximum,
                maximum,
                healthy[value],
                "Verified posture is healthy.",
                observed_at=observed,
                expires_at=observed + timedelta(minutes=5),
            )
        if value in unsafe:
            code, cap = unsafe[value]
            return Signal(
                signal_id,
                category,
                S.UNSAFE,
                0,
                maximum,
                code,
                "Unsafe posture requires remediation.",
                remedy,
                observed,
                hard_cap=cap,
            )
        if degraded and value in degraded:
            code, cap = degraded[value]
            return Signal(
                signal_id,
                category,
                S.DEGRADED,
                maximum * 0.4,
                maximum,
                code,
                "Posture evidence is stale or degraded.",
                remedy,
                observed,
                hard_cap=cap,
            )
        return Signal(
            signal_id,
            category,
            S.UNAVAILABLE,
            0,
            maximum,
            f"{signal_id}_evidence_unavailable",
            "Evidence is unavailable.",
            remedy,
            observed,
        )

    @staticmethod
    def classify_band(score: int) -> Band:
        return (
            Band.EXCELLENT
            if score >= 90
            else Band.STRONG
            if score >= 75
            else Band.GUARDED
            if score >= 55
            else Band.RESTRICTED
            if score >= 30
            else Band.CRITICAL
        )

    @staticmethod
    def build_recommendations(signals: list[Signal], band: Band) -> list[R]:
        values = list(
            dict.fromkeys(
                s.remediation
                for s in signals
                if s.remediation is not R.NONE and s.status not in {S.HEALTHY, S.NOT_APPLICABLE}
            )
        )
        if band is Band.CRITICAL:
            values.append(R.START_LOCKDOWN)
        elif band is Band.RESTRICTED:
            values.append(R.ENTER_READ_ONLY)
        return list(dict.fromkeys(values))

    @staticmethod
    def build_policy_hints(band: Band) -> list[str]:
        return {
            Band.EXCELLENT: [],
            Band.STRONG: ["native_step_up_for_high_risk"],
            Band.GUARDED: ["step_up_recommended", "shorten_session_ttl"],
            Band.RESTRICTED: ["read_only_recommended", "deny_new_child_keys"],
            Band.CRITICAL: ["lockdown_recommended", "recovery_only"],
        }[band]

    @staticmethod
    def verify_evidence_freshness(
        result: AccessIntegrityScore, at_time: datetime | None = None
    ) -> bool:
        return result.evidence_fresh_until is not None and result.evidence_fresh_until >= (
            at_time or datetime.now(UTC)
        )

    def _emit(self, result: AccessIntegrityScore, revocation_epoch: int) -> None:
        if self.audit_emitter:
            self.audit_emitter(
                "access_integrity_calculated",
                {
                    "principal_hash": result.principal_hash,
                    "score": result.score,
                    "band": result.band.value,
                    "score_version": result.version,
                    "evidence_fingerprint": result.evidence_fingerprint,
                    "critical_reason_codes": list(result.critical_flags),
                    "policy_epoch": result.policy_epoch,
                    "revocation_epoch": revocation_epoch,
                    "calculated_at": result.calculated_at.isoformat(),
                },
            )
            if result.critical_flags:
                self.audit_emitter(
                    "access_integrity_critical_signal",
                    {
                        "principal_hash": result.principal_hash,
                        "band": result.band.value,
                        "score_version": result.version,
                        "evidence_fingerprint": result.evidence_fingerprint,
                        "critical_reason_codes": list(result.critical_flags),
                        "policy_epoch": result.policy_epoch,
                    },
                )
            recommendation_event = {
                Band.GUARDED: "access_integrity_step_up_recommended",
                Band.RESTRICTED: "access_integrity_read_only_recommended",
                Band.CRITICAL: "access_integrity_lockdown_recommended",
            }.get(result.band)
            if recommendation_event:
                self.audit_emitter(
                    recommendation_event,
                    {
                        "principal_hash": result.principal_hash,
                        "band": result.band.value,
                        "score_version": result.version,
                        "evidence_fingerprint": result.evidence_fingerprint,
                        "policy_epoch": result.policy_epoch,
                    },
                )
        if self.metric_emitter:
            self.metric_emitter(
                "bastion_access_integrity_calculations_total",
                {
                    "band": result.band.value,
                    "actor_type": result.actor_type,
                    "score_version": result.version,
                },
            )
            self.metric_emitter(
                "bastion_access_integrity_band_total",
                {
                    "band": result.band.value,
                    "actor_type": result.actor_type,
                    "score_version": result.version,
                },
            )
            for reason_code in result.critical_flags:
                self.metric_emitter(
                    "bastion_access_integrity_critical_signals_total",
                    {
                        "band": result.band.value,
                        "reason_code": reason_code,
                        "score_version": result.version,
                    },
                )
            if "step_up_recommended" in result.policy_hints:
                self.metric_emitter(
                    "bastion_access_integrity_step_up_hints_total",
                    {"band": result.band.value, "score_version": result.version},
                )
            if "lockdown_recommended" in result.policy_hints:
                self.metric_emitter(
                    "bastion_access_integrity_lockdown_hints_total",
                    {"band": result.band.value, "score_version": result.version},
                )

    @staticmethod
    def _reject_secret_evidence(evidence: dict[str, Any]) -> None:
        forbidden = (
            "seed",
            "private_key",
            "xprv",
            "mnemonic",
            "raw_k1",
            "raw_signature",
            "session_token",
            "linking_key",
            "wallet_address",
            "preimage",
            "bolt11",
        )
        if any(any(part in str(key).lower() for part in forbidden) for key in evidence):
            raise ValueError("forbidden_integrity_evidence")


class AccessIntegrityCache:
    """Short-lived safe result cache keyed only by pseudonym and evidence epochs."""

    INVALIDATING_EVENTS = frozenset(
        {
            "wallet_proof_verified",
            "wallet_proof_revoked",
            "lnurl_auth_success",
            "lnurl_auth_failed",
            "lnurl_k1_replay_detected",
            "wallet_device_added",
            "wallet_device_revoked",
            "wallet_session_created",
            "wallet_session_revoked",
            "wallet_session_frozen",
            "entitlement_issued",
            "entitlement_renewed",
            "entitlement_downgraded",
            "entitlement_revoked",
            "child_api_key_created",
            "child_api_key_revoked",
            "recovery_configuration_changed",
            "lockdown_started",
            "lockdown_released",
            "policy_epoch_changed",
            "revocation_epoch_changed",
            "access_certificate_issued",
            "access_certificate_revoked",
            "offline_validity_pack_issued",
            "offline_validity_pack_revoked",
        }
    )

    def __init__(self, *, audit_emitter: AuditEmitter | None = None) -> None:
        self._values: dict[tuple[object, ...], AccessIntegrityScore] = {}
        self.audit_emitter = audit_emitter

    @staticmethod
    def key(
        principal_hash: str,
        *,
        policy_epoch: int,
        revocation_epoch: int,
        entitlement_version: int = 0,
        device_version: int = 0,
        session_version: int = 0,
    ) -> tuple[object, ...]:
        return (
            principal_hash,
            policy_epoch,
            revocation_epoch,
            entitlement_version,
            device_version,
            session_version,
        )

    def get(self, key: tuple[object, ...]) -> AccessIntegrityScore | None:
        return self._values.get(key)

    def put(self, key: tuple[object, ...], result: AccessIntegrityScore) -> None:
        self._values[key] = result

    def invalidate(self, principal_hash: str, event_type: str) -> bool:
        if event_type not in self.INVALIDATING_EVENTS:
            return False
        keys = [key for key in self._values if key[0] == principal_hash]
        for key in keys:
            self._values.pop(key, None)
        if keys and self.audit_emitter:
            self.audit_emitter(
                "access_integrity_cache_invalidated",
                {
                    "principal_hash": principal_hash,
                    "reason_code": event_type,
                    "invalidated_entries": len(keys),
                    "score_version": SCORE_VERSION,
                },
            )
        return bool(keys)
