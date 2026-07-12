"""Production wallet challenge lifecycle for Wallet-first Proof-of-Access Auth.

This service creates and consumes short-lived, single-use, origin-bound,
network-bound, device-bound, policy-bound wallet challenges. It does not verify
wallet signatures, create principals, issue sessions, or implement LNURL k1
flows.
"""

from __future__ import annotations

import logging
from collections.abc import Callable, Sequence
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from typing import Any, Protocol
from urllib.parse import urlparse

from app.domain.wallet_auth.actions import WalletAuthAction
from app.domain.wallet_auth.networks import WalletNetwork
from app.domain.wallet_auth.proofs import WalletProofType
from app.domain.wallet_auth.risks import WalletRiskLevel, is_strength_allowed_for_action
from app.services.access.crypto.hashing import (
    constant_time_equal,
    hmac_sha256_prefixed,
    secure_nonce_hex,
    secure_token_urlsafe,
    sha256_prefixed,
)
from app.services.wallet_auth.auth_intent import (
    canonical_intent_json,
    hash_intent,
    render_wallet_message,
    build_human_intent,
    build_wallet_auth_intent,
    requires_human_intent,
)
from app.services.wallet_auth.privacy_commitments import reject_forbidden_wallet_secret_input
from app.services.wallet_auth.repositories.challenges import InMemoryWalletChallengeRepository, WalletChallengeRepository
from app.services.wallet_auth.types import WalletChallengePurpose, WalletChallengeRecord, WalletChallengeResult, WalletChallengeStatus

logger = logging.getLogger(__name__)

WALLET_CHALLENGE_SCHEMA_EPOCH = 1
WALLET_CHALLENGE_POLICY_EPOCH = 1
WALLET_CHALLENGE_CRYPTO_EPOCH = 1
DEFAULT_WALLET_AUTH_DOMAIN = "auth.bitcoin-bastion.com"
DEFAULT_ALLOWED_ORIGINS = ("https://bitcoin-bastion.com", "https://auth.bitcoin-bastion.com", "app://wallet-auth", "cli://wallet-auth")
FORBIDDEN_WALLET_CHALLENGE_SCOPES = frozenset({"api:all", "metrics:all", "admin:all", "*"})
KNOWN_WALLET_CHALLENGE_SCOPES = frozenset({"quotes:read", "metrics:read", "payregister:read", "payregister:refund", "devices:write", "recovery:start", "certificates:bridge"})
DEVICE_FINGERPRINT_MIN_LENGTH = 8

_PURPOSE_ACTION = {
    WalletChallengePurpose.REGISTER: WalletAuthAction.REGISTER,
    WalletChallengePurpose.LOGIN: WalletAuthAction.LOGIN,
    WalletChallengePurpose.LINK_WALLET: WalletAuthAction.LINK,
    WalletChallengePurpose.NEW_DEVICE: WalletAuthAction.DEVICE_ADD,
    WalletChallengePurpose.STEP_UP: WalletAuthAction.STEP_UP,
    WalletChallengePurpose.RECOVERY_START: WalletAuthAction.RECOVERY_START,
    WalletChallengePurpose.OWNERSHIP_PROOF: WalletAuthAction.STEP_UP,
    WalletChallengePurpose.HARDWARE_WALLET_PROOF: WalletAuthAction.STEP_UP,
    WalletChallengePurpose.ACCESS_CERTIFICATE_BRIDGE: WalletAuthAction.STEP_UP,
}
_PURPOSE_TTL_SECONDS = {
    WalletChallengePurpose.REGISTER: 300,
    WalletChallengePurpose.LOGIN: 300,
    WalletChallengePurpose.LINK_WALLET: 300,
    WalletChallengePurpose.NEW_DEVICE: 300,
    WalletChallengePurpose.STEP_UP: 180,
    WalletChallengePurpose.RECOVERY_START: 300,
    WalletChallengePurpose.OWNERSHIP_PROOF: 300,
    WalletChallengePurpose.HARDWARE_WALLET_PROOF: 300,
    WalletChallengePurpose.ACCESS_CERTIFICATE_BRIDGE: 300,
}

AuditEmitter = Callable[[str, dict[str, Any]], None]


class WalletChallengeError(ValueError):
    code = "wallet_challenge_error"

    def __init__(self, code: str | None = None) -> None:
        self.code = code or self.code
        super().__init__(self.code)


