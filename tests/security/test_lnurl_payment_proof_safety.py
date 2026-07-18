from __future__ import annotations

import asyncio
import base64
import hashlib
from datetime import UTC, datetime

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from app.domain.lnurl.payment_proofs import LNURLPaymentContext, LNURLPrincipalBindingMethod
from app.services.lnurl.errors import PaymentBindingInvalidError, SettlementNotVerifiedError
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
from app.services.lnurl.verify import InMemoryLNURLVerifyRepository, LNURLPaymentForVerification, LNURLVerifyService


class Source:
    source_type = LNURLVerificationSourceType.INTERNAL_LIGHTNING_NODE

    def __init__(self, result):
        self.result = result

    async def verify(self, payment):
        return self.result


def keypair():
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


def service_with_secret_material(*, issue_proof=True):
    preimage = b"secret-preimage-material-1234567"[:32]
    payment_hash = hashlib.sha256(preimage).hexdigest()
    invoice = make_test_bolt11(
        payment_hash=payment_hash,
        amount_msat=1000,
        network="lightning-mainnet",
        timestamp=datetime.now(UTC),
        description_hash="sha256:metadata",
    )
    payment = LNURLPaymentForVerification(
        "pay1",
        "lpay_secret",
        invoice,
        1000,
        payment_hash,
        "lightning-mainnet",
        metadata_hash="sha256:metadata",
        plan_code="pro_pass",
    )
    verify_repo = InMemoryLNURLVerifyRepository({"pay1": payment})
    verify = LNURLVerifyService(
        repository=verify_repo,
        sources=[
            Source(
                SettlementSourceResult(
                    LNURLVerificationSourceType.INTERNAL_LIGHTNING_NODE,
                    True,
                    LNURLSettlementState.SETTLED,
                    invoice=invoice,
                    preimage=preimage.hex(),
                )
            )
        ],
    )
    asyncio.run(verify.verify_payment("pay1"))
    private_key, public_key = keypair()
    proof_service = LNURLPaymentProofService(
        verification_service=verify,
        repository=InMemoryLNURLPaymentProofRepository(),
        config=LNURLPaymentProofConfig(issuer_private_key=private_key, issuer_public_key=public_key),
    )
    proof = None
    if issue_proof:
        proof = asyncio.run(
            proof_service.issue_payment_proof(
                "pay1", payment_context=LNURLPaymentContext.SUBSCRIPTION, product_code="pro_pass"
            )
        )
    return payment, preimage, private_key, proof, proof_service


def test_payment_proof_response_and_record_do_not_expose_raw_secrets():
    payment, preimage, private_key, proof, _ = service_with_secret_material()
    raw_payer_data = "person@example.com"
    raw_callback_token = "raw-callback-token"
    raw_access_pass = "raw-access-pass"
    raw_session_token = "raw-session-token"
    wallet_seed = "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about"
    rendered = repr(proof.safe_response()) + repr(proof)
    forbidden = [
        payment.bolt11,
        preimage.hex(),
        raw_payer_data,
        raw_callback_token,
        wallet_seed,
        private_key,
        raw_access_pass,
        raw_session_token,
    ]
    for value in forbidden:
        assert value not in rendered


def test_success_action_frontend_status_comment_and_email_cannot_create_proof_or_binding():
    _, _, _, _, proof_service = service_with_secret_material(issue_proof=False)
    with pytest.raises(PaymentBindingInvalidError):
        asyncio.run(
            proof_service.issue_payment_proof(
                "pay1",
                payment_context="subscription",
                product_code="pro_pass",
                principal_binding=LNURLPrincipalBinding(
                    method=LNURLPrincipalBindingMethod.VERIFIED_PAYERDATA_AUTH,
                    principal_hash=None,
                    verification_hash=None,
                ),
            )
        )


def test_invoice_issuance_without_settlement_cannot_create_payment_proof():
    payment, _, private_key, _, _ = service_with_secret_material()
    repo = InMemoryLNURLVerifyRepository({"pay2": payment})
    verify = LNURLVerifyService(repository=repo, sources=[])
    proof_service = LNURLPaymentProofService(
        verification_service=verify,
        config=LNURLPaymentProofConfig(issuer_private_key=private_key),
    )
    with pytest.raises(SettlementNotVerifiedError):
        asyncio.run(
            proof_service.issue_payment_proof(
                "pay2", payment_context="subscription", product_code="pro_pass"
            )
        )
