from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict
from datetime import UTC, datetime

import pytest

from app.domain.wallet_auth.proofs import WalletVerificationStrength
from app.services.access.crypto.hashing import sha256_prefixed
from app.services.lnurl.auth_callback_verifier import VerifiedLNURLAuthProof
from app.services.lnurl.principal_service import (
    AuthDomainPolicy,
    InMemoryLightningPrincipalRepository,
    LightningPrincipalConfig,
    LightningPrincipalDomainMismatchError,
    LightningPrincipalInvalidTransitionError,
    LightningPrincipalProofNotVerifiedError,
    LightningPrincipalRevokedError,
    LightningPrincipalService,
    LightningPrincipalSuspendedError,
    normalize_auth_domain,
)

NOW = datetime(2026, 7, 15, tzinfo=UTC)
KEY = "02" + "11" * 32
OTHER_KEY = "03" + "22" * 32


class Revocations:
    def __init__(self) -> None:
        self.revoked: set[tuple[str, str]] = set()

    def is_revoked(self, *, target_type: str, target_hash: str) -> bool:
        return (target_type, target_hash) in self.revoked

    def revoke(self, *, target_type: str, target_hash: str, reason_code: str, policy_epoch: int) -> None:
        self.revoked.add((target_type, target_hash))


def _proof(*, domain: str = "auth.bitcoin-bastion.com", key: str = KEY, device: str | None = None, strength: WalletVerificationStrength = WalletVerificationStrength.STANDARD) -> VerifiedLNURLAuthProof:
    return VerifiedLNURLAuthProof(
        lnurl_key_hash="hmac-sha256:callback-hash",
        key_fingerprint=sha256_prefixed(bytes.fromhex(key)),
        auth_domain=domain,
        lnurl_action="login",  # type: ignore[arg-type]
        bastion_action="wallet_principal_authenticate",
        challenge_id="lac_test",
        policy_intent_hash="sha256:intent",
        verification_strength=strength,
        device_key_fingerprint=device,
        verified_at=NOW,
    )


def _service(*, events=None, revocations=None, policy: AuthDomainPolicy | None = None) -> LightningPrincipalService:
    return LightningPrincipalService(
        config=LightningPrincipalConfig(
            lnurl_auth_server_pepper="lnurl-pepper",
            principal_server_pepper="principal-pepper",
            product_pseudonym_pepper="product-pepper",
            domain_policy=policy or AuthDomainPolicy(),
        ),
        repository=InMemoryLightningPrincipalRepository(),
        revocation_registry=revocations,
        audit_emitter=(lambda event, payload: events.append((event, payload))) if events is not None else None,
        clock=lambda: NOW,
    )


def test_verified_lnurl_proof_creates_principal_and_reuse_is_idempotent() -> None:
    events: list[tuple[str, dict[str, object]]] = []
    service = _service(events=events)
    result = service.create_from_verified_lnurl_auth(
        proof=_proof(),
        normalized_linking_public_key=KEY,
        proof_fingerprint="sha256:proof",
        policy_hash="sha256:policy",
    )
    assert result.created is True
    assert result.principal.principal_type == "lightning_wallet_principal"
    assert result.principal.principal_hash.startswith("hmac-sha256:")
    assert result.principal.lnurl_key_hash.startswith("hmac-sha256:")
    assert result.device_binding_required is True
    assert result.policy_evaluation_required is True
    assert not hasattr(result, "session_token")
    assert not hasattr(result, "entitlement_id")
    again = service.create_from_verified_lnurl_auth(
        proof=_proof(),
        normalized_linking_public_key=KEY,
        proof_fingerprint="sha256:proof2",
        policy_hash="sha256:policy",
    )
    assert again.created is False
    assert again.principal.principal_hash == result.principal.principal_hash
    assert again.principal.verification_count == 2
    assert [event for event, _ in events][:2] == ["lightning_principal_created", "lightning_principal_verified"]


def test_unverified_or_mismatched_proof_cannot_create_principal() -> None:
    service = _service()
    with pytest.raises(LightningPrincipalProofNotVerifiedError):
        service.create_from_verified_lnurl_auth(proof=object(), normalized_linking_public_key=KEY, proof_fingerprint="sha256:proof", policy_hash="sha256:policy")  # type: ignore[arg-type]
    with pytest.raises(LightningPrincipalProofNotVerifiedError):
        service.create_from_verified_lnurl_auth(proof=_proof(strength=WalletVerificationStrength.HIGH_ASSURANCE), normalized_linking_public_key=KEY, proof_fingerprint="sha256:proof", policy_hash="sha256:policy")
    with pytest.raises(LightningPrincipalProofNotVerifiedError):
        service.create_from_verified_lnurl_auth(proof=_proof(key=KEY), normalized_linking_public_key=OTHER_KEY, proof_fingerprint="sha256:proof", policy_hash="sha256:policy")


