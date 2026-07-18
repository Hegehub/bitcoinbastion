from __future__ import annotations

import asyncio
import base64
import hashlib
from datetime import UTC, datetime

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from app.domain.lnurl.payment_proofs import LNURLPaymentContext
from app.services.lnurl.payment_proof import (
    InMemoryLNURLPaymentProofRepository,
    LNURLPaymentProofConfig,
    LNURLPaymentProofService,
)
from app.services.lnurl.verification_sources import (
    LNURLSettlementState,
    LNURLVerificationSourceType,
    SettlementSourceResult,
    test_bolt11 as make_test_bolt11,
)
from app.services.lnurl.verify import InMemoryLNURLVerifyRepository, LNURLPaymentForVerification, LNURLVerifyService


class Provider:
    source_type = LNURLVerificationSourceType.TRUSTED_PAYMENT_PROVIDER

    async def verify(self, payment):
        return self.result


def keys():
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


def test_lnurl_payment_proof_flow_after_verified_settlement_no_entitlement_issued():
    preimage = b"i" * 32
    payment_hash = hashlib.sha256(preimage).hexdigest()
    invoice = make_test_bolt11(
        payment_hash=payment_hash,
        amount_msat=2500,
        network="lightning-mainnet",
        timestamp=datetime.now(UTC),
        description_hash="sha256:metadata",
    )
    payment = LNURLPaymentForVerification(
        "pay1",
        "lpay_1",
        invoice,
        2500,
        payment_hash,
        "lightning-mainnet",
        metadata_hash="sha256:metadata",
        plan_code="pro_pass",
    )
    provider = Provider()
    provider.result = SettlementSourceResult(
        LNURLVerificationSourceType.TRUSTED_PAYMENT_PROVIDER,
        False,
        LNURLSettlementState.PENDING,
        invoice=invoice,
    )
    verify = LNURLVerifyService(repository=InMemoryLNURLVerifyRepository({"pay1": payment}), sources=[provider])
    pending = asyncio.run(verify.verify_payment("pay1"))
    assert not pending.eligible_for_payment_proof
    provider.result = SettlementSourceResult(
        LNURLVerificationSourceType.TRUSTED_PAYMENT_PROVIDER,
        True,
        LNURLSettlementState.SETTLED,
        invoice=invoice,
        preimage=preimage.hex(),
    )
    settled = asyncio.run(verify.verify_payment("pay1", force_refresh=True))
    assert settled.eligible_for_payment_proof
    private_key, public_key = keys()
    events = []
    proof_service = LNURLPaymentProofService(
        verification_service=verify,
        repository=InMemoryLNURLPaymentProofRepository(),
        config=LNURLPaymentProofConfig(issuer_private_key=private_key, issuer_public_key=public_key),
        event_sink=events.append,
    )
    proof = asyncio.run(
        proof_service.issue_payment_proof(
            "pay1", payment_context=LNURLPaymentContext.SUBSCRIPTION, product_code="pro_pass"
        )
    )
    response = proof.safe_response()
    assert response["proof_id"].startswith("lpp_")
    assert proof_service.verify_payment_proof_integrity(proof)
    assert events and events[0].safe_payload()["proof_id"] == proof.proof_id
    assert proof_service.repository.count_entitlements() == 0
    assert invoice not in repr(response)
    assert preimage.hex() not in repr(response)
