"""LNURL-pay successAction builder and activation reference service."""

from __future__ import annotations

from dataclasses import dataclass, field
from inspect import isawaitable
from datetime import UTC, datetime, timedelta
from typing import Any
from urllib.parse import urlsplit, urlunsplit
from uuid import uuid4

from app.db.repositories.lnurl_success_action_repository import (
    InMemoryLNURLSuccessActionRepository,
    LNURLSuccessActionRecord,
    LNURLSuccessActionRepository,
)
from app.domain.lnurl.success_actions import (
    LNURLActivationPurpose,
    LNURLActivationStatus,
    LNURLSuccessActionType,
    LNURL_ACTIVATION_DEFAULT_TTL_SECONDS,
    LNURL_ACTIVATION_MAX_TTL_SECONDS,
    LNURL_ACTIVATION_REFERENCE_BYTES,
    LNURL_SUCCESS_ACTION_ALLOWED_SCHEMES,
    LNURL_SUCCESS_ACTION_ONION_SCHEMES,
    contains_forbidden_success_action_secret,
)
from app.schemas.lnurl_success_action import LNURLMessageSuccessAction, LNURLURLSuccessAction
from app.services.access.crypto.hashing import hmac_sha256_prefixed, secure_token_urlsafe, sha256_prefixed
from app.services.lnurl.url_safety import LNURLURLPolicy, validate_lnurl_url

_SUBSCRIPTION_PURPOSES = {
    LNURLActivationPurpose.SUBSCRIPTION_ACTIVATION,
    LNURLActivationPurpose.SUBSCRIPTION_RENEWAL,
    LNURLActivationPurpose.SUBSCRIPTION_UPGRADE,
}

_PURPOSE_TARGETS = {
    LNURLActivationPurpose.SUBSCRIPTION_ACTIVATION: "/access/activate/{reference}",
    LNURLActivationPurpose.SUBSCRIPTION_RENEWAL: "/access/status/{reference}",
    LNURLActivationPurpose.SUBSCRIPTION_UPGRADE: "/access/activate/{reference}",
    LNURLActivationPurpose.VAULT_SETUP: "/vault/setup/{reference}",
    LNURLActivationPurpose.ACCESS_CERTIFICATE_SETUP: "/access/activate/{reference}",
    LNURLActivationPurpose.PAYREGISTER_RECEIPT: "/payregister/receipts/{reference}",
    LNURLActivationPurpose.MERCHANT_RECEIPT: "/receipts/{reference}",
    LNURLActivationPurpose.BUSINESS_ONBOARDING: "/business/onboarding/{reference}",
    LNURLActivationPurpose.ENTERPRISE_ONBOARDING: "/business/onboarding/{reference}",
    LNURLActivationPurpose.PAYMENT_RECEIPT: "/receipts/{reference}",
    LNURLActivationPurpose.CONTRIBUTION_RECEIPT: "/receipts/{reference}",
}


@dataclass(frozen=True, slots=True)
class LNURLSuccessActionConfig:
    enabled: bool = True
    default_type: LNURLSuccessActionType = LNURLSuccessActionType.URL
    base_url: str = "https://bastion.example.com"
    allowed_hosts: frozenset[str] = frozenset({"bastion.example.com"})
    activation_ttl_seconds: int = LNURL_ACTIVATION_DEFAULT_TTL_SECONDS
    max_ttl_seconds: int = LNURL_ACTIVATION_MAX_TTL_SECONDS
    activation_server_pepper: str = "development-lnurl-activation-pepper-change-me"
    onion_mode_enabled: bool = False
    public_receipts_enabled: bool = True
    vault_setup_links_enabled: bool = False


@dataclass(slots=True)
class LNURLSuccessActionMetrics:
    counters: dict[tuple[str, tuple[tuple[str, str], ...]], int] = field(default_factory=dict)

    def increment(self, name: str, **labels: str) -> None:
        safe_labels = tuple(sorted((key, value) for key, value in labels.items()))
        self.counters[(name, safe_labels)] = self.counters.get((name, safe_labels), 0) + 1


