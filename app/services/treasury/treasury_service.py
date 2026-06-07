import json

from app.db.models.treasury import TreasuryRequest
from app.db.repositories.audit_repository import AuditRepository
from app.db.repositories.treasury_repository import TreasuryRepository
from app.schemas.policy import PolicyCheckRequest
from app.schemas.fees import FeeRecommendationRequest
from app.schemas.treasury import (
    TreasuryApprovalActionIn,
    TreasuryApprovalOut,
    TreasuryRejectActionIn,
    TreasuryRejectOut,
    TreasuryRequestIn,
)
from app.services.admin.audit_service import AuditService
from app.services.analytics.fee_service import FeeAnalyticsService
from app.services.policy.policy_service import TreasuryPolicyService
from app.services.blockchain.chain_state_service import ChainStateService
from app.services.blockchain.chain_state_service import ChainStateEvaluation
from app.services.explainability.contract import build_audit_packet
from app.services.events.domain_event_publisher import publish_domain_event


class TreasuryService:
    def __init__(self, repo: TreasuryRepository) -> None:
        self.repo = repo
        self.policy_service = TreasuryPolicyService()
        self.audit_service = AuditService(AuditRepository(repo.db))

    def _publish_treasury_event(
        self,
        event_type: str,
        request: TreasuryRequest,
        *,
        actor_id: int | None = None,
        policy_result: object | None = None,
        approval_required: bool | None = None,
        idempotency_suffix: str,
    ) -> None:
        policy_payload: dict[str, object] = {}
        try:
            policy_payload = json.loads(request.policy_snapshot_json or "{}")
        except json.JSONDecodeError:
            policy_payload = {}
        if policy_result is not None:
            policy_payload.update(
                {
                    "policy_name": getattr(policy_result, "evaluated_policy", policy_payload.get("policy_name", "unknown")),
                    "allowed": getattr(policy_result, "allowed", policy_payload.get("allowed")),
                    "violations": getattr(policy_result, "violations", policy_payload.get("violations", [])),
                    "next_actions": getattr(policy_result, "next_actions", policy_payload.get("next_actions", [])),
                }
            )
        publish_domain_event(
            self.repo.db,
            event_type,
            {
                "request_id": request.id,
                "status": request.status,
                "requested_by": request.requested_by,
                "amount": request.amount_sats,
                "asset": "BTC",
                "policy_result": policy_payload,
                "approval_required": approval_required if approval_required is not None else request.status in {"pending", "needs_review", "awaiting_approval"},
                "approver_id": actor_id,
                "created_at": request.created_at.isoformat() if request.created_at else None,
                "updated_at": request.updated_at.isoformat() if request.updated_at else None,
                "limitations": [
                    "Treasury events are workflow events, not proof of fund movement.",
                    "No transaction signing or broadcasting is performed by event publication.",
                    "Operator approval is required before external treasury workflows proceed.",
                ],
                "no_custody": True,
                "no_auto_execution": True,
            },
            aggregate_type="treasury_request",
            aggregate_id=request.id,
            source="treasury_service",
            actor_id=actor_id,
            idempotency_key=f"{event_type}:treasury_request:{request.id}:{idempotency_suffix}",
        )

    @staticmethod
    def _chain_state_for_treasury(
        *,
        wallet_health_score: float,
        amount_sats: int,
        data_source: str = "repository_fallback",
    ) -> ChainStateEvaluation:
        observed = 900_000
        if amount_sats >= 10_000_000 or wallet_health_score < 50:
            tip = observed
        elif wallet_health_score < 70:
            tip = observed + 2
        else:
            tip = observed + 6
        return ChainStateService().evaluate(
            tip_height=tip,
            observed_block_height=observed,
            headers_height=tip,
            data_source=data_source,
        )

    def create_request(self, payload: TreasuryRequestIn, requested_by: int | None = None) -> TreasuryRequest:
        fee_model = FeeAnalyticsService().recommend(
            FeeRecommendationRequest(
                mempool_congestion=min(1.0, max(0.0, 1.0 - payload.wallet_health_score)),
                target_blocks=3,
            )
        )
        policy_result = self.policy_service.evaluate_and_log(
            db=self.repo.db,
            payload=PolicyCheckRequest(
                policy_name=payload.policy_name,
                wallet_health_score=payload.wallet_health_score,
                transaction_amount_sats=payload.amount_sats,
                required_approvals=1,
            ),
        )

        chain_state = self._chain_state_for_treasury(
            wallet_health_score=payload.wallet_health_score,
            amount_sats=payload.amount_sats,
        )

        status = "pending" if policy_result.allowed else "needs_review"
        required_approvals = 1 if policy_result.allowed else 2
        chain_warnings: list[str] = []
        if chain_state.reorg_risk_score >= 0.55:
            chain_warnings.append("Elevated chain reorg risk detected; increase confirmation threshold before emergency spend execution.")
            status = "needs_review"
            required_approvals = max(required_approvals, 2)
        elif chain_state.finality_band == "moderate":
            chain_warnings.append("Moderate finality context; confirm additional blocks before irreversible spend.")

        request = TreasuryRequest(
            title=payload.title,
            amount_sats=payload.amount_sats,
            destination_reference=payload.destination_reference,
            requested_by=requested_by,
            status=status,
            required_approvals=required_approvals,
            policy_snapshot_json=json.dumps(
                {
                    "policy_name": policy_result.evaluated_policy,
                    "allowed": policy_result.allowed,
                    "violations": policy_result.violations,
                    "next_actions": policy_result.next_actions,
                    "applied_rules": [rule.model_dump() for rule in policy_result.applied_rules],
                    "wallet_health_score": payload.wallet_health_score,
                    "chain_state_context": {
                        "finality_band": chain_state.finality_band,
                        "finality_score": chain_state.finality_score,
                        "reorg_risk_score": chain_state.reorg_risk_score,
                        "confidence_score": chain_state.confidence_score,
                        "freshness": chain_state.freshness,
                        "warnings": chain_warnings,
                    },
                    "audit_packet": build_audit_packet(
                        packet_type="treasury_warning" if chain_warnings else "treasury_review",
                        evidence_refs=[f"policy:{policy_result.evaluated_policy}", "chain_state_context"],
                        source_quality={
                            "source_type": chain_state.freshness.get("source_type", "runtime"),
                            "is_fallback": chain_state.freshness.get("is_fallback", False),
                            "freshness": chain_state.freshness,
                        },
                        confidence=chain_state.confidence_score,
                        transformations=["treasury_policy_eval", "chain_state_risk_adjustment"],
                        policy_context={"violations": policy_result.violations},
                        recommendation_rationale="Increase approval rigor when reorg risk or policy violations are elevated.",
                        lineage=[
                            {"domain": "policy", "reference": policy_result.evaluated_policy},
                            {"domain": "treasury", "reference": payload.policy_name},
                        ],
                    ),
                    "fee_risk_context": {
                        "congestion_state": fee_model.congestion_state,
                        "suggested_fee_rate_sat_vb": fee_model.suggested_fee_rate_sat_vb,
                        "high_fee_scenario_sat_vb": fee_model.high_fee_scenario_sat_vb,
                    },
                }
            ),
        )
        created = self.repo.create(request)
        self.audit_service.record_action(
            action="treasury.request.create",
            resource_type="treasury_request",
            resource_id=str(created.id),
            actor_user_id=requested_by,
            after={"status": created.status, "required_approvals": created.required_approvals},
        )
        self._publish_treasury_event(
            "treasury.request.created",
            created,
            actor_id=requested_by,
            policy_result=policy_result,
            approval_required=created.status in {"pending", "needs_review", "awaiting_approval"},
            idempotency_suffix="created",
        )
        if created.status in {"pending", "needs_review", "awaiting_approval"}:
            self._publish_treasury_event(
                "treasury.approval.required",
                created,
                actor_id=requested_by,
                policy_result=policy_result,
                approval_required=True,
                idempotency_suffix="approval_required",
            )
        if not policy_result.allowed:
            self._publish_treasury_event(
                "treasury.policy.failed",
                created,
                actor_id=requested_by,
                policy_result=policy_result,
                approval_required=True,
                idempotency_suffix="policy_failed",
            )
        return created

    def approve_request(self, request_id: int, approver_user_id: int, payload: TreasuryApprovalActionIn) -> TreasuryApprovalOut:
        request = self.repo.get(request_id)
        if request is None:
            raise ValueError("Treasury request not found")

        before_status = request.status

        try:
            approved_by = json.loads(request.approved_by_json or "[]")
            if not isinstance(approved_by, list):
                approved_by = []
        except json.JSONDecodeError:
            approved_by = []

        if approver_user_id not in approved_by:
            approved_by.append(approver_user_id)

        policy_result = self.policy_service.evaluate_and_log(
            db=self.repo.db,
            payload=PolicyCheckRequest(
                policy_name=payload.policy_name,
                wallet_health_score=payload.wallet_health_score,
                transaction_amount_sats=request.amount_sats,
                required_approvals=request.required_approvals,
            ),
        )
        chain_state = self._chain_state_for_treasury(
            wallet_health_score=payload.wallet_health_score,
            amount_sats=request.amount_sats,
            data_source="provider_probe",
        )

        request.approved_by_json = json.dumps(approved_by)

        if chain_state.reorg_risk_score >= 0.65:
            request.status = "needs_review"
        elif policy_result.allowed and len(approved_by) >= request.required_approvals:
            request.status = "approved"
        elif policy_result.allowed:
            request.status = "awaiting_approval"
        else:
            request.status = "needs_review"

        snapshot = {
            "policy_name": policy_result.evaluated_policy,
            "allowed": policy_result.allowed,
            "violations": policy_result.violations,
            "next_actions": policy_result.next_actions,
            "approval_note": payload.note,
            "approved_count": len(approved_by),
            "required_approvals": request.required_approvals,
            "chain_state_context": {
                "finality_band": chain_state.finality_band,
                "reorg_risk_score": chain_state.reorg_risk_score,
                "confidence_score": chain_state.confidence_score,
                "freshness": chain_state.freshness,
                "warning": "Human review required for elevated reorg risk." if chain_state.reorg_risk_score >= 0.65 else "",
            },
        }
        request.policy_snapshot_json = json.dumps(snapshot)
        saved = self.repo.update(request)
        self.audit_service.record_action(
            action="treasury.request.approve",
            resource_type="treasury_request",
            resource_id=str(saved.id),
            actor_user_id=approver_user_id,
            before={"status": before_status},
            after={"status": saved.status, "approved_count": len(approved_by)},
        )
        if saved.status == "approved":
            self._publish_treasury_event(
                "treasury.request.approved",
                saved,
                actor_id=approver_user_id,
                policy_result=policy_result,
                approval_required=False,
                idempotency_suffix="approved",
            )
        elif not policy_result.allowed:
            self._publish_treasury_event(
                "treasury.policy.failed",
                saved,
                actor_id=approver_user_id,
                policy_result=policy_result,
                approval_required=True,
                idempotency_suffix="policy_failed",
            )

        return TreasuryApprovalOut(
            request_id=saved.id,
            status=saved.status,
            approved_count=len(approved_by),
            required_approvals=saved.required_approvals,
            allowed_by_policy=policy_result.allowed,
            violations=policy_result.violations,
        )


    def reject_request(self, request_id: int, actor_user_id: int, payload: TreasuryRejectActionIn) -> TreasuryRejectOut:
        request = self.repo.get(request_id)
        if request is None:
            raise ValueError("Treasury request not found")

        before_status = request.status
        request.status = "rejected"
        request.policy_snapshot_json = json.dumps({"rejection_note": payload.note, "actor_user_id": actor_user_id})
        saved = self.repo.update(request)

        self.audit_service.record_action(
            action="treasury.request.reject",
            resource_type="treasury_request",
            resource_id=str(saved.id),
            actor_user_id=actor_user_id,
            before={"status": before_status},
            after={"status": saved.status},
        )
        self._publish_treasury_event(
            "treasury.request.rejected",
            saved,
            actor_id=actor_user_id,
            approval_required=False,
            idempotency_suffix="rejected",
        )

        return TreasuryRejectOut(request_id=saved.id, status=saved.status, note=payload.note)

    def list_requests(self, limit: int, offset: int, status: str | None = None) -> list[TreasuryRequest]:
        return self.repo.list(limit=limit, offset=offset, status=status)

    def list_pending_approvals(self, limit: int, offset: int) -> list[TreasuryRequest]:
        return self.repo.list_pending_approvals(limit=limit, offset=offset)

    def count_requests(self, status: str | None = None) -> int:
        return self.repo.count(status=status)

    def count_pending_approvals(self) -> int:
        return self.repo.count_pending_approvals()