class WalletChallengeNotFoundError(WalletChallengeError):
    code = "wallet_challenge_not_found"


class WalletChallengeExpiredError(WalletChallengeError):
    code = "wallet_challenge_expired"


class WalletChallengeConsumedError(WalletChallengeError):
    code = "wallet_challenge_consumed"


class WalletChallengeRevokedError(WalletChallengeError):
    code = "wallet_challenge_revoked"


class WalletChallengeContextMismatchError(WalletChallengeError):
    code = "wallet_challenge_context_mismatch"


class WalletChallengeOriginMismatchError(WalletChallengeContextMismatchError):
    code = "wallet_challenge_origin_mismatch"


class WalletChallengeNetworkMismatchError(WalletChallengeContextMismatchError):
    code = "wallet_challenge_network_mismatch"


class WalletChallengeDeviceMismatchError(WalletChallengeContextMismatchError):
    code = "wallet_challenge_device_mismatch"


class WalletChallengeIntentMismatchError(WalletChallengeContextMismatchError):
    code = "wallet_challenge_intent_mismatch"


class WalletChallengePolicyRejectedError(WalletChallengeError):
    code = "wallet_challenge_policy_rejected"


class WalletChallengeRateLimitedError(WalletChallengeError):
    code = "wallet_challenge_rate_limited"


class WalletChallengeInvalidStateError(WalletChallengeError):
    code = "wallet_challenge_invalid_state"


class WalletChallengeRevocationChecker(Protocol):
    def is_revoked(self, *, target_type: str, target_hash: str) -> bool: ...


class WalletChallengeRateLimiter(Protocol):
    def check(self, *, purpose: str, origin: str, device_key_fingerprint: str, principal_hint: str | None) -> None: ...