class LNURLSuccessActionService:
    """Build safe LNURL successAction fragments without granting access."""

    def __init__(
        self,
        *,
        repository: LNURLSuccessActionRepository | None = None,
        config: LNURLSuccessActionConfig | None = None,
        audit_chain: Any | None = None,
        metrics: LNURLSuccessActionMetrics | None = None,
    ) -> None:
        self.repository = repository or InMemoryLNURLSuccessActionRepository()
        self.config = config or LNURLSuccessActionConfig()
        self.audit_chain = audit_chain
        self.metrics = metrics or LNURLSuccessActionMetrics()

    def activation_reference_hash(self, raw_reference: str) -> str:
        return hmac_sha256_prefixed(self.config.activation_server_pepper, f"lnurl-success-action:v1:{raw_reference}")

    def create_activation_reference(self) -> str:
        return "lnact_" + secure_token_urlsafe(LNURL_ACTIVATION_REFERENCE_BYTES)

    async def create_activation_record(
        self,
        *,
        payment_request_id: str,
        purpose: LNURLActivationPurpose,
        callback_origin: str,
        action_type: LNURLSuccessActionType | None = None,
        payment_proof_id: str | None = None,
        entitlement_id: str | None = None,
        wallet_principal_hash: str | None = None,
        lightning_principal_hash: str | None = None,
        merchant_context_hash: str | None = None,
        payregister_context_hash: str | None = None,
        ttl_seconds: int | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> tuple[LNURLSuccessActionRecord, str]:
        if not self.config.enabled:
            raise ValueError("success_action_disabled")
        raw_reference = self.create_activation_reference()
        callback_host = self.validate_callback_domain(callback_origin)
        purpose = LNURLActivationPurpose(purpose)
        action_type = action_type or self.config.default_type
        safe_target_path = self.validate_safe_target_path(_PURPOSE_TARGETS[purpose].format(reference=raw_reference))
        ttl = self._bounded_ttl(ttl_seconds)
        now = datetime.now(UTC)
        record = LNURLSuccessActionRecord(
            activation_id="lnactobj_" + uuid4().hex,
            action_type=action_type,
            purpose=purpose,
            activation_reference_hash=self.activation_reference_hash(raw_reference),
            payment_request_id=payment_request_id,
            payment_proof_id=payment_proof_id,
            entitlement_id=entitlement_id,
            wallet_principal_hash=wallet_principal_hash,
            lightning_principal_hash=lightning_principal_hash,
            merchant_context_hash=merchant_context_hash,
            payregister_context_hash=payregister_context_hash,
            callback_origin_hash=sha256_prefixed(callback_origin),
            callback_host=callback_host,
            safe_target_path=safe_target_path.replace(raw_reference, "{reference}"),
            status=LNURLActivationStatus.CREATED,
            expires_at=now + timedelta(seconds=ttl),
            created_at=now,
            updated_at=now,
            metadata_json=metadata or {},
        )
        persisted = await self.repository.create_success_action(record)
        returned_reference = raw_reference if persisted.activation_id == record.activation_id else ""
        self.metrics.increment("lnurl_success_actions_created_total", type=action_type.value, purpose=purpose.value)
        await self._audit("lnurl_success_action_created", persisted, reason_code="created")
        return persisted, returned_reference

    def build_message_action(self, message: str) -> dict[str, str]:
        if "activated" in message.lower() and "verify" not in message.lower() and "verified" not in message.lower():
            raise ValueError("misleading_success_action_message")
        return LNURLMessageSuccessAction(message=message).model_dump()

    def build_url_action(self, *, description: str, raw_reference: str, callback_origin: str, purpose: LNURLActivationPurpose) -> dict[str, str]:
        host = self.validate_callback_domain(callback_origin)
        target_path = self.validate_safe_target_path(_PURPOSE_TARGETS[LNURLActivationPurpose(purpose)].format(reference=raw_reference))
        parsed_base = urlsplit(self.config.base_url)
        scheme = parsed_base.scheme.lower()
        if scheme not in LNURL_SUCCESS_ACTION_ALLOWED_SCHEMES:
            if not (self.config.onion_mode_enabled and parsed_base.hostname and parsed_base.hostname.endswith(".onion") and scheme in LNURL_SUCCESS_ACTION_ONION_SCHEMES):
                raise ValueError("unsafe_success_action_url")
        if (parsed_base.hostname or "").lower() != host:
            raise ValueError("success_action_domain_mismatch")
        url = urlunsplit((scheme, parsed_base.netloc, target_path, "", ""))
        validate_lnurl_url(url, policy=LNURLURLPolicy.service_owned_callback(domains={host}))
        return LNURLURLSuccessAction(description=description, url=url).model_dump()

    async def render_lnurl_callback_response_fragment(
        self,
        *,
        payment_request_id: str,
        purpose: LNURLActivationPurpose,
        callback_origin: str,
        action_type: LNURLSuccessActionType | None = None,
        description: str = "Open Bastion to view activation status",
        message: str = "Payment complete. Bastion will verify your activation.",
        **context: Any,
    ) -> dict[str, str]:
        action_kind = action_type or self.config.default_type
        record, raw_reference = await self.create_activation_record(
            payment_request_id=payment_request_id,
            purpose=purpose,
            callback_origin=callback_origin,
            action_type=action_kind,
            **context,
        )
        if action_kind is LNURLSuccessActionType.MESSAGE or not raw_reference:
            action = self.build_message_action(message)
            await self._audit("lnurl_success_action_message_issued", record, reason_code="message_issued")
            return action
        action = self.build_url_action(description=description, raw_reference=raw_reference, callback_origin=callback_origin, purpose=purpose)
        await self._audit("lnurl_success_action_url_issued", record, reason_code="url_issued")
        return action

    def validate_callback_domain(self, callback_origin: str) -> str:
        parsed = urlsplit(callback_origin)
        host = (parsed.hostname or "").lower()
        if parsed.username or parsed.password or not host:
            raise ValueError("invalid_success_action_url")
        allowed = {item.lower() for item in self.config.allowed_hosts}
        if host not in allowed:
            self.metrics.increment("lnurl_success_action_domain_rejections_total")
            raise ValueError("success_action_domain_mismatch")
        if parsed.scheme != "https" and not (self.config.onion_mode_enabled and host.endswith(".onion") and parsed.scheme == "http"):
            raise ValueError("unsafe_success_action_url")
        return host

    def validate_safe_target_path(self, target_path: str) -> str:
        if contains_forbidden_success_action_secret(target_path):
            raise ValueError("unsafe_success_action_url")
        if not target_path.startswith(("/access/activate/", "/access/status/", "/receipts/", "/vault/setup/", "/payregister/receipts/", "/business/onboarding/")):
            raise ValueError("unsafe_success_action_url")
        if "//" in target_path or ".." in target_path or "#" in target_path or "?" in target_path:
            raise ValueError("unsafe_success_action_url")
        return target_path

    def validate_action_content(self, value: str) -> str:
        if contains_forbidden_success_action_secret(value):
            self.metrics.increment("lnurl_success_action_secret_rejections_total")
            raise ValueError("success_action_secret_rejected")
        return value

    async def revoke_success_action(self, activation_reference: str) -> LNURLSuccessActionRecord:
        record = await self._lookup(activation_reference)
        updated = await self.repository.revoke(record.activation_id)
        self.metrics.increment("lnurl_activation_revoked_total", purpose=updated.purpose.value)
        await self._audit("lnurl_activation_revoked", updated, reason_code="revoked")
        return updated

    async def expire_stale_actions(self, now: datetime | None = None) -> int:
        # SQL repositories should implement efficient expiry jobs; in-memory tests call expire_activation directly.
        return 0

    async def _lookup(self, activation_reference: str) -> LNURLSuccessActionRecord:
        record = await self.repository.get_by_activation_reference_hash(self.activation_reference_hash(activation_reference))
        if record is None:
            raise ValueError("activation_not_found")
        return record

    def _bounded_ttl(self, ttl_seconds: int | None) -> int:
        ttl = ttl_seconds or self.config.activation_ttl_seconds
        if ttl <= 0 or ttl > min(self.config.max_ttl_seconds, LNURL_ACTIVATION_MAX_TTL_SECONDS):
            raise ValueError("activation_ttl_invalid")
        return ttl

    async def _audit(self, event_type: str, record: LNURLSuccessActionRecord, *, reason_code: str) -> None:
        if self.audit_chain is None:
            return
        payload = {
            "activation_object_hash": sha256_prefixed(record.activation_id),
            "purpose": record.purpose.value,
            "action_type": record.action_type.value,
            "payment_request_hash": sha256_prefixed(record.payment_request_id),
            "callback_host_hash": sha256_prefixed(record.callback_host),
            "reason_code": reason_code,
        }
        result = self.audit_chain.record_event(event_type, payload) if hasattr(self.audit_chain, "record_event") else None
        if isawaitable(result):
            await result
