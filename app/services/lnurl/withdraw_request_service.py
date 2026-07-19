"""LNURL-withdraw request creation service.

This service only creates short-lived, single-use, policy-authorized
LNURL-withdraw requests. It never pays invoices, verifies callback invoices,
settles refunds, or treats k1 as sufficient authorization.
"""
from __future__ import annotations

import re
import secrets
import threading
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any, Protocol
from urllib.parse import urlparse

from app.services.access.crypto.hashing import hash_canonical_json_prefixed, hmac_sha256_prefixed, safe_hash_for_log, sha256_prefixed
from app.services.lnurl.encoding import encode_lnurl
from app.services.lnurl.k1_registry import InMemoryK1Repository, LNURLK1Config, LNURLK1Purpose, LNURLK1RegistryService, LNURLK1Status
from app.services.lnurl.repositories.withdraw_requests import (
    InMemoryLNURLWithdrawRequestRepository,
    LNURLWithdrawRequestRecord,
    LNURLWithdrawRequestRepository,
    LNURLWithdrawRequestStatus,
    TERMINAL_WITHDRAW_REQUEST_STATES,
    transition_withdraw_request,
)
from app.services.lnurl.url_safety import LNURLURLPolicy, validate_lnurl_url

_WITHDRAW_CALLBACK_PATH_PREFIX = "/v1/lnurl/withdraw/callback/"
_DESCRIPTION_CONTROL_RE = re.compile(r"[\x00-\x1f\x7f]")
_MAX_DESCRIPTION_CHARS = 120
_FORBIDDEN_DESCRIPTION_TERMS = ("seed", "private key", "private_key", "session token", "session_token", "preimage", "xprv", "mnemonic", "access pass", "access_pass")


class LNURLWithdrawPurpose(StrEnum):
    SUBSCRIPTION_REFUND = "subscription_refund"
    PAYREGISTER_REFUND = "payregister_refund"
    CASHBACK = "cashback"
    REWARD = "reward"
    BUG_BOUNTY = "bug_bounty"
    PARTNER_PAYOUT = "partner_payout"
    MERCHANT_SETTLEMENT_HELPER = "merchant_settlement_helper"
    TESTNET_FAUCET = "testnet_faucet"
    SIGNET_FAUCET = "signet_faucet"
    OTHER_CONTROLLED_PAYOUT = "other_controlled_payout"


class LNURLWithdrawPolicyDecisionValue(StrEnum):
    ALLOW = "allow"
    DENY = "deny"
    STEP_UP_REQUIRED = "step_up_required"
    QUOTA_EXCEEDED = "quota_exceeded"
    RECOVERY_REQUIRED = "recovery_required"
    ONLINE_CHECK_REQUIRED = "online_check_required"
    REVOKED = "revoked"
    EXPIRED = "expired"


class LNURLWithdrawRequestError(ValueError):
    reason_code = "lnurl_withdraw_configuration_error"


class LNURLWithdrawNotAuthorizedError(LNURLWithdrawRequestError):
    reason_code = "lnurl_withdraw_not_authorized"


class LNURLWithdrawStepUpRequiredError(LNURLWithdrawRequestError):
    reason_code = "lnurl_withdraw_step_up_required"


class LNURLWithdrawInvalidAmountError(LNURLWithdrawRequestError):
    reason_code = "lnurl_withdraw_invalid_amount"


class LNURLWithdrawLimitExceededError(LNURLWithdrawRequestError):
    reason_code = "lnurl_withdraw_limit_exceeded"


class LNURLWithdrawSourceRequiredError(LNURLWithdrawRequestError):
    reason_code = "lnurl_withdraw_source_required"


class LNURLWithdrawSourceAlreadyConsumedError(LNURLWithdrawRequestError):
    reason_code = "lnurl_withdraw_source_already_consumed"


class LNURLWithdrawInvalidStateError(LNURLWithdrawRequestError):
    reason_code = "lnurl_withdraw_invalid_state"


class LNURLWithdrawExpiredError(LNURLWithdrawRequestError):
    reason_code = "lnurl_withdraw_expired"


class LNURLWithdrawRevokedError(LNURLWithdrawRequestError):
    reason_code = "lnurl_withdraw_revoked"


