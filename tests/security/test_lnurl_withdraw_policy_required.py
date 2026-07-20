from __future__ import annotations

import asyncio
from urllib.parse import parse_qs, urlparse

from app.services.access.policy_context import AccessPolicyContext
from app.services.lnurl.encoding import decode_lnurl
from app.services.lnurl.url_safety import LNURLURLPolicy
from app.services.lnurl.verification_sources import test_bolt11 as make_test_bolt11
from app.services.lnurl.withdraw_callback_verifier import InMemorySensitiveInvoiceStore, LNURLWithdrawCallbackVerifier, LNURLWithdrawCallbackVerifierConfig
from app.services.lnurl.withdraw_policy import LNURLPayoutActorType, LNURLPayoutPolicyContext, LNURLPayoutPolicyStage, LNURLPayoutPurpose, LNURLWithdrawPolicyLimits, LNURLWithdrawPolicyService, OriginalPaymentRefundState
from app.services.lnurl.withdraw_request_service import LNURLWithdrawPurpose, LNURLWithdrawRequestConfig, LNURLWithdrawRequestService, PolicyDecision, PrincipalContext


def access(recovery: bool = False) -> AccessPolicyContext:
    return AccessPolicyContext(certificate_fingerprint="sha256:cert", pass_lookup_hash="hmac-sha256:pass", plan_code="enterprise_pass", effective_scopes={"refunds:subscription:create", "refunds:subscription:approve", "payouts:execute", "lnurl:withdraw:read"}, business_role="admin", metric_entitlements={"groups": []}, metadata={"recovery": recovery})


def policy_ctx(**kwargs) -> LNURLPayoutPolicyContext:
    base = dict(stage=LNURLPayoutPolicyStage.PAYMENT_EXECUTION, purpose=LNURLPayoutPurpose.SUBSCRIPTION_REFUND, actor_type=LNURLPayoutActorType.BUSINESS_ADMIN, amount_msat=50_000, access_context=access(), original_payment=OriginalPaymentRefundState("sha256:proof", None, None, 50_000), step_up_fresh=True, invoice_hash="sha256:invoice", payment_hash_hash="hmac-sha256:pay", payment_execution_id="exec1")
    base.update(kwargs)
    return LNURLPayoutPolicyContext(**base)


def test_valid_k1_or_callback_without_policy_approval_cannot_cause_payout() -> None:
    service = LNURLWithdrawPolicyService()
    result = service.enqueue_payment(policy_ctx(policy_approval_id=None))
    assert result.queued is False
    assert result.reason_code == "execution_requires_prior_policy_approval"


def test_recovery_browser_and_critical_policy_fail_closed() -> None:
    service = LNURLWithdrawPolicyService(limits=LNURLWithdrawPolicyLimits(global_max_msat=25_000_000, rolling_1h_max_msat=25_000_000, daily_max_msat=25_000_000))
    recovery = service.evaluate_payment_execution(policy_ctx(policy_approval_id="approval", recovery_only_session=True))
    assert recovery.decision == "recovery_locked"
    critical = service.evaluate_request_creation(policy_ctx(stage=LNURLPayoutPolicyStage.REQUEST_CREATION, purpose=LNURLPayoutPurpose.BUG_BOUNTY, actor_type=LNURLPayoutActorType.BUG_BOUNTY_REVIEWER, amount_msat=10_000_000, original_payment=None, browser_only_approval=True, step_up_fresh=True, human_intent_verified=True))
    assert critical.decision in {"step_up_required", "quorum_required"}


def test_callback_invoice_acceptance_policy_denial_blocks_invoice_received_state() -> None:
    async def run():
        withdraw = LNURLWithdrawRequestService(config=LNURLWithdrawRequestConfig(enabled=True))
        created = await withdraw.create_request(principal_context=PrincipalContext("lightning_wallet_principal", "hmac-sha256:p", "sha256:d", "sha256:s"), purpose=LNURLWithdrawPurpose.SUBSCRIPTION_REFUND, approved_amount_msat=50_000, source_reference="src", policy_decision=PolicyDecision("allow", "sha256:policy", "decision", 50_000))
        decoded = decode_lnurl(created.lnurl, policy=LNURLURLPolicy.service_owned_callback(domains={"bitcoin-bastion.com"}))
        k1 = parse_qs(urlparse(decoded.normalized_url).query)["k1"][0]
        policy = LNURLWithdrawPolicyService()
        verifier = LNURLWithdrawCallbackVerifier(request_service=withdraw, invoice_store=InMemorySensitiveInvoiceStore(), config=LNURLWithdrawCallbackVerifierConfig(server_pepper=withdraw.config.server_pepper, require_protected_invoice_store=False), policy_service=policy)
        invoice = make_test_bolt11(payment_hash="4" * 64, amount_msat=50_000, network="bitcoin-mainnet")
        result = await verifier.verify_callback(withdraw_id=created.withdraw_request_id, k1=k1, pr=invoice)
        assert result.accepted is False
        assert withdraw.repository.get_by_request_id(created.withdraw_request_id).status.value == "lnurl_issued"
    asyncio.run(run())
