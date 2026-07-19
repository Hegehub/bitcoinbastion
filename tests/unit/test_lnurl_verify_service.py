# ruff: noqa: E701,E702
from __future__ import annotations
import asyncio
import hashlib
import pytest
from datetime import UTC, datetime
from dataclasses import replace

from app.services.lnurl.verify import (
    LNURLPaymentForVerification,
    LNURLVerifyService,
    InMemoryLNURLVerifyRepository,
    LUD21VerificationSource,
    LNURLVerifyConfig,
)
from app.services.lnurl.verification_sources import (
    LNURLSettlementState,
    LNURLVerificationSourceType,
    SettlementSourceResult,
    test_bolt11 as make_test_bolt11,
)


class Source:
    def __init__(self, st, result):
        self.source_type = st
        self.result = result

    async def verify(self, payment):
        return self.result


def payment(plan="lite_pass", ph=None):
    ph = ph or hashlib.sha256(b"x" * 32).hexdigest()
    inv = make_test_bolt11(
        payment_hash=ph,
        amount_msat=1000,
        network="testnet",
        timestamp=datetime.now(UTC),
        description_hash="sha256:meta",
    )
    return LNURLPaymentForVerification(
        "pay1",
        "req1",
        inv,
        1000,
        ph,
        "testnet",
        metadata_hash="sha256:meta",
        plan_code=plan,
        verify_url="https://example.com/verify",
    )


def test_internal_node_confirms_settled_and_idempotent():
    p = payment()
    repo = InMemoryLNURLVerifyRepository({"pay1": p})
    src = Source(
        LNURLVerificationSourceType.INTERNAL_LIGHTNING_NODE,
        SettlementSourceResult(
            LNURLVerificationSourceType.INTERNAL_LIGHTNING_NODE,
            True,
            LNURLSettlementState.SETTLED,
            invoice=p.bolt11,
        ),
    )
    svc = LNURLVerifyService(repository=repo, sources=[src])
    r1 = asyncio.run(svc.verify_payment("pay1"))
    r2 = asyncio.run(svc.verify_payment("pay1"))
    assert r1.eligible_for_payment_proof and r1.confidence == "internally_confirmed"
    assert r2.verified_at == r1.verified_at
    assert repo.count_entitlements() == repo.count_payment_proofs() == 0


def test_provider_confirms_settled():
    p = payment()
    repo = InMemoryLNURLVerifyRepository({"pay1": p})
    svc = LNURLVerifyService(
        repository=repo,
        sources=[
            Source(
                LNURLVerificationSourceType.TRUSTED_PAYMENT_PROVIDER,
                SettlementSourceResult(
                    LNURLVerificationSourceType.TRUSTED_PAYMENT_PROVIDER,
                    True,
                    LNURLSettlementState.SETTLED,
                    invoice=p.bolt11,
                ),
            )
        ],
    )
    assert (asyncio.run(svc.verify_payment("pay1"))).confidence == "provider_confirmed"


def test_lud21_settled_with_valid_preimage_lite_allowed():
    pre = b"a" * 32
    ph = hashlib.sha256(pre).hexdigest()
    p = payment(ph=ph)
    repo = InMemoryLNURLVerifyRepository({"pay1": p})

    async def fetch(url, config):
        return {"status": "OK", "settled": True, "preimage": pre.hex(), "pr": p.bolt11}

    svc = LNURLVerifyService(
        repository=repo,
        sources=[
            LUD21VerificationSource(
                fetch_json=fetch,
                config=LNURLVerifyConfig(trusted_verify_domains=frozenset({"example.com"})),
            )
        ],
    )
    r = asyncio.run(svc.verify_payment("pay1"))
    assert r.confidence == "remote_only" and r.preimage_verified and r.eligible_for_payment_proof
    assert pre.hex() not in repr(repo.records("pay1"))


def test_pending_and_expired_states_not_eligible():
    p = payment()
    repo = InMemoryLNURLVerifyRepository({"pay1": p})
    svc = LNURLVerifyService(
        repository=repo,
        sources=[
            Source(
                LNURLVerificationSourceType.TRUSTED_PAYMENT_PROVIDER,
                SettlementSourceResult(
                    LNURLVerificationSourceType.TRUSTED_PAYMENT_PROVIDER,
                    False,
                    LNURLSettlementState.PENDING,
                    invoice=p.bolt11,
                ),
            )
        ],
    )
    assert not (asyncio.run(svc.verify_payment("pay1"))).eligible_for_payment_proof