class LNURLWithdrawIdempotencyConflictError(LNURLWithdrawRequestError):
    reason_code = "lnurl_withdraw_idempotency_conflict"


@dataclass(frozen=True, slots=True)
class PrincipalContext:
    principal_type: str
    principal_reference_hash: str
    device_reference_hash: str
    session_reference_hash: str
    authenticated: bool = True
    principal_active: bool = True
    device_active: bool = True
    session_active: bool = True
    pop_session_active: bool = True
    auth_method: str = "wallet_principal_pop"
    business_role: str | None = None
    workspace_hash: str | None = None


@dataclass(frozen=True, slots=True)
class PolicyDecision:
    decision: LNURLWithdrawPolicyDecisionValue | str
    policy_hash: str
    decision_reference: str
    approved_amount_msat: int
    reason_code: str = "allow"
    required_step_up: str | None = None


@dataclass(frozen=True, slots=True)
class WithdrawPurposePolicy:
    purpose: LNURLWithdrawPurpose
    default_risk_level: str
    authentication_required: bool
    wallet_step_up_required: bool
    business_role_required: bool
    cooldown_applies: bool
    max_amount_msat: int
    allowed_networks: frozenset[str]
    audit_event_type: str
    source_required: bool = True


@dataclass(frozen=True, slots=True)
class LNURLWithdrawRequestConfig:
    enabled: bool = True
    callback_base_url: str = "https://bitcoin-bastion.com"
    default_ttl_seconds: int = 300
    max_ttl_seconds: int = 900
    global_max_msat: int = 10_000_000
    require_policy: bool = True
    allow_test_faucet: bool = False
    onion_enabled: bool = False
    server_pepper: str = "dev-lnurl-withdraw-pepper-change-me"
    network: str = "bitcoin-mainnet"


@dataclass(frozen=True, slots=True)
class LNURLWithdrawRequestResult:
    withdraw_request_id: str
    status: str
    tag: str
    lnurl: str
    callback_url: str
    expires_at: datetime
    min_withdrawable_msat: int
    max_withdrawable_msat: int
    default_description: str
    purpose: str
    policy_decision_reference: str

    def withdraw_request_payload(self, k1: str) -> dict[str, Any]:
        return {
            "tag": self.tag,
            "callback": self.callback_url,
            "k1": k1,
            "defaultDescription": self.default_description,
            "minWithdrawable": self.min_withdrawable_msat,
            "maxWithdrawable": self.max_withdrawable_msat,
        }


class LNURLWithdrawAuditSink(Protocol):
    def emit(self, event_type: str, payload: dict[str, Any]) -> str: ...


class InMemoryLNURLWithdrawAuditSink:
    def __init__(self) -> None:
        self.events: list[dict[str, Any]] = []

    def emit(self, event_type: str, payload: dict[str, Any]) -> str:
        safe_payload = {k: v for k, v in payload.items() if "k1" not in k and "lnurl" not in k and "token" not in k and "secret" not in k}
        event_hash = hash_canonical_json_prefixed({"event_type": event_type, **safe_payload, "index": len(self.events)})
        self.events.append({"event_type": event_type, "event_hash": event_hash, **safe_payload})
        return event_hash


class LNURLWithdrawRevocationChecker(Protocol):
    def is_revoked(self, target_type: str, target_hash: str) -> bool: ...


class NoopLNURLWithdrawRevocationChecker:
    def is_revoked(self, target_type: str, target_hash: str) -> bool:
        return False


