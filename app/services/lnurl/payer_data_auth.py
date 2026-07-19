"""Replay-safe payerData.auth challenge verification and principal binding."""
from __future__ import annotations

import asyncio
import secrets
from collections.abc import Callable, Mapping
from dataclasses import dataclass, replace
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from typing import Any, Protocol

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec, utils

from app.domain.lnurl.auth import LNURLAuthAction
from app.domain.wallet_auth.proofs import WalletVerificationStrength
from app.services.access.crypto.hashing import hash_canonical_json_prefixed, hmac_sha256_prefixed, sha256_prefixed
from app.services.lnurl.auth_callback_verifier import SECP256K1_ORDER, VerifiedLNURLAuthProof
from app.services.lnurl.payer_data import ParsedPayerAuth, build_payer_data_declaration
from app.services.lnurl.principal_service import (
    AuthDomainPolicy,
    InMemoryLightningPrincipalRepository,
    LightningPrincipalConfig,
    LightningPrincipalService,
)

PAYERDATA_AUTH_PURPOSE = "lnurl_payerdata_auth"
PUBLIC_PAYERDATA_AUTH_ERROR = "Payer authentication failed."


class PayerAuthChallengeStatus(StrEnum):
    UNUSED = "unused"
    CONSUMED = "consumed"
    EXPIRED = "expired"
    REVOKED = "revoked"


class PayerDataAuthError(ValueError):
    def __init__(self, reason_code: str) -> None:
        self.reason_code = reason_code
        self.public_reason = PUBLIC_PAYERDATA_AUTH_ERROR
        super().__init__(reason_code)


class PayerDataSignatureInvalidError(PayerDataAuthError): ...
class PayerDataK1UnknownError(PayerDataAuthError): ...
class PayerDataK1ExpiredError(PayerDataAuthError): ...
class PayerDataK1UsedError(PayerDataAuthError): ...
class PayerDataPaymentMismatchError(PayerDataAuthError): ...
class PayerDataDomainMismatchError(PayerDataAuthError): ...
class PayerDataPolicyDeniedError(PayerDataAuthError): ...
class PayerDataConflictError(PayerDataAuthError): ...


@dataclass(frozen=True, slots=True)
class PayerAuthConfig:
    enabled: bool = True
    default_mode: str = "required"
    ttl_seconds: int = 300
    max_bytes: int = 4096
    store_raw: bool = False
    challenge_pepper: str = "dev-lnurl-payerdata-k1-pepper-change-me"
    linking_key_pepper: str = "dev-lnurl-payerdata-linking-key-pepper-change-me"
    principal_pepper: str = "dev-lnurl-payerdata-principal-pepper-change-me"
    product_pseudonym_pepper: str = "dev-lnurl-payerdata-product-pepper-change-me"
    canonical_domain: str = "auth.bitcoin-bastion.com"
    allow_auto_principal_create: bool = True


@dataclass(frozen=True, slots=True)
class PayerAuthChallenge:
    challenge_id: str
    k1: str
    k1_hash: str
    payment_request_id: str
    callback_hash: str | None
    auth_domain: str
    product_context: str
    plan_code: str
    policy_hash: str | None
    existing_principal_hash: str | None
    purpose: str
    status: PayerAuthChallengeStatus
    issued_at: datetime
    expires_at: datetime
    consumed_at: datetime | None = None
    linking_key_fingerprint: str | None = None
    accepted_callback_fingerprint: str | None = None
    accepted_auth_proof_hash: str | None = None
    principal_hash: str | None = None
    product_pseudonym: str | None = None


@dataclass(frozen=True, slots=True)
class VerifiedPayerAuth:
    verified: bool
    principal_hash: str
    lnurl_key_hash: str
    product_pseudonym: str
    proof_hash: str
    linking_key_fingerprint: str
    auth_domain: str
    verification_strength: str
    method: str
    verified_at: datetime
    idempotent_replay: bool = False


class PayerAuthRepository(Protocol):
    async def create(self, challenge: PayerAuthChallenge) -> PayerAuthChallenge: ...
    async def get_by_k1_hash(self, k1_hash: str) -> PayerAuthChallenge | None: ...
    async def consume(self, *, k1_hash: str, callback_fingerprint: str, auth_proof_hash: str, linking_key_fingerprint: str, principal_hash: str, product_pseudonym: str, now: datetime) -> tuple[PayerAuthChallenge, bool]: ...


