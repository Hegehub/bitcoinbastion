from __future__ import annotations

import asyncio
from urllib.parse import parse_qs, urlparse

from app.services.access.policy_context import AccessPolicyContext
from app.services.lnurl.encoding import decode_lnurl
from app.services.lnurl.url_safety import LNURLURLPolicy
from app.services.lnurl.verification_sources import test_bolt11 as make_test_bolt11
from app.services.lnurl.withdraw_callback_verifier import InMemorySensitiveInvoiceStore, LNURLWithdrawCallbackVerifier, LNURLWithdrawCallbackVerifierConfig
from app.services.lnurl.withdraw_policy import FakeLNURLPayoutExecutor, LNURLPayoutActorType, LNURLPayoutPolicyContext, LNURLPayoutPolicyStage, LNURLPayoutPurpose, LNURLWithdrawPolicyService, OriginalPaymentRefundState
from app.services.lnurl.withdraw_request_service import LNURLWithdrawPurpose, LNURLWithdrawRequestConfig, LNURLWithdrawRequestService, PolicyDecision, PrincipalContext


def access():
    return AccessPolicyContext(certificate_fingerprint="sha256:c", pass_lookup_hash="hmac-sha256:p", plan_code="enterprise_pass", effective_scopes={"refunds:subscription:create", "refunds:subscription:approve", "payouts:execute", "lnurl:withdraw:read"}, business_role="admin", metric_entitlements={"groups": []})


def test_lnurl_refund_policy_to_fake_executor_flow() -> None:
    async def run():
        executor = FakeLNURLPayoutExecutor()
        policy = LNURLWithdrawPolicyService(executor=executor)
        original = OriginalPaymentRefundState("sha256:proof", "workspace", "principal", 50_000)
        create_decision = policy.evaluate_request_creation(LNURLPayoutPolicyContext(stage=LNURLPayoutPolicyStage.REQUEST_CREATION, purpose=LNURLPayoutPurpose.SUBSCRIPTION_REFUND, actor_type=LNURLPayoutActorType.BUSINESS_ADMIN, amount_msat=50_000, access_context=access(), original_payment=original, workspace_hash="workspace", business_role="admin", step_up_fresh=True))
        assert create_decision.allowed is True
        withdraw = LNURLWithdrawRequestService(config=LNURLWithdrawRequestConfig(enabled=True))
        created = await withdraw.create_request(principal_context=PrincipalContext("lightning_wallet_principal", "hmac-sha256:p", "sha256:d", "sha256:s"), purpose=LNURLWithdrawPurpose.SUBSCRIPTION_REFUND, approved_amount_msat=50_000, source_reference="source", policy_decision=PolicyDecision("allow", create_decision.policy_hash, "approval", 50_000))
        exposure = policy.evaluate_withdraw_exposure(LNURLPayoutPolicyContext(stage=LNURLPayoutPolicyStage.WITHDRAW_EXPOSURE, purpose=LNURLPayoutPurpose.SUBSCRIPTION_REFUND, actor_type=LNURLPayoutActorType.BUSINESS_ADMIN, amount_msat=50_000, access_context=access(), original_payment=original, withdraw_request=withdraw.repository.get_by_request_id(created.withdraw_request_id), workspace_hash="workspace", step_up_fresh=True))
        assert exposure.allowed is True
        decoded = decode_lnurl(created.lnurl, policy=LNURLURLPolicy.service_owned_callback(domains={"bitcoin-bastion.com"}))
        k1 = parse_qs(urlparse(decoded.normalized_url).query)["k1"][0]
        verifier = LNURLWithdrawCallbackVerifier(request_service=withdraw, invoice_store=InMemorySensitiveInvoiceStore(), config=LNURLWithdrawCallbackVerifierConfig(server_pepper=withdraw.config.server_pepper, require_protected_invoice_store=False))
        invoice = make_test_bolt11(payment_hash="7" * 64, amount_msat=50_000, network="bitcoin-mainnet")
        callback = await verifier.verify_callback(withdraw_id=created.withdraw_request_id, k1=k1, pr=invoice)
        assert callback.accepted is True
        record = withdraw.repository.get_by_request_id(created.withdraw_request_id)
        prepay = LNURLPayoutPolicyContext(stage=LNURLPayoutPolicyStage.PAYMENT_EXECUTION, purpose=LNURLPayoutPurpose.SUBSCRIPTION_REFUND, actor_type=LNURLPayoutActorType.BUSINESS_ADMIN, amount_msat=50_000, access_context=access(), original_payment=original, withdraw_request=record, invoice_hash=record.invoice_hash, payment_hash_hash=record.payment_hash_hash, workspace_hash="workspace", step_up_fresh=True, policy_approval_id="approval", payment_execution_id="exec")
        queued = policy.enqueue_payment(prepay)
        assert queued.queued is True
        policy.record_paid(record.payment_hash_hash, execution_id="exec")
        duplicate = policy.enqueue_payment(prepay)
        assert len(executor.enqueued) == 1
        assert duplicate.queued is False
        assert any(e["event_type"] == "lnurl_payout_paid" for e in policy.audit_sink.events)
    asyncio.run(run())