class LNURLWithdrawRequestService:
    def __init__(
        self,
        *,
        repository: LNURLWithdrawRequestRepository | None = None,
        k1_registry: LNURLK1RegistryService | None = None,
        audit_sink: LNURLWithdrawAuditSink | None = None,
        revocation_checker: LNURLWithdrawRevocationChecker | None = None,
        config: LNURLWithdrawRequestConfig | None = None,
        purpose_policies: dict[LNURLWithdrawPurpose, WithdrawPurposePolicy] | None = None,
    ) -> None:
        self.config = config or LNURLWithdrawRequestConfig()
        self.repository = repository or InMemoryLNURLWithdrawRequestRepository()
        self.audit_sink = audit_sink or InMemoryLNURLWithdrawAuditSink()
        self.revocation_checker = revocation_checker or NoopLNURLWithdrawRevocationChecker()
        self.k1_registry = k1_registry or LNURLK1RegistryService(
            config=LNURLK1Config(server_pepper=self.config.server_pepper, withdraw_ttl_seconds=min(self.config.default_ttl_seconds, self.config.max_ttl_seconds), allow_test_pepper=True),
            repository=InMemoryK1Repository(),
        )
        self.purpose_policies = purpose_policies or _default_purpose_policies()
        self._creation_lock = threading.RLock()

    async def create_request(
        self,
        *,
        principal_context: PrincipalContext,
        purpose: LNURLWithdrawPurpose | str,
        approved_amount_msat: int,
        min_withdrawable_msat: int | None = None,
        max_withdrawable_msat: int | None = None,
        source_reference: str | None = None,
        description: str | None = None,
        expires_in_seconds: int | None = None,
        policy_decision: PolicyDecision | None = None,
        idempotency_key: str | None = None,
        client_callback_url: str | None = None,
        client_k1: str | None = None,
    ) -> LNURLWithdrawRequestResult:
        if not self.config.enabled:
            raise LNURLWithdrawRequestError("lnurl_withdraw_disabled")
        purpose_enum = self._purpose(purpose)
        purpose_policy = self.purpose_policies.get(purpose_enum)
        if purpose_policy is None:
            raise LNURLWithdrawNotAuthorizedError("unknown_purpose")
        if self.config.network not in purpose_policy.allowed_networks:
            raise LNURLWithdrawNotAuthorizedError("purpose_not_allowed_on_network")
        if purpose_enum in {LNURLWithdrawPurpose.TESTNET_FAUCET, LNURLWithdrawPurpose.SIGNET_FAUCET}:
            if self.config.network == "bitcoin-mainnet" or not self.config.allow_test_faucet:
                raise LNURLWithdrawNotAuthorizedError("test_faucet_denied")
        self._validate_auth(principal_context, purpose_policy)
        self._validate_policy(policy_decision, approved_amount_msat)
        source_hash = safe_hash_for_log(source_reference) if source_reference else None
        if purpose_policy.source_required and source_hash is None:
            raise LNURLWithdrawSourceRequiredError("source_reference_required")
        min_msat, max_msat = self._amount_bounds(
            approved_amount_msat=approved_amount_msat,
            min_withdrawable_msat=min_withdrawable_msat,
            max_withdrawable_msat=max_withdrawable_msat,
            purpose_policy=purpose_policy,
            policy_decision=policy_decision,
        )
        ttl = self._ttl(expires_in_seconds)
        desc = _sanitize_description(description or _default_description(purpose_enum))
        callback_url = self._build_callback_url(_new_request_reference())
        if client_callback_url and client_callback_url != callback_url:
            # Client-supplied callback URL is ignored; never used to construct the response.
            self.audit_sink.emit("lnurl_withdraw_client_callback_ignored", {"purpose": purpose_enum.value, "client_callback_url_hash": safe_hash_for_log(client_callback_url)})
        if client_k1 is not None:
            raise LNURLWithdrawNotAuthorizedError("client_supplied_k1_denied")
        payload_hash = hash_canonical_json_prefixed({"purpose": purpose_enum.value, "amount": approved_amount_msat, "min": min_msat, "max": max_msat, "source": source_hash, "principal": principal_context.principal_reference_hash, "network": self.config.network})
        idem_basis = idempotency_key or f"{purpose_enum.value}:{source_hash}:{principal_context.principal_reference_hash}"
        idem_hash = hmac_sha256_prefixed(self.config.server_pepper, idem_basis)
        with self._creation_lock:
            existing = self.repository.get_by_idempotency_key_hash(idem_hash)
            if existing is not None:
                if existing.payload_hash != payload_hash:
                    raise LNURLWithdrawIdempotencyConflictError("idempotency_payload_conflict")
                if existing.status in TERMINAL_WITHDRAW_REQUEST_STATES:
                    raise LNURLWithdrawInvalidStateError("idempotent_request_terminal")
                return self._result_from_record(existing)
            if source_hash is not None and self.repository.active_for_source(source_hash) is not None:
                raise LNURLWithdrawSourceAlreadyConsumedError("source_already_has_active_withdraw_request")
            return self._issue_new_request(
                purpose_enum=purpose_enum,
                principal_context=principal_context,
                policy_decision=policy_decision,
                source_hash=source_hash,
                min_msat=min_msat,
                max_msat=max_msat,
                desc=desc,
                callback_url=callback_url,
                payload_hash=payload_hash,
                idem_hash=idem_hash,
                ttl=ttl,
                purpose_policy=purpose_policy,
            )

    def _issue_new_request(self, *, purpose_enum: LNURLWithdrawPurpose, principal_context: PrincipalContext, policy_decision: PolicyDecision | None, source_hash: str | None, min_msat: int, max_msat: int, desc: str, callback_url: str, payload_hash: str, idem_hash: str, ttl: int, purpose_policy: WithdrawPurposePolicy) -> LNURLWithdrawRequestResult:
        reference = callback_url.rsplit("/", 1)[-1]
        request_hash = sha256_prefixed(reference)
        issued_k1 = self.k1_registry.issue_k1(
            LNURLK1Purpose.LNURL_WITHDRAW,
            self._callback_host(),
            lnurl_action="lnurl_withdraw_callback",
            internal_action=purpose_enum.value,
            policy_hash=policy_decision.policy_hash if policy_decision else None,
            principal_hash=principal_context.principal_reference_hash,
            device_key_fingerprint=principal_context.device_reference_hash,
            session_hash=principal_context.session_reference_hash,
            withdraw_request_hash=request_hash,
            metadata_hash=payload_hash,
            ttl_seconds=ttl,
        )
        record = LNURLWithdrawRequestRecord(
            opaque_request_id=reference,
            withdraw_request_reference_hash=request_hash,
            purpose=purpose_enum.value,
            status=LNURLWithdrawRequestStatus.POLICY_APPROVED,
            principal_type=principal_context.principal_type,
            principal_reference_hash=principal_context.principal_reference_hash,
            device_reference_hash=principal_context.device_reference_hash,
            session_reference_hash=principal_context.session_reference_hash,
            source_reference_hash=source_hash,
            policy_decision_reference=policy_decision.decision_reference if policy_decision else "policy:not-required",
            policy_hash=policy_decision.policy_hash if policy_decision else "sha256:test-faucet-policy",
            k1_registry_id=issued_k1.registry_id,
            k1_fingerprint=issued_k1.k1_fingerprint,
            callback_url_hash=safe_hash_for_log(callback_url),
            min_withdrawable_msat=min_msat,
            max_withdrawable_msat=max_msat,
            default_description=desc,
            network=self.config.network,
            risk_level=purpose_policy.default_risk_level,
            idempotency_key_hash=idem_hash,
            payload_hash=payload_hash,
            created_at=datetime.now(UTC),
            expires_at=issued_k1.expires_at,
            issued_at=None,
            metadata_json={"k1_status": LNURLK1Status.ACTIVE.value, "k1_fingerprint": issued_k1.k1_fingerprint},
        )
        issued = transition_withdraw_request(record, LNURLWithdrawRequestStatus.LNURL_ISSUED, now=datetime.now(UTC))
        saved = self.repository.save(issued)
        self.audit_sink.emit("lnurl_withdraw_request_created", self._audit_payload(saved, decision="allow"))
        self.audit_sink.emit("lnurl_withdraw_request_issued", self._audit_payload(saved, decision="allow"))
        return self._result_from_record(saved, k1=issued_k1.k1)

    def get_request_for_callback_reference(self, opaque_request_reference: str) -> LNURLWithdrawRequestRecord | None:
        return self.repository.get_by_reference_hash(sha256_prefixed(opaque_request_reference))

    def validate_request_usable_for_callback(self, opaque_request_reference: str) -> LNURLWithdrawRequestRecord:
        record = self.get_request_for_callback_reference(opaque_request_reference)
        if record is None:
            raise LNURLWithdrawInvalidStateError("lnurl_withdraw_unknown")
        if record.status == LNURLWithdrawRequestStatus.REVOKED:
            raise LNURLWithdrawRevokedError("lnurl_withdraw_revoked")
        if record.status == LNURLWithdrawRequestStatus.EXPIRED or record.expires_at <= datetime.now(UTC):
            raise LNURLWithdrawExpiredError("lnurl_withdraw_expired")
        if record.status != LNURLWithdrawRequestStatus.LNURL_ISSUED:
            raise LNURLWithdrawInvalidStateError("lnurl_withdraw_invalid_state")
        return record

    def revoke_request(self, request_id: str, reason: str, actor_context: str | None = None) -> LNURLWithdrawRequestRecord:
        record = self._record(request_id)
        if record.status == LNURLWithdrawRequestStatus.REVOKED:
            return record
        if record.status in TERMINAL_WITHDRAW_REQUEST_STATES:
            return record
        updated = transition_withdraw_request(record, LNURLWithdrawRequestStatus.REVOKED, now=datetime.now(UTC))
        self.k1_registry.revoke_k1(registry_id=record.k1_registry_id, reason_code=reason, actor_hash=safe_hash_for_log(actor_context or "system"))
        saved = self.repository.update(updated)
        self.audit_sink.emit("lnurl_withdraw_request_revoked", self._audit_payload(saved, decision="revoked", reason=reason))
        return saved

    def cancel_request(self, request_id: str, reason: str, actor_context: str | None = None) -> LNURLWithdrawRequestRecord:
        record = self._record(request_id)
        if record.status == LNURLWithdrawRequestStatus.CANCELLED:
            return record
        if record.status in TERMINAL_WITHDRAW_REQUEST_STATES:
            return record
        target = LNURLWithdrawRequestStatus.CANCELLED
        if record.status == LNURLWithdrawRequestStatus.LNURL_ISSUED:
            # Prompt 44 state machine permits revoke/expire after issuance; use revoke for issued requests.
            return self.revoke_request(request_id, reason, actor_context)
        updated = transition_withdraw_request(record, target, now=datetime.now(UTC))
        self.k1_registry.revoke_k1(registry_id=record.k1_registry_id, reason_code=reason, actor_hash=safe_hash_for_log(actor_context or "system"))
        saved = self.repository.update(updated)
        self.audit_sink.emit("lnurl_withdraw_request_cancelled", self._audit_payload(saved, decision="cancelled", reason=reason))
        return saved

    def expire_request(self, request_id: str) -> LNURLWithdrawRequestRecord:
        record = self._record(request_id)
        if record.status == LNURLWithdrawRequestStatus.EXPIRED:
            return record
        if record.status != LNURLWithdrawRequestStatus.LNURL_ISSUED:
            raise LNURLWithdrawInvalidStateError("lnurl_withdraw_invalid_state")
        updated = transition_withdraw_request(record, LNURLWithdrawRequestStatus.EXPIRED, now=datetime.now(UTC))
        self.k1_registry.revoke_k1(registry_id=record.k1_registry_id, reason_code="expired")
        saved = self.repository.update(updated)
        self.audit_sink.emit("lnurl_withdraw_request_expired", self._audit_payload(saved, decision="expired"))
        return saved

    def _record(self, request_id: str) -> LNURLWithdrawRequestRecord:
        record = self.repository.get_by_request_id(request_id)
        if record is None:
            raise LNURLWithdrawInvalidStateError("lnurl_withdraw_unknown")
        return record

    def _purpose(self, purpose: LNURLWithdrawPurpose | str) -> LNURLWithdrawPurpose:
        try:
            return purpose if isinstance(purpose, LNURLWithdrawPurpose) else LNURLWithdrawPurpose(str(purpose))
        except ValueError as exc:
            raise LNURLWithdrawNotAuthorizedError("unknown_purpose") from exc

    def _validate_auth(self, principal: PrincipalContext, purpose_policy: WithdrawPurposePolicy) -> None:
        if purpose_policy.authentication_required and not (principal.authenticated and principal.pop_session_active):
            raise LNURLWithdrawNotAuthorizedError("authenticated_pop_session_required")
        if not principal.principal_active or self.revocation_checker.is_revoked("lnurl_withdraw_principal", principal.principal_reference_hash):
            raise LNURLWithdrawNotAuthorizedError("principal_revoked")
        if not principal.device_active or self.revocation_checker.is_revoked("lnurl_withdraw_device", principal.device_reference_hash):
            raise LNURLWithdrawNotAuthorizedError("device_revoked")
        if not principal.session_active or self.revocation_checker.is_revoked("lnurl_withdraw_session", principal.session_reference_hash):
            raise LNURLWithdrawNotAuthorizedError("session_expired")

    def _validate_policy(self, policy: PolicyDecision | None, approved_amount_msat: int) -> None:
        if self.config.require_policy and policy is None:
            self.audit_sink.emit("lnurl_withdraw_policy_denied", {"decision": "missing_policy"})
            raise LNURLWithdrawNotAuthorizedError("policy_decision_required")
        if policy is None:
            return
        decision = LNURLWithdrawPolicyDecisionValue(str(policy.decision))
        if decision == LNURLWithdrawPolicyDecisionValue.STEP_UP_REQUIRED:
            self.audit_sink.emit("lnurl_withdraw_step_up_required", {"decision": decision.value, "required_step_up": policy.required_step_up or "wallet_step_up"})
            raise LNURLWithdrawStepUpRequiredError(policy.required_step_up or "wallet_step_up_required")
        if decision != LNURLWithdrawPolicyDecisionValue.ALLOW:
            self.audit_sink.emit("lnurl_withdraw_policy_denied", {"decision": decision.value, "reason_code": policy.reason_code})
            raise LNURLWithdrawNotAuthorizedError(policy.reason_code)
        if policy.approved_amount_msat < approved_amount_msat:
            raise LNURLWithdrawLimitExceededError("amount_exceeds_policy_approval")

    def _amount_bounds(self, *, approved_amount_msat: int, min_withdrawable_msat: int | None, max_withdrawable_msat: int | None, purpose_policy: WithdrawPurposePolicy, policy_decision: PolicyDecision | None) -> tuple[int, int]:
        if not isinstance(approved_amount_msat, int) or approved_amount_msat <= 0:
            raise LNURLWithdrawInvalidAmountError("amount_must_be_positive_msat")
        if approved_amount_msat > self.config.global_max_msat:
            raise LNURLWithdrawLimitExceededError("amount_exceeds_global_limit")
        if approved_amount_msat > purpose_policy.max_amount_msat:
            raise LNURLWithdrawLimitExceededError("amount_exceeds_purpose_limit")
        if policy_decision and approved_amount_msat > policy_decision.approved_amount_msat:
            raise LNURLWithdrawLimitExceededError("amount_exceeds_policy_limit")
        min_msat = min_withdrawable_msat if min_withdrawable_msat is not None else approved_amount_msat
        max_msat = max_withdrawable_msat if max_withdrawable_msat is not None else approved_amount_msat
        if min_msat <= 0 or max_msat <= 0 or min_msat > max_msat:
            raise LNURLWithdrawInvalidAmountError("invalid_withdrawable_bounds")
        if max_msat > approved_amount_msat:
            raise LNURLWithdrawLimitExceededError("max_exceeds_approved_amount")
        return min_msat, max_msat

    def _ttl(self, requested: int | None) -> int:
        ttl = requested or self.config.default_ttl_seconds
        if ttl <= 0:
            raise LNURLWithdrawRequestError("invalid_ttl")
        return min(ttl, self.config.max_ttl_seconds)

    def _callback_host(self) -> str:
        parsed = urlparse(self.config.callback_base_url)
        if not parsed.hostname:
            raise LNURLWithdrawRequestError("callback_host_invalid")
        return parsed.hostname.lower()

    def _build_callback_url(self, reference: str) -> str:
        parsed = urlparse(self.config.callback_base_url.rstrip("/"))
        if parsed.username or parsed.password or parsed.fragment or not parsed.hostname:
            raise LNURLWithdrawRequestError("callback_url_invalid")
        if parsed.scheme != "https" and not (self.config.onion_enabled and parsed.hostname.endswith(".onion") and parsed.scheme in {"http", "https"}):
            raise LNURLWithdrawRequestError("callback_url_invalid")
        base = self.config.callback_base_url.rstrip("/")
        url = f"{base}{_WITHDRAW_CALLBACK_PATH_PREFIX}{reference}"
        validate_lnurl_url(url, policy=LNURLURLPolicy.onion() if parsed.hostname.endswith(".onion") else LNURLURLPolicy.service_owned_callback(domains={parsed.hostname}))
        return url

    def _result_from_record(self, record: LNURLWithdrawRequestRecord, *, k1: str | None = None) -> LNURLWithdrawRequestResult:
        callback_url = self._build_callback_url(record.opaque_request_id)
        if k1 is None:
            # k1 is intentionally not recoverable from persisted storage. The LNURL itself is returned
            # on the initial issuance path; idempotent retries return the same safe callback URL and status.
            k1 = "0" * 64
        payload = {
            "tag": "withdrawRequest",
            "callback": callback_url,
            "k1": k1,
            "defaultDescription": record.default_description,
            "minWithdrawable": record.min_withdrawable_msat,
            "maxWithdrawable": record.max_withdrawable_msat,
        }
        lnurl = encode_lnurl(_url_with_query(callback_url, payload), policy=LNURLURLPolicy.service_owned_callback(domains={self._callback_host()}))
        return LNURLWithdrawRequestResult(
            withdraw_request_id=record.opaque_request_id,
            status=record.status.value,
            tag="withdrawRequest",
            lnurl=lnurl,
            callback_url=callback_url,
            expires_at=record.expires_at,
            min_withdrawable_msat=record.min_withdrawable_msat,
            max_withdrawable_msat=record.max_withdrawable_msat,
            default_description=record.default_description,
            purpose=record.purpose,
            policy_decision_reference=record.policy_decision_reference,
        )

    def _audit_payload(self, record: LNURLWithdrawRequestRecord, *, decision: str, reason: str | None = None) -> dict[str, Any]:
        return {
            "withdraw_request_reference_hash": record.withdraw_request_reference_hash,
            "purpose": record.purpose,
            "min_withdrawable_msat": record.min_withdrawable_msat,
            "max_withdrawable_msat": record.max_withdrawable_msat,
            "principal_type": record.principal_type,
            "safe_actor_reference": safe_hash_for_log(record.principal_reference_hash),
            "policy_decision": decision,
            "risk_level": record.risk_level,
            "network": record.network,
            "expires_at": record.expires_at.isoformat().replace("+00:00", "Z"),
            "source_reference_hash": record.source_reference_hash,
            "reason_code": reason,
        }


