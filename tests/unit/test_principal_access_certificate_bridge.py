from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime, timedelta

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.db.base import Base
from app.db.models.access import AccessCertificatePrincipalBinding, SubscriptionEntitlement
from app.db.models.wallet_auth import WalletDevice, WalletPrincipal, WalletSession
from app.services.access.certificate_issuer import AccessCertificateIssuer
from app.services.access.entitlement_service import SubscriptionEntitlementService
from app.services.access.principal_certificate_bridge import (
    CertificateAssuranceProfile,
    PrincipalAccessCertificateBridge,
    PrincipalCertificateBridgeError,
    PrincipalCertificateIssueRequest,
    PrincipalCertificatePolicyDecision,
)


class AllowPolicy:
    def evaluate(self, request):
        return PrincipalCertificatePolicyDecision(
            "allow",
            "verified",
            "sha256:policy",
            request.policy_allowed_scopes,
            request.policy_allowed_metric_groups,
            request.requested_assurance_profile,
        )


class DenyPolicy(AllowPolicy):
    def evaluate(self, request):
        return replace(super().evaluate(request), decision="deny", reason_code="policy_denied")


class Revocations:
    revoked = False

    def check_certificate_bridge_targets(self, **targets):
        return {key: self.revoked for key in targets}


def keys():
    private = Ed25519PrivateKey.generate()
    private_pem = private.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    ).decode()
    public_pem = (
        private.public_key()
        .public_bytes(
            serialization.Encoding.PEM,
            serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        .decode()
    )
    return private_pem, public_pem


@pytest.fixture()
def setup():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    now = datetime.now(UTC)
    with Session(engine) as db:
        principal = WalletPrincipal(
            principal_hash="hmac-sha256:principal",
            principal_type="bitcoin_wallet_principal",
            status="active",
            verification_strength="standard",
            primary_proof_method="bip322",
            policy_epoch=2,
        )
        db.add(principal)
        db.flush()
        device = WalletDevice(
            principal_id=principal.id,
            principal_hash=principal.principal_hash,
            device_id_hash="sha256:device-id",
            device_key_fingerprint="sha256:device",
            device_class="desktop_vault",
            binding_method="bip322",
            status="active",
        )
        db.add(device)
        db.flush()
        db.add(
            WalletSession(
                principal_id=principal.id,
                principal_hash=principal.principal_hash,
                device_id=device.id,
                device_key_fingerprint=device.device_key_fingerprint,
                session_hash="sha256:session",
                status="active",
                auth_method="bip322",
                verification_strength="standard",
                scopes_json=["signals:lite:read"],
                expires_at=now + timedelta(hours=1),
            )
        )
        entitlement = SubscriptionEntitlement(
            pass_lookup_hash="hmac-sha256:source-pass",
            plan_code="pro_pass",
            status="active",
            metric_entitlements_json={"metrics_basic": {}},
            limits_json={},
            scopes_json=["signals:lite:read", "treasury:read"],
            issuer_key_id="issuer",
            issuer_signature_json={},
            valid_from=now - timedelta(minutes=1),
            valid_until=now + timedelta(days=1),
            metadata_json={"principal_hash": principal.principal_hash},
        )
        db.add(entitlement)
        db.flush()
        private, public = keys()
        issuer = AccessCertificateIssuer(
            db,
            server_pepper="test-pepper",
            issuer_private_key=private,
            issuer_public_key=public,
            issuer_key_id="issuer",
        )
        entitlements = SubscriptionEntitlementService(
            db,
            issuer_private_key=private,
            issuer_public_key=public,
            issuer_key_id="issuer",
        )
        revocations = Revocations()
        bridge = PrincipalAccessCertificateBridge(
            db,
            issuer=issuer,
            entitlement_service=entitlements,
            policy=AllowPolicy(),
            revocation_resolver=revocations,
        )
        request = PrincipalCertificateIssueRequest(
            principal_hash=principal.principal_hash,
            principal_type=principal.principal_type,
            device_key_fingerprint=device.device_key_fingerprint,
            entitlement_id=entitlement.id,
            session_hash="sha256:session",
            proof_method="bip322",
            verification_strength="standard",
            last_principal_verification_at=now,
            requested_scopes=frozenset({"signals:lite:read"}),
            requested_metric_groups=frozenset({"metrics_basic"}),
            policy_allowed_scopes=frozenset({"signals:lite:read"}),
            policy_allowed_metric_groups=frozenset({"metrics_basic"}),
            principal_allowed_scopes=frozenset({"signals:lite:read"}),
            requested_assurance_profile=CertificateAssuranceProfile.STANDARD,
            requested_expires_at=now + timedelta(hours=2),
            idempotency_key_hash="sha256:idempotency",
            pop_request_verified=True,
        )
        yield db, bridge, request, principal, device, entitlement, revocations


def test_bitcoin_principal_certificate_is_bound_and_idempotent(setup):
    db, bridge, request, *_ = setup
    first = bridge.issue(request)
    second = bridge.issue(request)
    binding = db.execute(select(AccessCertificatePrincipalBinding)).scalar_one()
    assert first.certificate_fingerprint == second.certificate_fingerprint
    assert second.idempotent_replay
    assert binding.principal_hash == request.principal_hash
    assert binding.device_key_fingerprint == request.device_key_fingerprint
    assert first.effective_scopes == ("signals:lite:read",)
    assert (
        first.certificate_payload["principal_binding"]["principal_hash"] == request.principal_hash
    )


def test_policy_revocation_and_entitlement_are_fail_closed(setup):
    _, bridge, request, _, _, entitlement, revocations = setup
    bridge.policy = DenyPolicy()
    with pytest.raises(PrincipalCertificateBridgeError, match="policy_denied"):
        bridge.issue(request)
    bridge.policy = AllowPolicy()
    revocations.revoked = True
    with pytest.raises(PrincipalCertificateBridgeError, match="principal_revoked"):
        bridge.issue(replace(request, idempotency_key_hash="sha256:second"))
    revocations.revoked = False
    entitlement.valid_until = datetime.now(UTC) - timedelta(seconds=1)
    with pytest.raises(PrincipalCertificateBridgeError, match="entitlement_expired"):
        bridge.issue(replace(request, idempotency_key_hash="sha256:third"))


def test_scope_intersection_never_expands_permissions(setup):
    _, bridge, request, *_ = setup
    with pytest.raises(PrincipalCertificateBridgeError, match="scope_not_allowed"):
        bridge.issue(
            replace(
                request,
                requested_scopes=frozenset({"signals:lite:read", "api_keys:manage"}),
            )
        )


def test_lnurl_certificate_cannot_claim_treasury_or_skip_domain_verification(setup):
    _, bridge, request, principal, *_ = setup
    principal.principal_type = "lightning_wallet_principal"
    lightning = replace(
        request,
        principal_type="lightning_wallet_principal",
        proof_method="lnurl_auth",
        requested_scopes=frozenset({"treasury:read"}),
        principal_allowed_scopes=frozenset({"treasury:read"}),
        policy_allowed_scopes=frozenset({"treasury:read"}),
        auth_domain_verified=True,
    )
    with pytest.raises(PrincipalCertificateBridgeError, match="proof_too_weak"):
        bridge.issue(lightning)
    with pytest.raises(PrincipalCertificateBridgeError, match="proof_too_weak"):
        bridge.issue(
            replace(
                lightning,
                requested_scopes=frozenset({"signals:lite:read"}),
                principal_allowed_scopes=frozenset({"signals:lite:read"}),
                policy_allowed_scopes=frozenset({"signals:lite:read"}),
                auth_domain_verified=False,
            )
        )


def test_high_assurance_requires_fresh_step_up_and_pop(setup):
    _, bridge, request, *_ = setup
    high = replace(request, requested_assurance_profile=CertificateAssuranceProfile.HIGH_ASSURANCE)
    with pytest.raises(PrincipalCertificateBridgeError, match="step_up_required"):
        bridge.issue(high)
    with pytest.raises(PrincipalCertificateBridgeError, match="session_invalid"):
        bridge.issue(replace(request, pop_request_verified=False))


def test_export_is_explicit_non_bearer_and_contains_no_secret_fields(setup):
    _, bridge, request, *_ = setup
    bridge.export_enabled = True
    result = bridge.issue(replace(request, export_requested=True, human_intent_verified=True))
    assert result.export_payload["export_policy"]["bearer_access"] is False
    serialized = str(result.export_payload).lower()
    assert "private_key" not in serialized
    assert "mnemonic" not in serialized
    assert "raw_access_pass" not in serialized
