# ruff: noqa: E701,E702
from __future__ import annotations
import asyncio
import hashlib
from datetime import UTC, datetime

from app.services.lnurl.verify import (
    InMemoryLNURLVerifyRepository,
    LNURLPaymentForVerification,
    LNURLVerifyService,
)
from app.services.lnurl.verification_sources import (
    LNURLSettlementState,
    LNURLVerificationSourceType,
    SettlementSourceResult,
    test_bolt11 as make_test_bolt11,
)


class MutableProvider:
    source_type = LNURLVerificationSourceType.TRUSTED_PAYMENT_PROVIDER

    def __init__(self, result):
        self.result = result

    async def verify(self, payment):
        return self.result


def make_payment(pre=b"s" * 32):
    ph = hashlib.sha256(pre).hexdigest()
    inv = make_test_bolt11(
        payment_hash=ph,
        amount_msat=2500,
        network="testnet",
        timestamp=datetime.now(UTC),
        description_hash="sha256:meta",
    )
    return pre, LNURLPaymentForVerification(
        "pay1",
        "req1",
        inv,
        2500,
        ph,
        "testnet",
        metadata_hash="sha256:meta",
        provider_invoice_id_hash="sha256:provider",
        plan_code="lite_pass",
    )


def test_lnurl_verify_settlement_flow_no_proof_or_entitlement_created():
    pre, p = make_payment()
    repo = InMemoryLNURLVerifyRepository({"pay1": p})
    provider = MutableProvider(
        SettlementSourceResult(
            LNURLVerificationSourceType.TRUSTED_PAYMENT_PROVIDER,
            False,
            LNURLSettlementState.PENDING,
            invoice=p.bolt11,
        )
    )
    svc = LNURLVerifyService(repository=repo, sources=[provider])
    pending = asyncio.run(svc.verify_payment("pay1"))
    assert pending.status == "pending" and not pending.eligible_for_payment_proof
    provider.result = SettlementSourceResult(
        LNURLVerificationSourceType.TRUSTED_PAYMENT_PROVIDER,
        True,
        LNURLSettlementState.SETTLED,
        invoice=p.bolt11,
        preimage=pre.hex(),
        provider_event_id="evt1",
    )
    settled = asyncio.run(svc.verify_payment("pay1", force_refresh=True))
    assert settled.status == "settled" and settled.eligible_for_payment_proof
    assert (
        settled.payment_hash_matches
        and settled.amount_matches
        and settled.network_matches
        and settled.preimage_verified
    )
    assert repo.count_payment_proofs() == 0 and repo.count_entitlements() == 0
    assert svc.get_verified_settlement("pay1").eligible_for_payment_proof


def test_inconsistent_source_blocks_payment_proof_eligibility():
    _, p = make_payment()
    wrong = make_test_bolt11(payment_hash="0" * 64, amount_msat=2500, network="testnet")

    class Internal:
        source_type = LNURLVerificationSourceType.INTERNAL_LIGHTNING_NODE

        async def verify(self, payment):
            return SettlementSourceResult(
                self.source_type, False, LNURLSettlementState.FAILED, invoice=wrong
            )

    class Remote:
        source_type = LNURLVerificationSourceType.LUD21_VERIFY_URL

        async def verify(self, payment):
            return SettlementSourceResult(
                self.source_type, True, LNURLSettlementState.SETTLED, invoice=p.bolt11
            )

    repo = InMemoryLNURLVerifyRepository({"pay1": p})
    result = asyncio.run(
        LNURLVerifyService(repository=repo, sources=[Internal(), Remote()]).verify_payment("pay1")
    )
    assert result.status in {"failed", "inconsistent"}
    assert not result.eligible_for_payment_proof
    assert repo.count_payment_proofs() == 0 and repo.count_entitlements() == 0