def _new_request_reference() -> str:
    return f"wdr_{secrets.token_urlsafe(18)}"


def _sanitize_description(value: str) -> str:
    text = _DESCRIPTION_CONTROL_RE.sub(" ", value).replace("<", " ").replace(">", " ")
    text = " ".join(text.split())[:_MAX_DESCRIPTION_CHARS]
    lowered = text.lower()
    if any(term in lowered for term in _FORBIDDEN_DESCRIPTION_TERMS):
        raise LNURLWithdrawNotAuthorizedError("unsafe_description")
    if not text:
        return "Bitcoin Bastion withdraw"
    return text


def _default_description(purpose: LNURLWithdrawPurpose) -> str:
    return {
        LNURLWithdrawPurpose.SUBSCRIPTION_REFUND: "Bitcoin Bastion subscription refund",
        LNURLWithdrawPurpose.PAYREGISTER_REFUND: "Bastion PayRegister refund",
        LNURLWithdrawPurpose.CASHBACK: "Bitcoin Bastion cashback reward",
        LNURLWithdrawPurpose.REWARD: "Bitcoin Bastion reward payout",
        LNURLWithdrawPurpose.BUG_BOUNTY: "Bitcoin Bastion bug bounty payout",
        LNURLWithdrawPurpose.PARTNER_PAYOUT: "Bitcoin Bastion partner payout",
        LNURLWithdrawPurpose.MERCHANT_SETTLEMENT_HELPER: "Bastion merchant settlement helper",
        LNURLWithdrawPurpose.TESTNET_FAUCET: "Bitcoin Bastion testnet faucet",
        LNURLWithdrawPurpose.SIGNET_FAUCET: "Bitcoin Bastion signet faucet",
        LNURLWithdrawPurpose.OTHER_CONTROLLED_PAYOUT: "Bitcoin Bastion controlled payout",
    }[purpose]