@pytest.mark.parametrize("mut", ["invoice", "hash", "amount", "network", "metadata"])
def test_invoice_integrity_mismatches_rejected(mut):
    p = payment()
    other = p.bolt11
    if mut == "invoice":
        other = make_test_bolt11(
            payment_hash=p.payment_hash,
            amount_msat=1000,
            network="testnet",
            description_hash="sha256:meta",
            expiry_seconds=901,
        )
    if mut == "hash":
        other = make_test_bolt11(
            payment_hash="0" * 64,
            amount_msat=1000,
            network="testnet",
            description_hash="sha256:meta",
        )
    if mut == "amount":
        other = make_test_bolt11(
            payment_hash=p.payment_hash,
            amount_msat=2000,
            network="testnet",
            description_hash="sha256:meta",
        )
    if mut == "network":
        other = make_test_bolt11(
            payment_hash=p.payment_hash,
            amount_msat=1000,
            network="bitcoin",
            description_hash="sha256:meta",
        )
    if mut == "metadata":
        other = make_test_bolt11(
            payment_hash=p.payment_hash,
            amount_msat=1000,
            network="testnet",
            description_hash="sha256:other",
        )
    repo = InMemoryLNURLVerifyRepository({"pay1": p})
    svc = LNURLVerifyService(
        repository=repo,
        sources=[
            Source(
                LNURLVerificationSourceType.INTERNAL_LIGHTNING_NODE,
                SettlementSourceResult(
                    LNURLVerificationSourceType.INTERNAL_LIGHTNING_NODE,
                    True,
                    LNURLSettlementState.SETTLED,
                    invoice=other,
                ),
            )
        ],
    )
    r = asyncio.run(svc.verify_payment("pay1", force_refresh=True))
    assert r.status == "inconsistent" and not r.eligible_for_payment_proof


@pytest.mark.parametrize("pre", ["zz", "00", (b"b" * 32).hex()])
def test_preimage_malformed_length_or_mismatch_rejected(pre):
    p = payment()
    repo = InMemoryLNURLVerifyRepository({"pay1": p})
    svc = LNURLVerifyService(
        repository=repo,
        sources=[
            Source(
                LNURLVerificationSourceType.INTERNAL_LIGHTNING_NODE,
                SettlementSourceResult(
                    LNURLVerificationSourceType.INTERNAL_LIGHTNING_NODE,
                    True,
                    LNURLSettlementState.SETTLED,
                    invoice=p.bolt11,
                    preimage=pre,
                ),
            )
        ],
    )
    assert (asyncio.run(svc.verify_payment("pay1"))).status == "inconsistent"


def test_remote_url_ssrf_localhost_rejected():
    p = replace(payment(), verify_url="http://127.0.0.1/latest/meta-data")
    repo = InMemoryLNURLVerifyRepository({"pay1": p})

    async def fetch(url, config):
        raise AssertionError("must not fetch")

    svc = LNURLVerifyService(repository=repo, sources=[LUD21VerificationSource(fetch_json=fetch)])
    r = asyncio.run(svc.verify_payment("pay1"))
    assert r.status == "verification_unavailable" or not r.eligible_for_payment_proof


def test_business_remote_only_denied_by_default():
    pre = b"a" * 32
    ph = hashlib.sha256(pre).hexdigest()
    p = payment(plan="business", ph=ph)
    repo = InMemoryLNURLVerifyRepository({"pay1": p})

    async def fetch(url, config):
        return {"status": "OK", "settled": True, "preimage": pre.hex(), "pr": p.bolt11}

    svc = LNURLVerifyService(
        repository=repo,
        sources=[
            LUD21VerificationSource(
                fetch_json=fetch,
                config=LNURLVerifyConfig(trusted_verify_domains=frozenset({"example.com"})),
            )
        ],
    )
    assert not (asyncio.run(svc.verify_payment("pay1"))).eligible_for_payment_proof


def test_dual_confirmation_confidence():
    p = payment()
    repo = InMemoryLNURLVerifyRepository({"pay1": p})
    sources = [
        Source(
            LNURLVerificationSourceType.INTERNAL_LIGHTNING_NODE,
            SettlementSourceResult(
                LNURLVerificationSourceType.INTERNAL_LIGHTNING_NODE,
                True,
                LNURLSettlementState.SETTLED,
                invoice=p.bolt11,
            ),
        ),
        Source(
            LNURLVerificationSourceType.TRUSTED_PAYMENT_PROVIDER,
            SettlementSourceResult(
                LNURLVerificationSourceType.TRUSTED_PAYMENT_PROVIDER,
                True,
                LNURLSettlementState.SETTLED,
                invoice=p.bolt11,
            ),
        ),
    ]
    r = asyncio.run(LNURLVerifyService(repository=repo, sources=sources).verify_payment("pay1"))
    assert r.confidence == "dual_confirmed"
