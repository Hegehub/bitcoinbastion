import json

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.db.models.treasury import PolicyExecutionLog, PolicyRule, TreasuryPolicy
from app.schemas.policy import PolicyRuleUpsertIn


class PolicyExecutionRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(
        self,
        *,
        policy_name: str,
        wallet_health_score: int,
        transaction_amount_sats: int,
        allowed: bool,
        violations: list[str],
        next_actions: list[str],
    ) -> PolicyExecutionLog:
        item = PolicyExecutionLog(
            policy_name=policy_name,
            wallet_health_score=wallet_health_score,
            transaction_amount_sats=transaction_amount_sats,
            allowed=allowed,
            violations_json=json.dumps(violations),
            next_actions_json=json.dumps(next_actions),
        )
        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)
        return item

    def list_recent(self, limit: int, offset: int) -> list[PolicyExecutionLog]:
        stmt = (
            select(PolicyExecutionLog)
            .order_by(PolicyExecutionLog.executed_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(self.db.execute(stmt).scalars())


class PolicyRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_policy(self, name: str) -> TreasuryPolicy | None:
        stmt = select(TreasuryPolicy).where(TreasuryPolicy.name == name)
        return self.db.execute(stmt).scalar_one_or_none()

    def get_or_create_policy(self, name: str) -> TreasuryPolicy:
        policy = self.get_policy(name)
        if policy is not None:
            return policy

        policy = TreasuryPolicy(
            name=name,
            description="Default runtime policy",
            min_wallet_health_score=60,
            max_single_tx_sats=10_000_000,
        )
        self.db.add(policy)
        self.db.commit()
        self.db.refresh(policy)

        self.db.add_all(
            [
                PolicyRule(
                    policy_id=policy.id,
                    rule_key="min_wallet_health_score",
                    rule_value="gte:60",
                    severity="error",
                ),
                PolicyRule(
                    policy_id=policy.id,
                    rule_key="max_single_tx_sats",
                    rule_value="lte:10000000",
                    severity="error",
                ),
            ]
        )
        self.db.commit()
        return policy

    def upsert_policy(
        self,
        *,
        name: str,
        description: str,
        min_wallet_health_score: int,
        max_single_tx_sats: int,
        rules: list[PolicyRuleUpsertIn] | None = None,
    ) -> TreasuryPolicy:
        policy = self.get_policy(name)
        if policy is None:
            policy = TreasuryPolicy(name=name)
            self.db.add(policy)
            self.db.flush()

        policy.description = description
        policy.min_wallet_health_score = min_wallet_health_score
        policy.max_single_tx_sats = max_single_tx_sats
        self.db.flush()

        resolved_rules = rules or [
            PolicyRuleUpsertIn(rule_key="min_wallet_health_score", comparator="gte", threshold=min_wallet_health_score),
            PolicyRuleUpsertIn(rule_key="max_single_tx_sats", comparator="lte", threshold=max_single_tx_sats),
        ]

        self.db.execute(delete(PolicyRule).where(PolicyRule.policy_id == policy.id))
        self.db.add_all(
            [
                PolicyRule(
                    policy_id=policy.id,
                    rule_key=rule.rule_key,
                    rule_value=f"{rule.comparator}:{rule.threshold}",
                    severity=rule.severity,
                )
                for rule in resolved_rules
            ]
        )
        self.db.commit()
        self.db.refresh(policy)
        return policy

    def list_rules(self, policy_id: int) -> list[PolicyRule]:
        stmt = select(PolicyRule).where(PolicyRule.policy_id == policy_id).order_by(PolicyRule.id.asc())
        return list(self.db.execute(stmt).scalars())

    def list_policies(self) -> list[TreasuryPolicy]:
        stmt = select(TreasuryPolicy).order_by(TreasuryPolicy.name.asc())
        return list(self.db.execute(stmt).scalars())
