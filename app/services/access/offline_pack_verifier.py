"""Fail-closed verifier for canonical Offline Validity Pack v1 envelopes."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from hmac import compare_digest
from typing import Any

from app.services.access.crypto.hashing import canonical_json, sha256_prefixed
from app.services.access.crypto.issuer_envelope import verify_serialized_issuer_envelope
from app.services.access.crypto.signatures import verify_offline_validity_pack_signature


@dataclass(frozen=True, slots=True)
class OfflinePackVerificationResult:
    valid: bool
    decision: str
    reason_code: str
    allowed_scopes: tuple[str, ...] = ()
    denied_actions: tuple[str, ...] = ()
    expires_at: datetime | None = None
    reconciliation_required: bool = True
    stale_epochs: tuple[str, ...] = ()
    restrictions: tuple[str, ...] = ()


class OfflinePackVerifier:
    def __init__(
        self,
        issuer_public_key: str,
        *,
        supported_crypto_epochs: frozenset[int] = frozenset({1}),
        supported_policy_epoch: int = 1,
    ):
        self.public_key = issuer_public_key
        self.crypto_epochs = supported_crypto_epochs
        self.policy_epoch = supported_policy_epoch

    def verify(
        self,
        pack: dict[str, Any],
        *,
        device_key_fingerprint: str,
        principal_hash: str,
        entitlement_fingerprint: str,
        cached_revocation_epoch: int,
        certificate_fingerprint: str | None = None,
        revoked_pack_fingerprints: frozenset[str] = frozenset(),
        now: datetime | None = None,
    ) -> OfflinePackVerificationResult:
        if pack.get("type") != "bastion_offline_validity_pack" or pack.get("version") != 1:
            return self._deny("unsupported_version")
        payload = {k: v for k, v in pack.items() if k not in {"pack_fingerprint", "issuer"}}
        expected = sha256_prefixed(canonical_json(payload))
        if not compare_digest(str(pack.get("pack_fingerprint", "")), expected):
            return self._deny("fingerprint_mismatch")
        if expected in revoked_pack_fingerprints:
            return self._deny("revoked")
        issuer = pack.get("issuer", {})
        if issuer.get("signature_suite") != "ed25519":
            return self._deny("unsupported_crypto_epoch")
        signature = issuer.get("classical_signature", {}).get("sig")
        if (
            not isinstance(signature, str)
            or not verify_offline_validity_pack_signature(payload, self.public_key, signature).valid
        ):
            return self._deny("invalid_signature")
        envelope = issuer.get("envelope")
        if not isinstance(envelope, dict) or not verify_serialized_issuer_envelope(
            payload,
            envelope,
            public_key=self.public_key,
            expected_key_id=str(issuer.get("issuer_key_id", "")),
        ):
            return self._deny("invalid_issuer_envelope")
        epochs = pack.get("epochs", {})
        if int(epochs.get("crypto_epoch", -1)) not in self.crypto_epochs:
            return self._deny("unsupported_crypto_epoch")
        if int(epochs.get("policy_epoch", -1)) != self.policy_epoch:
            return self._deny("stale_policy_epoch", ("policy_epoch",))
        if int(epochs.get("revocation_epoch", -1)) < cached_revocation_epoch:
            return self._deny("stale_revocation_epoch", ("revocation_epoch",))
        if pack.get("device_binding", {}).get("device_key_fingerprint") != device_key_fingerprint:
            return self._deny("device_mismatch")
        if pack.get("principal", {}).get("principal_hash") != principal_hash:
            return self._deny("principal_mismatch")
        if pack.get("subscription", {}).get("entitlement_fingerprint") != entitlement_fingerprint:
            return self._deny("entitlement_mismatch")
        cert = pack.get("access_certificate", {})
        if cert.get("required") and cert.get("certificate_fingerprint") != certificate_fingerprint:
            return self._deny("certificate_required")
        expires = _parse(pack.get("validity", {}).get("expires_at"))
        issued = _parse(pack.get("validity", {}).get("issued_at"))
        maximum = int(pack.get("validity", {}).get("maximum_offline_seconds", 0))
        if maximum <= 0 or expires > issued + timedelta(seconds=maximum):
            return self._deny("maximum_offline_duration_exceeded")
        now = _utc(now or datetime.now(UTC))
        if now < _parse(pack.get("validity", {}).get("not_before")) or now >= expires:
            return self._deny("expired")
        policy = pack.get("offline_policy", {})
        return OfflinePackVerificationResult(
            True,
            "allow_offline",
            "verified",
            tuple(policy.get("allowed_scopes", [])),
            tuple(policy.get("denied_actions", [])),
            expires,
            True,
            (),
            ("not_bearer", "device_bound"),
        )

    @staticmethod
    def _deny(reason: str, stale: tuple[str, ...] = ()) -> OfflinePackVerificationResult:
        return OfflinePackVerificationResult(False, "deny", reason, stale_epochs=stale)


def _utc(value: datetime) -> datetime:
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)


def _parse(value: object) -> datetime:
    if not isinstance(value, str):
        return datetime.min.replace(tzinfo=UTC)
    return _utc(datetime.fromisoformat(value.replace("Z", "+00:00")))