def test_domain_normalization_policy_and_isolation() -> None:
    assert normalize_auth_domain("AUTH.Bitcoin-Bastion.Com.") == "auth.bitcoin-bastion.com"
    with pytest.raises(LightningPrincipalDomainMismatchError):
        normalize_auth_domain("https://auth.bitcoin-bastion.com/path?k=v")
    with pytest.raises(LightningPrincipalDomainMismatchError):
        _service().create_from_verified_lnurl_auth(proof=_proof(domain="login.bitcoin-bastion.com"), normalized_linking_public_key=KEY, proof_fingerprint="sha256:proof", policy_hash="sha256:policy")
    policy = AuthDomainPolicy(merchant_custom_domains=frozenset({"merchant.example.com"}))
    service = _service(policy=policy)
    primary = service.create_from_verified_lnurl_auth(proof=_proof(), normalized_linking_public_key=KEY, proof_fingerprint="sha256:p1", policy_hash="sha256:policy")
    merchant = service.create_from_verified_lnurl_auth(proof=_proof(domain="merchant.example.com"), normalized_linking_public_key=KEY, proof_fingerprint="sha256:p2", policy_hash="sha256:policy")
    assert primary.principal.principal_hash != merchant.principal.principal_hash


def test_concurrent_creation_returns_one_principal_identity() -> None:
    service = _service()

    def create() -> str:
        return service.create_from_verified_lnurl_auth(proof=_proof(), normalized_linking_public_key=KEY, proof_fingerprint="sha256:proof", policy_hash="sha256:policy").principal.principal_hash

    with ThreadPoolExecutor(max_workers=5) as pool:
        hashes = list(pool.map(lambda _: create(), range(5)))
    assert len(set(hashes)) == 1


def test_state_transitions_authentication_context_and_revocation() -> None:
    revocations = Revocations()
    service = _service(revocations=revocations)
    created = service.create_from_verified_lnurl_auth(proof=_proof(device="sha256:device"), normalized_linking_public_key=KEY, proof_fingerprint="sha256:proof", policy_hash="sha256:policy")
    context = service.find_active_principal(created.principal.principal_hash, device_key_fingerprint="sha256:device")
    assert context.device_binding_required is False
    assert context.entitlement_required is True
    assert context.policy_evaluation_required is True
    suspended = service.suspend_principal(created.principal.principal_hash, reason_code="risk")
    assert suspended.changed is True
    with pytest.raises(LightningPrincipalSuspendedError):
        service.find_active_principal(created.principal.principal_hash)
    service.activate_principal(created.principal.principal_hash, reason_code="reviewed")
    service.lock_for_recovery(created.principal.principal_hash, reason_code="recovery")
    recovery_context = service.find_active_principal(created.principal.principal_hash)
    assert recovery_context.status.value == "recovery_locked"
    service.restore_from_recovery_lock(created.principal.principal_hash, reason_code="restored")
    service.revoke_principal(created.principal.principal_hash, reason_code="compromised")
    with pytest.raises(LightningPrincipalRevokedError):
        service.find_active_principal(created.principal.principal_hash)
    with pytest.raises(LightningPrincipalInvalidTransitionError):
        service.activate_principal(created.principal.principal_hash, reason_code="no_auto_reactivate")


def test_revoked_key_device_and_principal_are_rejected() -> None:
    revocations = Revocations()
    service = _service(revocations=revocations)
    lnurl_key_hash = service.derive_lnurl_key_hash(normalized_linking_public_key=KEY, auth_domain="auth.bitcoin-bastion.com")
    revocations.revoked.add(("lnurl_auth_key_hash", lnurl_key_hash))
    with pytest.raises(LightningPrincipalRevokedError):
        service.create_from_verified_lnurl_auth(proof=_proof(), normalized_linking_public_key=KEY, proof_fingerprint="sha256:proof", policy_hash="sha256:policy")
    revocations.revoked.clear()
    revocations.revoked.add(("wallet_device", "sha256:device"))
    with pytest.raises(LightningPrincipalRevokedError):
        service.create_from_verified_lnurl_auth(proof=_proof(device="sha256:device"), normalized_linking_public_key=KEY, proof_fingerprint="sha256:proof", policy_hash="sha256:policy")


def test_audit_and_serialization_do_not_expose_raw_key_or_user_identity_fields() -> None:
    events: list[tuple[str, dict[str, object]]] = []
    service = _service(events=events)
    result = service.create_from_verified_lnurl_auth(proof=_proof(), normalized_linking_public_key=KEY, proof_fingerprint="sha256:proof", policy_hash="sha256:policy", request_context={"safe": "metadata"})
    rendered = repr(result) + repr(events) + repr(asdict(result.principal))
    assert KEY not in rendered
    assert "signature" not in rendered.lower()
    assert "k1" not in rendered.lower()
    assert "user_id" not in rendered.lower()
    assert "email" not in rendered.lower()
    assert events and events[0][0] == "lightning_principal_created"


def test_secret_material_and_automatic_merge_are_rejected_or_contract_only() -> None:
    service = _service()
    with pytest.raises(Exception):
        service.create_from_verified_lnurl_auth(proof=_proof(), normalized_linking_public_key=KEY, proof_fingerprint="sha256:proof", policy_hash="sha256:policy", request_context={"mnemonic": "seed phrase words"})
    first = service.create_from_verified_lnurl_auth(proof=_proof(), normalized_linking_public_key=KEY, proof_fingerprint="sha256:p1", policy_hash="sha256:policy")
    second = service.create_from_verified_lnurl_auth(proof=_proof(key=OTHER_KEY), normalized_linking_public_key=OTHER_KEY, proof_fingerprint="sha256:p2", policy_hash="sha256:policy")
    link = service.request_principal_link(source_principal_hash=first.principal.principal_hash, target_principal_hash=second.principal.principal_hash, policy_hash="sha256:policy")
    assert link.requires_policy_approval is True
    assert link.requires_fresh_proof is True
    assert link.automatic_merge_allowed is False
