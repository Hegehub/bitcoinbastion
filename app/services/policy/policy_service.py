import json

from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from app.db.models.treasury import PolicyExecutionLog
from app.db.repositories.policy_repository import PolicyExecutionRepository, PolicyRepository
from app.schemas.policy import (
    PolicyCatalogOut,
    PolicyCatalogUpsertIn,
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
        if payload.required_approvals < 1:
            violations.append("Required approvals must be at least 1.")

        allowed = not violations
        next_actions = self._next_actions(allowed)
        return PolicyCheckResponse(
            allowed=allowed,
            violations=violations,
            next_actions=next_actions,
            evaluated_policy=payload.policy_name,
            applied_rules=[
                PolicyRuleOut(rule_key="min_wallet_health_score", rule_value="gte:60", severity="error"),
                PolicyRuleOut(rule_key="max_single_tx_sats", rule_value="lte:10000000", severity="error"),
                PolicyRuleOut(rule_key="min_required_approvals", rule_value="gte:1", severity="error"),
            ],
        )

    def evaluate(self, db: Session, payload: PolicyCheckRequest) -> PolicyCheckResponse:
        repo = PolicyRepository(db)
        policy = repo.get_or_create_policy(payload.policy_name)
        rules = repo.list_rules(policy.id)

        context = {
            "wallet_health_score": float(payload.wallet_health_score),
            "transaction_amount_sats": float(payload.transaction_amount_sats),
            "required_approvals": float(payload.required_approvals),
        }
        rule_to_context = {
            "min_wallet_health_score": "wallet_health_score",
            "max_single_tx_sats": "transaction_amount_sats",
            "min_required_approvals": "required_approvals",
        }

        violations: list[str] = []
        for rule in rules:
            comparator, threshold = self._parse_rule(rule.rule_value)
            context_key = rule_to_context.get(rule.rule_key, rule.rule_key)
            actual = context.get(context_key)
            if actual is None:
                continue
            if not self._matches(actual=actual, comparator=comparator, threshold=threshold):
                violations.append(
                    f"Policy rule failed: {rule.rule_key} requires {comparator}:{int(threshold)} (actual={actual:.0f})."
                )

        allowed = not any("severity=error" in v for v in violations) and not violations
        next_actions = self._next_actions(allowed)
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

    def upsert_catalog_entry(self, db: Session, payload: PolicyCatalogUpsertIn) -> PolicyCatalogOut:
        repo = PolicyRepository(db)
        try:
            policy = repo.upsert_policy(
                name=payload.name,
                description=payload.description,
                min_wallet_health_score=payload.min_wallet_health_score,
                max_single_tx_sats=payload.max_single_tx_sats,
                rules=payload.rules,
            )
            return PolicyCatalogOut(
                name=policy.name,
                min_wallet_health_score=policy.min_wallet_health_score,
                max_single_tx_sats=policy.max_single_tx_sats,
            )
        except OperationalError:
            db.rollback()
            return PolicyCatalogOut(
                name=payload.name,
                min_wallet_health_score=payload.min_wallet_health_score,
                max_single_tx_sats=payload.max_single_tx_sats,
            )

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

    @staticmethod
    def _parse_rule(rule_value: str) -> tuple[str, float]:
        if ":" not in rule_value:
            return "eq", float(rule_value)
        comparator, raw = rule_value.split(":", 1)
        return comparator, float(raw)

    @staticmethod
    def _matches(actual: float, comparator: str, threshold: float) -> bool:
        if comparator == "gte":
            return actual >= threshold
        if comparator == "lte":
            return actual <= threshold
        return actual == threshold

    @staticmethod
    def _next_actions(allowed: bool) -> list[str]:
        return (
            ["Proceed with PSBT creation and designated signer quorum workflow."]
            if allowed
            else [
                "Escalate to treasury operator review.",
                "Record justification in policy execution log.",
            ]
        )
