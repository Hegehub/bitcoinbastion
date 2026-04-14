import json

from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from app.db.models.treasury import PolicyExecutionLog
from app.db.repositories.policy_repository import PolicyExecutionRepository, PolicyRepository
from app.schemas.policy import (
    PolicyCatalogOut,
    PolicyCheckRequest,
    PolicyCheckResponse,
    PolicyExecutionLogOut,
    PolicyRuleOut,
)


class TreasuryPolicyService:
    def _evaluate_stateless(self, payload: PolicyCheckRequest) -> PolicyCheckResponse:
        violations: list[str] = []
        if payload.wallet_health_score < 60:
            violations.append("Wallet health is below minimum threshold (60).")
        if payload.transaction_amount_sats > 10_000_000:
            violations.append("Transaction exceeds single-approval policy limit (10000000 sats).")

        allowed = not violations
        next_actions = (
            ["Proceed with PSBT creation and designated signer quorum workflow."]
            if allowed
            else [
                "Escalate to treasury operator review.",
                "Record justification in policy execution log.",
            ]
        )
        return PolicyCheckResponse(
            allowed=allowed,
            violations=violations,
            next_actions=next_actions,
            evaluated_policy=payload.policy_name,
            applied_rules=[
                PolicyRuleOut(rule_key="min_wallet_health_score", rule_value="60", severity="error"),
                PolicyRuleOut(rule_key="max_single_tx_sats", rule_value="10000000", severity="error"),
            ],
        )

    def evaluate(self, db: Session, payload: PolicyCheckRequest) -> PolicyCheckResponse:
        repo = PolicyRepository(db)
        policy = repo.get_or_create_policy(payload.policy_name)
        rules = repo.list_rules(policy.id)

        threshold_min_health = policy.min_wallet_health_score
        threshold_max_tx = policy.max_single_tx_sats
        for rule in rules:
            if rule.rule_key == "min_wallet_health_score":
                threshold_min_health = int(rule.rule_value)
            if rule.rule_key == "max_single_tx_sats":
                threshold_max_tx = int(rule.rule_value)

        violations: list[str] = []
        if payload.wallet_health_score < threshold_min_health:
            violations.append(
                f"Wallet health is below minimum threshold ({threshold_min_health})."
            )
        if payload.transaction_amount_sats > threshold_max_tx:
            violations.append(
                f"Transaction exceeds single-approval policy limit ({threshold_max_tx} sats)."
            )

        allowed = not violations
        next_actions = (
            ["Proceed with PSBT creation and designated signer quorum workflow."]
            if allowed
            else [
                "Escalate to treasury operator review.",
                "Record justification in policy execution log.",
            ]
        )
        return PolicyCheckResponse(
            allowed=allowed,
            violations=violations,
            next_actions=next_actions,
            evaluated_policy=policy.name,
            applied_rules=[
                PolicyRuleOut(rule_key=rule.rule_key, rule_value=rule.rule_value, severity=rule.severity)
                for rule in rules
            ],
        )

    def evaluate_and_log(self, db: Session, payload: PolicyCheckRequest) -> PolicyCheckResponse:
        try:
            result = self.evaluate(db=db, payload=payload)
        except OperationalError:
            db.rollback()
            result = self._evaluate_stateless(payload)

        repo = PolicyExecutionRepository(db)
        try:
            repo.create(
                policy_name=payload.policy_name,
                wallet_health_score=int(payload.wallet_health_score),
                transaction_amount_sats=payload.transaction_amount_sats,
                allowed=result.allowed,
                violations=result.violations,
                next_actions=result.next_actions,
            )
        except OperationalError:
            db.rollback()
        return result

    def list_executions(self, db: Session, limit: int, offset: int) -> list[PolicyExecutionLogOut]:
        repo = PolicyExecutionRepository(db)
        try:
            return [self._to_schema(item) for item in repo.list_recent(limit=limit, offset=offset)]
        except OperationalError:
            db.rollback()
            return []

    def list_catalog(self, db: Session) -> list[PolicyCatalogOut]:
        repo = PolicyRepository(db)
        try:
            items = repo.list_policies()
            return [
                PolicyCatalogOut(
                    name=item.name,
                    min_wallet_health_score=item.min_wallet_health_score,
                    max_single_tx_sats=item.max_single_tx_sats,
                )
                for item in items
            ]
        except OperationalError:
            db.rollback()
            return []

    def _to_schema(self, item: PolicyExecutionLog) -> PolicyExecutionLogOut:
        return PolicyExecutionLogOut(
            id=item.id,
            policy_name=item.policy_name,
            wallet_health_score=item.wallet_health_score,
            transaction_amount_sats=item.transaction_amount_sats,
            allowed=item.allowed,
            violations=json.loads(item.violations_json),
            next_actions=json.loads(item.next_actions_json),
            executed_at=item.executed_at,
        )