class InMemoryPayerAuthRepository:
    def __init__(self) -> None:
        self._records: dict[str, PayerAuthChallenge] = {}
        self._lock = asyncio.Lock()

    async def create(self, challenge: PayerAuthChallenge) -> PayerAuthChallenge:
        async with self._lock:
            if challenge.k1_hash in self._records:
                raise PayerDataConflictError("payerdata_conflict")
            self._records[challenge.k1_hash] = challenge
            return challenge

    async def get_by_k1_hash(self, k1_hash: str) -> PayerAuthChallenge | None:
        async with self._lock:
            return self._records.get(k1_hash)

    async def consume(self, *, k1_hash: str, callback_fingerprint: str, auth_proof_hash: str, linking_key_fingerprint: str, principal_hash: str, product_pseudonym: str, now: datetime) -> tuple[PayerAuthChallenge, bool]:
        async with self._lock:
            record = self._records.get(k1_hash)
            if record is None:
                raise PayerDataK1UnknownError("payerdata_k1_unknown")
            if record.status is PayerAuthChallengeStatus.CONSUMED:
                if record.accepted_callback_fingerprint == callback_fingerprint and record.accepted_auth_proof_hash == auth_proof_hash:
                    return record, True
                raise PayerDataK1UsedError("payerdata_k1_used")
            if record.status is not PayerAuthChallengeStatus.UNUSED:
                raise PayerDataK1UsedError("payerdata_k1_used")
            updated = replace(
                record,
                status=PayerAuthChallengeStatus.CONSUMED,
                consumed_at=now,
                linking_key_fingerprint=linking_key_fingerprint,
                accepted_callback_fingerprint=callback_fingerprint,
                accepted_auth_proof_hash=auth_proof_hash,
                principal_hash=principal_hash,
                product_pseudonym=product_pseudonym,
            )
            self._records[k1_hash] = updated
            return updated, False


class RevocationChecker(Protocol):
    def is_revoked(self, *, target_type: str, target_hash: str) -> bool: ...


class PolicyHook(Protocol):
    def evaluate_payerdata_auth(self, context: Mapping[str, Any]) -> Mapping[str, Any]: ...


AuditEmitter = Callable[[str, Mapping[str, Any]], None]


