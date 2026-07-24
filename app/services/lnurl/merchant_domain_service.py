"""Merchant Lightning Address domain lifecycle service."""
from __future__ import annotations

import secrets
from dataclasses import replace
from datetime import UTC, datetime

from app.domain.lnurl.merchant_addresses import MerchantDomainStatus, MerchantDomainVerificationMethod, MerchantLightningDomain, normalize_merchant_domain
from app.services.access.crypto.hashing import hmac_sha256_prefixed
from app.services.lnurl.merchant_address_audit import InMemoryMerchantAddressAudit
from app.services.lnurl.merchant_address_policy import AllowMerchantAddressPolicy, MerchantAddressPolicyHook
from app.services.lnurl.merchant_domain_verification import MerchantDomainVerificationChallenge, MerchantDomainVerificationService


class MerchantDomainError(ValueError):
    reason_code = "merchant_domain_error"


class MerchantDomainVerificationRequired(MerchantDomainError):
    reason_code = "merchant_domain_verification_required"


class MerchantDomainPolicyDenied(MerchantDomainError):
    reason_code = "merchant_domain_policy_denied"


class MerchantDomainRepository:
    def __init__(self) -> None:
        self.domains_by_id: dict[str, MerchantLightningDomain] = {}
        self.domain_id_by_hash: dict[str, str] = {}
        self.challenges_by_domain_id: dict[str, MerchantDomainVerificationChallenge] = {}

    def create(self, domain: MerchantLightningDomain) -> MerchantLightningDomain:
        existing_id = self.domain_id_by_hash.get(domain.domain_hash)
        if existing_id:
            return self.domains_by_id[existing_id]
        self.domains_by_id[domain.domain_id] = domain
        self.domain_id_by_hash[domain.domain_hash] = domain.domain_id
        return domain

    def save(self, domain: MerchantLightningDomain) -> MerchantLightningDomain:
        self.domains_by_id[domain.domain_id] = domain
        self.domain_id_by_hash[domain.domain_hash] = domain.domain_id
        return domain

    def get(self, domain_id: str) -> MerchantLightningDomain | None:
        return self.domains_by_id.get(domain_id)

    def get_by_domain(self, normalized_domain: str, pepper: str) -> MerchantLightningDomain | None:
        domain_id = self.domain_id_by_hash.get(hmac_sha256_prefixed(pepper, normalized_domain))
        return self.domains_by_id.get(domain_id) if domain_id else None

    def list(self) -> list[MerchantLightningDomain]:
        return list(self.domains_by_id.values())


class MerchantDomainService:
    def __init__(self, *, repository: MerchantDomainRepository | None = None, verifier: MerchantDomainVerificationService | None = None, policy_hook: MerchantAddressPolicyHook | None = None, audit: InMemoryMerchantAddressAudit | None = None, pepper: str = "dev-merchant-ln-domain-pepper-change-me", allow_operator_approval: bool = False) -> None:
        self.repository = repository or MerchantDomainRepository()
        self.verifier = verifier or MerchantDomainVerificationService()
        self.policy_hook = policy_hook or AllowMerchantAddressPolicy()
        self.audit = audit or InMemoryMerchantAddressAudit()
        self.pepper = pepper
        self.allow_operator_approval = allow_operator_approval

    def create_domain(self, *, normalized_domain: str, workspace_id_hash: str, verification_method: MerchantDomainVerificationMethod, bastion_managed_domains: frozenset[str] = frozenset()) -> MerchantLightningDomain:
        domain = normalize_merchant_domain(normalized_domain)
        if verification_method == MerchantDomainVerificationMethod.OPERATOR_APPROVED and not self.allow_operator_approval:
            raise MerchantDomainPolicyDenied("Operator approval is disabled")
        decision = self.policy_hook.evaluate("merchant_domain:create", {"workspace_hash": workspace_id_hash, "domain_hash": self._domain_hash(domain), "verification_method": verification_method.value})
        if not decision.allowed:
            raise MerchantDomainPolicyDenied(decision.reason_code)
        now = datetime.now(UTC)
        if verification_method == MerchantDomainVerificationMethod.BASTION_MANAGED and domain in bastion_managed_domains:
            status = MerchantDomainStatus.ACTIVE
            verified_at = now
        else:
            status = MerchantDomainStatus.PENDING_VERIFICATION
            verified_at = None
        record = MerchantLightningDomain(
            domain_id=f"mld_{secrets.token_urlsafe(18)}",
            domain_hash=self._domain_hash(domain),
            normalized_domain=domain,
            workspace_id_hash=workspace_id_hash,
            status=status,
            verification_method=verification_method,
            verification_token_hash=None,
            verified_at=verified_at,
            verification_expires_at=None,
            last_checked_at=None,
            tls_required=not domain.endswith(".onion"),
            onion_domain=domain.endswith(".onion"),
            created_at=now,
            updated_at=now,
        )
        persisted = self.repository.create(record)
        self.audit.emit("merchant_ln_domain_created", {"domain_hash": persisted.domain_hash, "workspace_hash": workspace_id_hash, "verification_method": verification_method.value})
        return persisted

    def start_verification(self, domain_id: str, method: MerchantDomainVerificationMethod) -> MerchantDomainVerificationChallenge:
        domain = self._domain(domain_id)
        challenge = self.verifier.create_challenge(domain.normalized_domain, method)
        self.repository.challenges_by_domain_id[domain_id] = challenge
        self.repository.save(replace(domain, verification_method=method, verification_token_hash=challenge.token_hash, verification_expires_at=challenge.expires_at, updated_at=datetime.now(UTC)))
        self.audit.emit("merchant_ln_domain_verification_started", {"domain_hash": domain.domain_hash, "method": method.value, "challenge_hash": challenge.token_hash})
        return challenge

    def mark_verified(self, domain_id: str) -> MerchantLightningDomain:
        domain = self._domain(domain_id)
        now = datetime.now(UTC)
        updated = replace(domain, status=MerchantDomainStatus.ACTIVE, verified_at=now, last_checked_at=now, updated_at=now)
        self.repository.save(updated)
        self.audit.emit("merchant_ln_domain_verified", {"domain_hash": domain.domain_hash, "workspace_hash": domain.workspace_id_hash})
        return updated

    def suspend_domain(self, domain_id: str, reason_code: str = "operator_request") -> MerchantLightningDomain:
        domain = self._domain(domain_id)
        updated = replace(domain, status=MerchantDomainStatus.SUSPENDED, updated_at=datetime.now(UTC))
        self.repository.save(updated)
        self.audit.emit("merchant_ln_domain_suspended", {"domain_hash": domain.domain_hash, "reason_code": reason_code})
        return updated

    def revoke_domain(self, domain_id: str, reason_code: str = "revoked") -> MerchantLightningDomain:
        domain = self._domain(domain_id)
        now = datetime.now(UTC)
        updated = replace(domain, status=MerchantDomainStatus.REVOKED, revoked_at=now, updated_at=now)
        self.repository.save(updated)
        self.audit.emit("merchant_ln_domain_revoked", {"domain_hash": domain.domain_hash, "reason_code": reason_code})
        return updated

    def _domain_hash(self, domain: str) -> str:
        return hmac_sha256_prefixed(self.pepper, domain)

    def _domain(self, domain_id: str) -> MerchantLightningDomain:
        domain = self.repository.get(domain_id)
        if domain is None:
            raise MerchantDomainError("Merchant domain unavailable")
        return domain
