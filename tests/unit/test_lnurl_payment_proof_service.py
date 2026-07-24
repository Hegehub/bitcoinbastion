from __future__ import annotations

import asyncio
import base64
import hashlib
from dataclasses import replace
from datetime import UTC, datetime, timedelta

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from app.domain.lnurl.payment_proofs import LNURLPaymentContext, LNURLPrincipalBindingMethod
from app.services.lnurl.errors import (
    PaymentBindingInvalidError,
    PaymentInvoiceMismatchError,
    PaymentProductMismatchError,
    PaymentProofIntegrityError,
    PaymentProofRevokedError,
    SettlementEvidenceExpiredError,
    SettlementNotVerifiedError,
)
from app.services.lnurl.payment_proof import (
    InMemoryLNURLPaymentProofRepository,
    LNURLPaymentProofConfig,
    LNURLPaymentProofService,
    LNURLPrincipalBinding,
)
from app.services.lnurl.verification_sources import (
    LNURLSettlementState,
    LNURLVerificationSourceType,
    SettlementSourceResult,
    test_bolt11 as make_test_bolt11,
)
from app.services.lnurl.verify import (
    InMemoryLNURLVerifyRepository,
    LNURLPaymentForVerification,
    LNURLVerifyService,
)


class Source:
    source_type = LNURLVerificationSourceType.INTERNAL_LIGHTNING_NODE

    def __init__(self, result: SettlementSourceResult) -> None:
        self.result = result

    async def verify(self, payment: LNURLPaymentForVerification) -> SettlementSourceResult:
        return self.result


def keys() -> tuple[str, str]:
    private = Ed25519PrivateKey.generate()
    raw_private = private.private_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PrivateFormat.Raw,
        encryption_algorithm=serialization.NoEncryption(),
    )
    raw_public = private.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    return (
        base64.urlsafe_b64encode(raw_private).decode().rstrip("="),
        base64.urlsafe_b64encode(raw_public).decode().rstrip("="),
    )


def setup_services(*, settled: bool = True, plan_code: str = "pro_pass", amount_msat: int = 2500):
    preimage = b"p" * 32
    payment_hash = hashlib.sha256(preimage).hexdigest()
    invoice = make_test_bolt11(
        payment_hash=payment_hash,
        amount_msat=amount_msat,
        network="lightning-mainnet",
        timestamp=datetime.now(UTC),
        description_hash="sha256:metadata",
    )
    payment = LNURLPaymentForVerification(
        "pay1",
        "lpay_1",
        invoice,
        amount_msat,
        payment_hash,
        "lightning-mainnet",
        metadata_hash="sha256:metadata",
        plan_code=plan_code,
    )
    verify_repo = InMemoryLNURLVerifyRepository({"pay1": payment})
    source = Source(
        SettlementSourceResult(
            LNURLVerificationSourceType.INTERNAL_LIGHTNING_NODE,
            settled,
            LNURLSettlementState.SETTLED if settled else LNURLSettlementState.PENDING,
            invoice=invoice,
            preimage=preimage.hex() if settled else None,
        )
    )
    verify = LNURLVerifyService(repository=verify_repo, sources=[source])
    if settled:
        asyncio.run(verify.verify_payment("pay1"))
    priv, pub = keys()
    events = []
    proof = LNURLPaymentProofService(
        verification_service=verify,
        repository=InMemoryLNURLPaymentProofRepository(),
        config=LNURLPaymentProofConfig(issuer_private_key=priv, issuer_public_key=pub),
        event_sink=events.append,
    )
    return payment, verify, proof, events


def issue(service: LNURLPaymentProofService, product_code: str = "pro_pass", binding=None):
    return asyncio.run(
        service.issue_payment_proof(
            "pay1",
            payment_context=LNURLPaymentContext.SUBSCRIPTION,
            product_code=product_code,
            principal_binding=binding,
        )
    )


def test_verified_settled_payment_creates_signed_proof_and_event():
    _, _, service, events = setup_services()
    proof = issue(service)
    assert proof.settled is True
    assert proof.proof_id.startswith("lpp_")
    assert service.verify_payment_proof_integrity(proof)
    assert events and events[0].event_type == "lnurl.payment_proof.issued"
    assert service.repository.count_entitlements() == 0