class LNURLPayerDataAuthService:
    def __init__(
        self,
        *,
        config: PayerAuthConfig | None = None,
        repository: PayerAuthRepository | None = None,
        principal_service: LightningPrincipalService | None = None,
        revocation_checker: RevocationChecker | None = None,
        policy_hook: PolicyHook | None = None,
        audit_emitter: AuditEmitter | None = None,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self.config = config or PayerAuthConfig()
        self.repository = repository or InMemoryPayerAuthRepository()
        self.clock = clock or (lambda: datetime.now(UTC))
        self.revocation_checker = revocation_checker
        self.policy_hook = policy_hook
        self.audit_emitter = audit_emitter
        self.principal_service = principal_service or LightningPrincipalService(
            config=LightningPrincipalConfig(
                lnurl_auth_server_pepper=self.config.linking_key_pepper,
                principal_server_pepper=self.config.principal_pepper,
                product_pseudonym_pepper=self.config.product_pseudonym_pepper,
                domain_policy=AuthDomainPolicy(primary_domain=self.config.canonical_domain, development_domains=frozenset({"auth.bitcoin-bastion.com", "localhost"})),
            ),
            repository=InMemoryLightningPrincipalRepository(),
            clock=self.clock,
        )

    async def create_payer_auth_challenge(self, *, payment_request_id: str, auth_domain: str, product_context: str, plan_code: str, callback_hash: str | None = None, existing_principal_hash: str | None = None, policy_hash: str | None = None, ttl_seconds: int | None = None) -> PayerAuthChallenge:
        if not self.config.enabled:
            raise PayerDataPolicyDeniedError("payerdata_policy_denied")
        raw = secrets.token_bytes(32)
        k1 = raw.hex()
        now = self._now()
        ttl = ttl_seconds or self.config.ttl_seconds
        challenge = PayerAuthChallenge(
            challenge_id=sha256_prefixed(f"{PAYERDATA_AUTH_PURPOSE}:{payment_request_id}:{k1}"),
            k1=k1,
            k1_hash=self._k1_hash(k1),
            payment_request_id=payment_request_id,
            callback_hash=callback_hash,
            auth_domain=auth_domain.lower(),
            product_context=product_context,
            plan_code=plan_code,
            policy_hash=policy_hash,
            existing_principal_hash=existing_principal_hash,
            purpose=PAYERDATA_AUTH_PURPOSE,
            status=PayerAuthChallengeStatus.UNUSED,
            issued_at=now,
            expires_at=now + timedelta(seconds=ttl),
        )
        stored = await self.repository.create(challenge)
        self._audit("lnurl_payerdata_challenge_created", stored, reason_code="created")
        return stored

    def build_payer_data_declaration(self, challenge: PayerAuthChallenge, *, mandatory: bool) -> dict[str, Any]:
        return build_payer_data_declaration(k1=challenge.k1, mandatory=mandatory)

    async def verify_payerdata_auth(self, *, payment_request: Any, parsed_auth: ParsedPayerAuth, expected_domain: str, expected_policy_hash: str | None = None, callback_fingerprint: str | None = None) -> VerifiedPayerAuth:
        now = self._now()
        record = await self.repository.get_by_k1_hash(self._k1_hash(parsed_auth.k1))
        if record is None:
            raise PayerDataK1UnknownError("payerdata_k1_unknown")
        payment_request_id = getattr(payment_request, "request_id", None)
        product_context = getattr(payment_request, "product_code", None)
        plan_code = getattr(payment_request, "plan_code", None)
        if record.payment_request_id != payment_request_id or record.product_context != product_context or record.plan_code != plan_code:
            raise PayerDataPaymentMismatchError("payerdata_payment_mismatch")
        if record.auth_domain != expected_domain.lower():
            raise PayerDataDomainMismatchError("payerdata_domain_mismatch")
        if expected_policy_hash is not None and record.policy_hash is not None and record.policy_hash != expected_policy_hash:
            raise PayerDataPolicyDeniedError("payerdata_policy_denied")
        if record.expires_at <= now:
            raise PayerDataK1ExpiredError("payerdata_k1_expired")
        if record.status is PayerAuthChallengeStatus.CONSUMED:
            if callback_fingerprint and record.accepted_callback_fingerprint == callback_fingerprint and record.accepted_auth_proof_hash == parsed_auth.proof_hash and record.principal_hash and record.product_pseudonym:
                return VerifiedPayerAuth(True, record.principal_hash, self._lnurl_key_hash(parsed_auth.key, record.auth_domain), record.product_pseudonym, parsed_auth.proof_hash, parsed_auth.key_fingerprint, record.auth_domain, "standard", PAYERDATA_AUTH_PURPOSE, record.consumed_at or now, idempotent_replay=True)
            raise PayerDataK1UsedError("payerdata_k1_used")
        self._check_revoked(parsed_auth.key_fingerprint, record)
        self._policy(record, parsed_auth)
        self._verify_signature(parsed_auth)
        proof = VerifiedLNURLAuthProof(
            lnurl_key_hash=self._lnurl_key_hash(parsed_auth.key, record.auth_domain),
            key_fingerprint=parsed_auth.key_fingerprint,
            auth_domain=record.auth_domain,
            lnurl_action=LNURLAuthAction.AUTH,
            bastion_action=PAYERDATA_AUTH_PURPOSE,
            challenge_id=record.challenge_id,
            policy_intent_hash=record.policy_hash or hash_canonical_json_prefixed({"purpose": PAYERDATA_AUTH_PURPOSE}),
            verification_strength=WalletVerificationStrength.STANDARD,
            device_key_fingerprint=None,
            verified_at=now,
        )
        principal_result = self.principal_service.create_from_verified_lnurl_auth(
            proof=proof,
            normalized_linking_public_key=parsed_auth.key,
            proof_fingerprint=parsed_auth.proof_hash,
            policy_hash=record.policy_hash or "sha256:unbound-policy",
            product_id=record.product_context,
            request_context={"payerdata_auth": "verified"},
        )
        principal = principal_result.principal
        product_pseudonym = self._product_pseudonym(principal.lnurl_key_hash, record)
        callback_fingerprint = callback_fingerprint or hash_canonical_json_prefixed({"payment_request_id": payment_request_id, "auth_proof_hash": parsed_auth.proof_hash})
        consumed, replay = await self.repository.consume(
            k1_hash=record.k1_hash,
            callback_fingerprint=callback_fingerprint,
            auth_proof_hash=parsed_auth.proof_hash,
            linking_key_fingerprint=parsed_auth.key_fingerprint,
            principal_hash=principal.principal_hash,
            product_pseudonym=product_pseudonym,
            now=now,
        )
        self._audit("lnurl_payerdata_auth_verified", consumed, reason_code="verified", principal_hash=principal.principal_hash, key_fingerprint=parsed_auth.key_fingerprint)
        return VerifiedPayerAuth(True, principal.principal_hash, principal.lnurl_key_hash, product_pseudonym, parsed_auth.proof_hash, parsed_auth.key_fingerprint, record.auth_domain, "standard", PAYERDATA_AUTH_PURPOSE, now, idempotent_replay=replay)

    def _verify_signature(self, parsed_auth: ParsedPayerAuth) -> None:
        try:
            sig_bytes = bytes.fromhex(parsed_auth.sig)
            _, s_value = utils.decode_dss_signature(sig_bytes)
            if s_value > SECP256K1_ORDER // 2:
                raise PayerDataSignatureInvalidError("payerdata_signature_invalid")
            public_key = ec.EllipticCurvePublicKey.from_encoded_point(ec.SECP256K1(), bytes.fromhex(parsed_auth.key))
            public_key.verify(sig_bytes, bytes.fromhex(parsed_auth.k1), ec.ECDSA(utils.Prehashed(hashes.SHA256())))
        except PayerDataSignatureInvalidError:
            raise
        except (ValueError, InvalidSignature) as exc:
            raise PayerDataSignatureInvalidError("payerdata_signature_invalid") from exc

    def _k1_hash(self, k1: str) -> str:
        return hmac_sha256_prefixed(self.config.challenge_pepper, bytes.fromhex(k1))

    def _lnurl_key_hash(self, key: str, domain: str) -> str:
        return hmac_sha256_prefixed(self.config.linking_key_pepper, f"{domain}:{key}".encode("utf-8"))

    def _product_pseudonym(self, lnurl_key_hash: str, record: PayerAuthChallenge) -> str:
        return hmac_sha256_prefixed(self.config.product_pseudonym_pepper, f"{record.auth_domain}:{lnurl_key_hash}:{record.product_context}".encode("utf-8"))

    def _check_revoked(self, key_fingerprint: str, record: PayerAuthChallenge) -> None:
        if self.revocation_checker is None:
            return
        checks = (("lnurl_linking_key", key_fingerprint), ("payer_auth_challenge", record.k1_hash), ("lnurl_pay_request", record.payment_request_id))
        for target_type, target_hash in checks:
            if self.revocation_checker.is_revoked(target_type=target_type, target_hash=target_hash):
                raise PayerDataPolicyDeniedError("payerdata_principal_revoked")

    def _policy(self, record: PayerAuthChallenge, parsed_auth: ParsedPayerAuth) -> None:
        if self.policy_hook is None:
            return
        decision = self.policy_hook.evaluate_payerdata_auth({"action": "lnurl_payerdata_bind_payment", "product_context": record.product_context, "plan_code": record.plan_code, "auth_domain": record.auth_domain, "linking_key_fingerprint": parsed_auth.key_fingerprint})
        if decision.get("decision") not in {"allow", None} and not decision.get("allowed", False):
            raise PayerDataPolicyDeniedError("payerdata_policy_denied")

    def _audit(self, event: str, challenge: PayerAuthChallenge, *, reason_code: str, principal_hash: str | None = None, key_fingerprint: str | None = None) -> None:
        if self.audit_emitter is None:
            return
        self.audit_emitter(event, {"payment_request_hash": sha256_prefixed(challenge.payment_request_id), "principal_hash": principal_hash, "product_pseudonym": challenge.product_pseudonym, "linking_key_fingerprint": key_fingerprint, "proof_hash": challenge.accepted_auth_proof_hash, "policy_hash": challenge.policy_hash, "reason_code": reason_code, "timestamp": self._now().isoformat()})

    def _now(self) -> datetime:
        value = self.clock()
        if value.tzinfo is None:
            value = value.replace(tzinfo=UTC)
        return value.astimezone(UTC)


__all__ = [
    "PAYERDATA_AUTH_PURPOSE",
    "PayerAuthConfig",
    "PayerAuthChallenge",
    "PayerAuthChallengeStatus",
    "VerifiedPayerAuth",
    "InMemoryPayerAuthRepository",
    "LNURLPayerDataAuthService",
    "PayerDataAuthError",
    "PayerDataSignatureInvalidError",
    "PayerDataK1UnknownError",
    "PayerDataK1ExpiredError",
    "PayerDataK1UsedError",
    "PayerDataPaymentMismatchError",
    "PayerDataDomainMismatchError",
    "PayerDataPolicyDeniedError",
    "PayerDataConflictError",
]
