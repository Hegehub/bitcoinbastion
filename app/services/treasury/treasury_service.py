import json

from app.db.models.treasury import TreasuryRequest
from app.db.repositories.audit_repository import AuditRepository
from app.db.repositories.treasury_repository import TreasuryRepository
from app.schemas.policy import PolicyCheckRequest
from app.schemas.treasury import (
    TreasuryApprovalActionIn,
    TreasuryApprovalOut,
    TreasuryRejectActionIn,
    TreasuryRejectOut,
    TreasuryRequestIn,
)
from app.services.admin.audit_service import AuditService
from app.services.policy.policy_service import TreasuryPolicyService


class TreasuryService:
    def __init__(self, repo: TreasuryRepository) -> None:
        self.repo = repo
        self.policy_service = TreasuryPolicyService()
        self.audit_service = AuditService(AuditRepository(repo.db))

    def create_request(self, payload: TreasuryRequestIn, requested_by: int | None = None) -> TreasuryRequest:
        policy_result = self.policy_service.evaluate_and_log(
            db=self.repo.db,
            payload=PolicyCheckRequest(
                policy_name=payload.policy_name,
                wallet_health_score=payload.wallet_health_score,
                transaction_amount_sats=payload.amount_sats,
                required_approvals=1,
            ),
        )

        status = "pending" if policy_result.allowed else "needs_review"
        required_approvals = 1 if policy_result.allowed else 2

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

        request.approved_by_json = json.dumps(approved_by)

        if policy_result.allowed and len(approved_by) >= request.required_approvals:
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

        return TreasuryRejectOut(request_id=saved.id, status=saved.status, note=payload.note)

    def list_requests(self, limit: int, offset: int, status: str | None = None) -> list[TreasuryRequest]:
        return self.repo.list(limit=limit, offset=offset, status=status)

    def list_pending_approvals(self, limit: int, offset: int) -> list[TreasuryRequest]:
        return self.repo.list_pending_approvals(limit=limit, offset=offset)

    def count_requests(self, status: str | None = None) -> int:
        return self.repo.count(status=status)

    def count_pending_approvals(self) -> int:
        return self.repo.count_pending_approvals()