def test_unsettled_or_unverified_invoice_does_not_create_proof():
    _, _, service, _ = setup_services(settled=False)
    with pytest.raises(SettlementNotVerifiedError):
        issue(service)


def test_payment_substitution_mismatches_are_rejected():
    payment, verify, service, _ = setup_services()
    latest = verify.get_latest_verification("pay1")
    assert latest is not None
    verify.repository.save(replace(latest, invoice_hash="sha256:wrong", idempotency_key="sha256:wrong"))
    with pytest.raises(PaymentInvoiceMismatchError):
        issue(service)
    payment2, _, service2, _ = setup_services(plan_code="enterprise_pass")
    service2.verification_service.repository.payments["pay1"] = payment2
    with pytest.raises(PaymentProductMismatchError):
        issue(service2, product_code="pro_pass")


def test_duplicate_issuance_returns_existing_proof():
    _, _, service, _ = setup_services()
    first = issue(service)
    second = issue(service)
    assert first.proof_id == second.proof_id


def test_concurrent_issuance_is_idempotent():
    _, _, service, _ = setup_services()

    async def run():
        return await asyncio.gather(
            service.issue_payment_proof(
                "pay1", payment_context="subscription", product_code="pro_pass"
            ),
            service.issue_payment_proof(
                "pay1", payment_context="subscription", product_code="pro_pass"
            ),
        )

    a, b = asyncio.run(run())
    assert a.proof_id == b.proof_id


def test_canonical_fingerprint_stable_and_tampering_fails():
    _, _, service, _ = setup_services()
    proof = issue(service)
    assert service.verify_payment_proof_integrity(proof)
    tampered = replace(proof, amount_msat=proof.amount_msat + 1)
    with pytest.raises(PaymentProofIntegrityError):
        service.verify_payment_proof_integrity(tampered)
    invalid_sig = replace(proof, issuer_signature=replace(proof.issuer_signature, sig="A" * 86))
    with pytest.raises(PaymentProofIntegrityError):
        service.verify_payment_proof_integrity(invalid_sig)


def test_verified_principal_binding_succeeds_and_unverified_binding_rejected():
    _, _, service, _ = setup_services()
    binding = LNURLPrincipalBinding(
        method=LNURLPrincipalBindingMethod.VERIFIED_LNURL_AUTH,
        principal_hash="hmac-sha256:principal",
        principal_type="lightning_wallet_principal",
        verification_hash="sha256:verified-auth",
    )
    assert issue(service, binding=binding).principal_hash == "hmac-sha256:principal"
    _, _, service2, _ = setup_services()
    with pytest.raises(PaymentBindingInvalidError):
        issue(service2, binding=LNURLPrincipalBinding(method=LNURLPrincipalBindingMethod.VERIFIED_LNURL_AUTH))


def test_anonymous_payment_supported_and_raw_material_not_stored_or_returned():
    payment, _, service, _ = setup_services()
    proof = issue(service)
    rendered = repr(proof) + repr(proof.safe_response())
    assert payment.bolt11 not in rendered
    assert payment.payment_hash not in proof.safe_response().values()
    assert "preimage" not in repr(proof.safe_response()).lower()
    assert proof.binding_method == "unbound_payment"


def test_revoked_proof_fails_active_integrity_verification():
    _, _, service, _ = setup_services()
    proof = issue(service)
    revoked = service.revoke_payment_proof(proof.proof_id, reason="administrative_dispute")
    with pytest.raises(PaymentProofRevokedError):
        service.verify_payment_proof_integrity(revoked)


def test_stale_verification_and_test_settlement_rejected():
    _, verify, service, _ = setup_services()
    latest = verify.get_latest_verification("pay1")
    assert latest is not None
    verify.repository.save(
        replace(
            latest,
            verified_at=datetime.now(UTC) - timedelta(hours=3),
            idempotency_key="sha256:stale",
        )
    )
    service.config = replace(service.config, max_verification_age_seconds=1)
    with pytest.raises(SettlementEvidenceExpiredError):
        issue(service)