def _url_with_query(callback_url: str, payload: dict[str, Any]) -> str:
    from urllib.parse import urlencode

    return f"{callback_url}?{urlencode({'k1': payload['k1']})}"


def _default_purpose_policies() -> dict[LNURLWithdrawPurpose, WithdrawPurposePolicy]:
    mainnet = frozenset({"bitcoin-mainnet"})
    testnets = frozenset({"bitcoin-testnet", "bitcoin-signet", "bitcoin-regtest"})
    return {
        LNURLWithdrawPurpose.SUBSCRIPTION_REFUND: WithdrawPurposePolicy(LNURLWithdrawPurpose.SUBSCRIPTION_REFUND, "controlled", True, True, False, True, 5_000_000, mainnet, "lnurl_withdraw_request_created"),
        LNURLWithdrawPurpose.PAYREGISTER_REFUND: WithdrawPurposePolicy(LNURLWithdrawPurpose.PAYREGISTER_REFUND, "business_critical", True, True, True, True, 10_000_000, mainnet, "lnurl_withdraw_request_created"),
        LNURLWithdrawPurpose.CASHBACK: WithdrawPurposePolicy(LNURLWithdrawPurpose.CASHBACK, "low_value", True, False, False, True, 500_000, mainnet, "lnurl_withdraw_request_created", source_required=False),
        LNURLWithdrawPurpose.REWARD: WithdrawPurposePolicy(LNURLWithdrawPurpose.REWARD, "controlled", True, True, False, True, 1_000_000, mainnet, "lnurl_withdraw_request_created"),
        LNURLWithdrawPurpose.BUG_BOUNTY: WithdrawPurposePolicy(LNURLWithdrawPurpose.BUG_BOUNTY, "high_value", True, True, False, True, 25_000_000, mainnet, "lnurl_withdraw_request_created"),
        LNURLWithdrawPurpose.PARTNER_PAYOUT: WithdrawPurposePolicy(LNURLWithdrawPurpose.PARTNER_PAYOUT, "business_critical", True, True, True, True, 25_000_000, mainnet, "lnurl_withdraw_request_created"),
        LNURLWithdrawPurpose.MERCHANT_SETTLEMENT_HELPER: WithdrawPurposePolicy(LNURLWithdrawPurpose.MERCHANT_SETTLEMENT_HELPER, "business_critical", True, True, True, True, 25_000_000, mainnet, "lnurl_withdraw_request_created"),
        LNURLWithdrawPurpose.TESTNET_FAUCET: WithdrawPurposePolicy(LNURLWithdrawPurpose.TESTNET_FAUCET, "low_value", False, False, False, True, 100_000, testnets, "lnurl_withdraw_request_created", source_required=False),
        LNURLWithdrawPurpose.SIGNET_FAUCET: WithdrawPurposePolicy(LNURLWithdrawPurpose.SIGNET_FAUCET, "low_value", False, False, False, True, 100_000, testnets, "lnurl_withdraw_request_created", source_required=False),
        LNURLWithdrawPurpose.OTHER_CONTROLLED_PAYOUT: WithdrawPurposePolicy(LNURLWithdrawPurpose.OTHER_CONTROLLED_PAYOUT, "high_value", True, True, False, True, 1_000_000, mainnet, "lnurl_withdraw_request_created"),
    }


__all__ = [
    "InMemoryLNURLWithdrawAuditSink",
    "LNURLWithdrawInvalidAmountError",
    "LNURLWithdrawIdempotencyConflictError",
    "LNURLWithdrawLimitExceededError",
    "LNURLWithdrawNotAuthorizedError",
    "LNURLWithdrawPurpose",
    "LNURLWithdrawRequestConfig",
    "LNURLWithdrawRequestError",
    "LNURLWithdrawRequestResult",
    "LNURLWithdrawRequestService",
    "LNURLWithdrawRevokedError",
    "LNURLWithdrawSourceAlreadyConsumedError",
    "LNURLWithdrawSourceRequiredError",
    "LNURLWithdrawStepUpRequiredError",
    "PolicyDecision",
    "PrincipalContext",
    "WithdrawPurposePolicy",
]