class WalletChallengeService:
    def __init__(
        self,
        repository: WalletChallengeRepository | None = None,
        *,
        server_pepper: str = "wallet-auth-test-pepper",
        wallet_auth_domain: str = DEFAULT_WALLET_AUTH_DOMAIN,
        allowed_origins: Sequence[str] = DEFAULT_ALLOWED_ORIGINS,
        max_ttl_seconds: int = 600,
        policy_epoch: int = WALLET_CHALLENGE_POLICY_EPOCH,
        crypto_epoch: int = WALLET_CHALLENGE_CRYPTO_EPOCH,
        audit_emitter: AuditEmitter | None = None,
        revocation_checker: WalletChallengeRevocationChecker | None = None,
        rate_limiter: WalletChallengeRateLimiter | None = None,
        now_factory: Callable[[], datetime] | None = None,
    ) -> None:
        if not server_pepper:
            raise ValueError("server_pepper must not be empty")
        self.repository = repository or InMemoryWalletChallengeRepository()
        self.server_pepper = server_pepper
        self.wallet_auth_domain = wallet_auth_domain
        self.allowed_origins = frozenset(self.normalize_origin(origin) for origin in allowed_origins)
        self.max_ttl_seconds = max_ttl_seconds
        self.policy_epoch = policy_epoch
        self.crypto_epoch = crypto_epoch
        self.audit_emitter = audit_emitter
        self.revocation_checker = revocation_checker
        self.rate_limiter = rate_limiter
        self.now_factory = now_factory or (lambda: datetime.now(UTC))

    async def create_challenge(
        self,
        *,
        purpose: WalletChallengePurpose | str,
        network: WalletNetwork | str,
        proof_type: WalletProofType | str,
        origin: str,
        device_key_fingerprint: str,
        requested_scopes: Sequence[str] = (),
        principal_hint: str | None = None,
        risk_level: WalletRiskLevel | str | None = None,
        policy_hash: str | None = None,
        domain: str | None = None,
    ) -> WalletChallengeResult:
        purpose_value = WalletChallengePurpose(purpose)
        network_value = WalletNetwork(network)
        proof_value = WalletProofType(proof_type)
        normalized_origin = self.normalize_origin(origin)
        domain_value = self._validate_domain(domain or self.wallet_auth_domain)
        self._reject_disallowed_origin(normalized_origin)
        self._validate_device_fingerprint(device_key_fingerprint)
        scopes = self.normalize_requested_scopes(requested_scopes)
        risk = WalletRiskLevel(risk_level) if risk_level is not None else self._default_risk(purpose_value)
        self._reject_policy_incompatible_proof(purpose_value, proof_value, risk)
        if principal_hint is not None and not (principal_hint.startswith("hmac-sha256:") or principal_hint.startswith("sha256:")):
            raise WalletChallengePolicyRejectedError("wallet_challenge_policy_rejected")
        self._check_revocation(proof_value=proof_value, device_key_fingerprint=device_key_fingerprint, principal_hint=principal_hint)
        self._check_rate_limit(purpose=purpose_value.value, origin=normalized_origin, device_key_fingerprint=device_key_fingerprint, principal_hint=principal_hint)
        issued_at = self.now_factory()
        ttl = min(_PURPOSE_TTL_SECONDS[purpose_value], self.max_ttl_seconds)
        expires_at = issued_at + timedelta(seconds=ttl)
        challenge_id = f"wch_{secure_token_urlsafe(24)}"
        nonce = secure_nonce_hex(32)
        action = _PURPOSE_ACTION[purpose_value]
        policy = policy_hash or self._build_policy_hash(
            purpose=purpose_value.value,
            network=network_value.value,
            proof_type=proof_value.value,
            origin=normalized_origin,
            domain=domain_value,
            device_key_fingerprint=device_key_fingerprint,
            requested_scopes=scopes,
            risk_level=risk.value,
        )
        intent = self._build_intent(
            purpose=purpose_value,
            action=action,
            domain=domain_value,
            origin=normalized_origin,
            network=network_value,
            challenge_id=challenge_id,
            nonce=nonce,
            device_key_fingerprint=device_key_fingerprint,
            policy_hash=policy,
            risk_level=risk,
            proof_type=proof_value,
            requested_scopes=scopes,
            issued_at=issued_at,
            expires_at=expires_at,
            principal_hint=principal_hint,
        )
        intent_dict = intent.__dict__
        canonical_intent = canonical_intent_json(intent_dict)
        intent_hash = hash_intent(intent_dict)
        signable_message = render_wallet_message(intent)
        stored_intent = {**intent_dict, "nonce": "<redacted>", "nonce_hash": sha256_prefixed(nonce)}
        challenge_hash = self._challenge_hash(
            challenge_id=challenge_id,
            intent_hash=intent_hash,
            nonce_hash=sha256_prefixed(nonce),
            purpose=purpose_value.value,
            origin=normalized_origin,
            network=network_value.value,
            device_key_fingerprint=device_key_fingerprint,
        )
        record = WalletChallengeRecord(
            challenge_id=challenge_id,
            challenge_hash=challenge_hash,
            nonce_hash=sha256_prefixed(nonce),
            intent_hash=intent_hash,
            purpose=purpose_value.value,
            action=action.value,
            network=network_value.value,
            proof_type=proof_value.value,
            origin=normalized_origin,
            domain=domain_value,
            device_key_fingerprint=device_key_fingerprint,
            policy_hash=policy,
            requested_scopes=scopes,
            risk_level=risk.value,
            principal_hint_hash=principal_hint,
            created_at=issued_at,
            expires_at=expires_at,
            consumed_at=None,
            revoked_at=None,
            failure_reason_code=None,
            status=WalletChallengeStatus.PENDING.value,
            schema_epoch=WALLET_CHALLENGE_SCHEMA_EPOCH,
            policy_epoch=self.policy_epoch,
            crypto_epoch=self.crypto_epoch,
            intent=stored_intent,
            signable_message=signable_message,
        )
        await self.repository.add(record)
        self._emit_audit("wallet_challenge_created", record, reason="created")
        logger.info("wallet_challenge_created", extra={"challenge_hash": challenge_hash, "purpose": purpose_value.value, "network": network_value.value})
        return WalletChallengeResult(
            challenge_id=challenge_id,
            intent_hash=intent_hash,
            canonical_intent=canonical_intent,
            signable_message=signable_message,
            nonce=nonce,
            expires_at=expires_at,
            status=record.status,
            requested_scopes=scopes,
        )

    async def get_challenge(self, challenge_id: str) -> WalletChallengeRecord:
        record = await self.repository.get(challenge_id)
        if record is None:
            raise WalletChallengeNotFoundError()
        return record

    async def validate_pending_challenge(
        self,
        *,
        challenge_id: str,
        expected_purpose: WalletChallengePurpose | str,
        expected_origin: str,
        expected_network: WalletNetwork | str,
        expected_device_key_fingerprint: str,
        expected_domain: str | None = None,
        expected_requested_scopes: Sequence[str] | None = None,
    ) -> WalletChallengeRecord:
        record = await self.get_challenge(challenge_id)
        self._reject_not_pending(record)
        self._reject_expired(record)
        self._validate_context(
            record,
            expected_purpose=WalletChallengePurpose(expected_purpose).value,
            expected_origin=self.normalize_origin(expected_origin),
            expected_network=WalletNetwork(expected_network).value,
            expected_device_key_fingerprint=expected_device_key_fingerprint,
            expected_domain=self._validate_domain(expected_domain or self.wallet_auth_domain),
            expected_requested_scopes=tuple(self.normalize_requested_scopes(expected_requested_scopes or record.requested_scopes)),
        )
        return record

    async def consume_challenge(self, *, challenge_id: str, expected_intent_hash: str) -> WalletChallengeRecord:
        now = self.now_factory()

        def predicate(record: WalletChallengeRecord) -> None:
            if not constant_time_equal(record.intent_hash, expected_intent_hash):
                self._emit_audit("wallet_challenge_context_mismatch", record, reason="wallet_challenge_intent_mismatch")
                raise WalletChallengeIntentMismatchError()

        try:
            consumed = await self.repository.consume_if_pending(challenge_id, now=now, predicate=predicate)
        except KeyError as exc:
            raise WalletChallengeNotFoundError() from exc
        except TimeoutError as exc:
            record = await self.repository.get(challenge_id)
            if record is not None:
                self._emit_audit("wallet_challenge_expired", record, reason="wallet_challenge_expired")
            raise WalletChallengeExpiredError() from exc
        except WalletChallengeIntentMismatchError:
            raise
        except ValueError as exc:
            record = await self.repository.get(challenge_id)
            if record is not None:
                self._emit_audit("wallet_challenge_replay_rejected", record, reason=str(exc))
            if str(exc) == "wallet_challenge_consumed":
                raise WalletChallengeConsumedError() from exc
            if str(exc) == "wallet_challenge_revoked":
                raise WalletChallengeRevokedError() from exc
            if str(exc) == "wallet_challenge_expired":
                raise WalletChallengeExpiredError() from exc
            raise WalletChallengeInvalidStateError("wallet_challenge_invalid_state") from exc
        self._emit_audit("wallet_challenge_consumed", consumed, reason="consumed")
        return consumed

    async def revoke_challenge(self, *, challenge_id: str, reason_code: str) -> WalletChallengeRecord:
        record = await self.get_challenge(challenge_id)
        if record.status != WalletChallengeStatus.PENDING.value:
            raise WalletChallengeInvalidStateError("wallet_challenge_invalid_state")
        revoked = replace(record, status=WalletChallengeStatus.REVOKED.value, revoked_at=self.now_factory(), failure_reason_code=reason_code)
        await self.repository.update(revoked)
        self._emit_audit("wallet_challenge_revoked", revoked, reason=reason_code)
        return revoked

    async def expire_due_challenges(self, *, limit: int = 1000) -> int:
        count = await self.repository.expire_due(now=self.now_factory(), limit=limit)
        return count

    def normalize_origin(self, origin: str) -> str:
        if not origin or not origin.strip():
            raise WalletChallengeOriginMismatchError("wallet_challenge_origin_mismatch")
        parsed = urlparse(origin.strip())
        if parsed.username or parsed.password or parsed.fragment:
            raise WalletChallengeOriginMismatchError("wallet_challenge_origin_mismatch")
        scheme = parsed.scheme.lower()
        if scheme not in {"https", "app", "cli"}:
            raise WalletChallengeOriginMismatchError("wallet_challenge_origin_mismatch")
        if not parsed.netloc:
            raise WalletChallengeOriginMismatchError("wallet_challenge_origin_mismatch")
        host = (parsed.hostname or "").encode("idna").decode("ascii").lower()
        if not host:
            raise WalletChallengeOriginMismatchError("wallet_challenge_origin_mismatch")
        port = f":{parsed.port}" if parsed.port else ""
        if scheme == "https":
            return f"https://{host}{port}"
        return f"{scheme}://{host}{port}"

    def normalize_requested_scopes(self, requested_scopes: Sequence[str]) -> tuple[str, ...]:
        scopes = tuple(sorted({scope.strip() for scope in requested_scopes if scope and scope.strip()}))
        if set(scopes) & FORBIDDEN_WALLET_CHALLENGE_SCOPES:
            raise WalletChallengePolicyRejectedError("wallet_challenge_policy_rejected")
        unknown = [scope for scope in scopes if scope not in KNOWN_WALLET_CHALLENGE_SCOPES]
        if unknown:
            raise WalletChallengePolicyRejectedError("wallet_challenge_policy_rejected")
        for scope in scopes:
            reject_forbidden_wallet_secret_input(scope, "requested_scope")
        return scopes

    def _build_intent(self, **kwargs: Any) -> Any:
        if requires_human_intent(kwargs["action"].value, kwargs["risk_level"].value):
            return build_human_intent(
                domain=kwargs["domain"],
                action=kwargs["action"].value,
                purpose=kwargs["purpose"].value,
                challenge_id=kwargs["challenge_id"],
                nonce=kwargs["nonce"],
                device_key_fingerprint=kwargs["device_key_fingerprint"],
                policy_hash=kwargs["policy_hash"],
                risk_level=kwargs["risk_level"].value,
                requested_scopes=list(kwargs["requested_scopes"]),
                requested_metric_groups=[],
                cannot_access=["api:all", "metrics:all", "admin:all"],
                issued_at=kwargs["issued_at"],
                expires_at=kwargs["expires_at"],
                principal_hash=kwargs["principal_hint"],
                network=kwargs["network"].value,
            )
        return build_wallet_auth_intent(
            domain=kwargs["domain"],
            origin=kwargs["origin"],
            action=kwargs["action"].value,
            purpose=kwargs["purpose"].value,
            network=kwargs["network"].value,
            challenge_id=kwargs["challenge_id"],
            nonce=kwargs["nonce"],
            device_key_fingerprint=kwargs["device_key_fingerprint"],
            policy_hash=kwargs["policy_hash"],
            risk_level=kwargs["risk_level"].value,
            wallet_proof_type=kwargs["proof_type"].value,
            requested_scopes=list(kwargs["requested_scopes"]),
            issued_at=kwargs["issued_at"],
            expires_at=kwargs["expires_at"],
            principal_hint_hash=kwargs["principal_hint"],
        )

    def _build_policy_hash(self, **material: Any) -> str:
        return hmac_sha256_prefixed(self.server_pepper, canonical_intent_json(material))

    def _challenge_hash(self, **material: Any) -> str:
        return hmac_sha256_prefixed(self.server_pepper, canonical_intent_json(material))

    def _default_risk(self, purpose: WalletChallengePurpose) -> WalletRiskLevel:
        if purpose in {WalletChallengePurpose.NEW_DEVICE, WalletChallengePurpose.STEP_UP, WalletChallengePurpose.HARDWARE_WALLET_PROOF, WalletChallengePurpose.ACCESS_CERTIFICATE_BRIDGE}:
            return WalletRiskLevel.HIGH
        return WalletRiskLevel.MEDIUM

    def _reject_policy_incompatible_proof(self, purpose: WalletChallengePurpose, proof_type: WalletProofType, risk: WalletRiskLevel) -> None:
        if proof_type == WalletProofType.LEGACY_MESSAGE_SIGNATURE and (risk == WalletRiskLevel.CRITICAL or purpose in {WalletChallengePurpose.RECOVERY_START, WalletChallengePurpose.OWNERSHIP_PROOF, WalletChallengePurpose.HARDWARE_WALLET_PROOF, WalletChallengePurpose.ACCESS_CERTIFICATE_BRIDGE}):
            raise WalletChallengePolicyRejectedError("wallet_challenge_policy_rejected")
        if risk == WalletRiskLevel.CRITICAL and not is_strength_allowed_for_action("standard", _PURPOSE_ACTION[purpose]):
            raise WalletChallengePolicyRejectedError("wallet_challenge_policy_rejected")

    def _validate_domain(self, domain: str) -> str:
        if not domain or ":" in domain or "/" in domain or "@" in domain:
            raise WalletChallengeOriginMismatchError("wallet_challenge_origin_mismatch")
        normalized = domain.encode("idna").decode("ascii").lower()
        if normalized != self.wallet_auth_domain:
            raise WalletChallengeOriginMismatchError("wallet_challenge_origin_mismatch")
        return normalized

    def _reject_disallowed_origin(self, origin: str) -> None:
        if origin not in self.allowed_origins:
            raise WalletChallengeOriginMismatchError("wallet_challenge_origin_mismatch")

    def _validate_device_fingerprint(self, fingerprint: str) -> None:
        if not fingerprint or len(fingerprint.strip()) < DEVICE_FINGERPRINT_MIN_LENGTH:
            raise WalletChallengeDeviceMismatchError("wallet_challenge_device_mismatch")
        try:
            reject_forbidden_wallet_secret_input(fingerprint, "device_key_fingerprint")
        except ValueError as exc:
            raise WalletChallengeDeviceMismatchError("wallet_challenge_device_mismatch") from exc

    def _reject_not_pending(self, record: WalletChallengeRecord) -> None:
        if record.status == WalletChallengeStatus.CONSUMED.value:
            raise WalletChallengeConsumedError()
        if record.status == WalletChallengeStatus.EXPIRED.value:
            raise WalletChallengeExpiredError()
        if record.status == WalletChallengeStatus.REVOKED.value:
            raise WalletChallengeRevokedError()
        if record.status != WalletChallengeStatus.PENDING.value:
            raise WalletChallengeInvalidStateError("wallet_challenge_invalid_state")

    def _reject_expired(self, record: WalletChallengeRecord) -> None:
        if _aware(record.expires_at) <= _aware(self.now_factory()):
            self._emit_audit("wallet_challenge_expired", record, reason="wallet_challenge_expired")
            raise WalletChallengeExpiredError()

    def _validate_context(
        self,
        record: WalletChallengeRecord,
        *,
        expected_purpose: str,
        expected_origin: str,
        expected_network: str,
        expected_device_key_fingerprint: str,
        expected_domain: str,
        expected_requested_scopes: tuple[str, ...],
    ) -> None:
        if record.purpose != expected_purpose:
            self._emit_audit("wallet_challenge_context_mismatch", record, reason="wallet_challenge_context_mismatch")
            raise WalletChallengeContextMismatchError()
        if record.origin != expected_origin or record.domain != expected_domain:
            self._emit_audit("wallet_challenge_context_mismatch", record, reason="wallet_challenge_origin_mismatch")
            raise WalletChallengeOriginMismatchError()
        if record.network != expected_network:
            self._emit_audit("wallet_challenge_context_mismatch", record, reason="wallet_challenge_network_mismatch")
            raise WalletChallengeNetworkMismatchError()
        if record.device_key_fingerprint != expected_device_key_fingerprint:
            self._emit_audit("wallet_challenge_context_mismatch", record, reason="wallet_challenge_device_mismatch")
            raise WalletChallengeDeviceMismatchError()
        if record.requested_scopes != expected_requested_scopes:
            self._emit_audit("wallet_challenge_context_mismatch", record, reason="wallet_challenge_context_mismatch")
            raise WalletChallengeContextMismatchError()

    def _check_rate_limit(self, *, purpose: str, origin: str, device_key_fingerprint: str, principal_hint: str | None) -> None:
        if self.rate_limiter is None:
            return
        try:
            self.rate_limiter.check(purpose=purpose, origin=origin, device_key_fingerprint=device_key_fingerprint, principal_hint=principal_hint)
        except Exception as exc:
            raise WalletChallengeRateLimitedError("wallet_challenge_rate_limited") from exc

    def _check_revocation(self, *, proof_value: WalletProofType, device_key_fingerprint: str, principal_hint: str | None) -> None:
        if self.revocation_checker is None:
            return
        checks = [("proof_method", proof_value.value), ("wallet_device", device_key_fingerprint)]
        if principal_hint is not None:
            checks.append(("wallet_principal", principal_hint))
        for target_type, target_hash in checks:
            if self.revocation_checker.is_revoked(target_type=target_type, target_hash=target_hash):
                raise WalletChallengeRevokedError("wallet_challenge_revoked")

    def _emit_audit(self, event_type: str, record: WalletChallengeRecord, *, reason: str) -> None:
        if self.audit_emitter is None:
            return
        self.audit_emitter(
            event_type,
            {
                "challenge_hash": record.challenge_hash,
                "intent_hash": record.intent_hash,
                "purpose": record.purpose,
                "network": record.network,
                "proof_type": record.proof_type,
                "origin_hash": sha256_prefixed(record.origin),
                "device_key_fingerprint": record.device_key_fingerprint,
                "policy_hash": record.policy_hash,
                "risk_level": record.risk_level,
                "status": record.status,
                "reason": reason,
            },
        )


def _aware(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)
