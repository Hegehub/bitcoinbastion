import json
from typing import Literal

from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from app.db.models.treasury import PolicyExecutionLog
from app.db.repositories.policy_repository import PolicyExecutionRepository, PolicyRepository
from app.schemas.policy import (
    PolicyCatalogOut,
    PolicyCatalogUpsertIn,
    PolicyCatalogCompareRequest,
    PolicyCatalogCompareOut,
    PolicyCheckRequest,
    PolicyCheckResponse,
    PolicyExecutionLogOut,
    PolicyRuleOut,
    PolicySimulationDiffOut,
    PolicySimulationOut,
    PolicySimulationRequest,
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
            existing = repo.get_policy(payload.name)
            self._validate_policy_change_controls(existing=existing, payload=payload)

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

    @staticmethod
    def _validate_policy_change_controls(existing: object | None, payload: PolicyCatalogUpsertIn) -> None:
        if existing is None:
            return

        old_min_wallet_health = int(getattr(existing, "min_wallet_health_score", payload.min_wallet_health_score))
        old_max_single_tx = int(getattr(existing, "max_single_tx_sats", payload.max_single_tx_sats))

        min_health_delta = payload.min_wallet_health_score - old_min_wallet_health
        tx_limit_drop_ratio = 0.0
        if old_max_single_tx > 0:
            tx_limit_drop_ratio = (old_max_single_tx - payload.max_single_tx_sats) / old_max_single_tx

        high_risk_tightening = min_health_delta >= 15 or tx_limit_drop_ratio >= 0.5
        has_justification = bool((payload.change_justification or "").strip())

        if high_risk_tightening and not has_justification:
            raise ValueError(
                "High-risk policy tightening requires change_justification for governance traceability."
            )

    def simulate_compare(self, db: Session, payload: PolicySimulationRequest) -> PolicySimulationOut:
        baseline_input = PolicyCheckRequest(
            policy_name=payload.baseline_policy_name,
            wallet_health_score=payload.wallet_health_score,
            transaction_amount_sats=payload.transaction_amount_sats,
            required_approvals=payload.required_approvals,
        )
        candidate_input = PolicyCheckRequest(
            policy_name=payload.candidate_policy_name,
            wallet_health_score=payload.wallet_health_score,
            transaction_amount_sats=payload.transaction_amount_sats,
            required_approvals=payload.required_approvals,
        )

        try:
            baseline = self.evaluate(db=db, payload=baseline_input)
            candidate = self.evaluate(db=db, payload=candidate_input)
        except OperationalError:
            db.rollback()
            baseline = self._evaluate_stateless(baseline_input)
            candidate = self._evaluate_stateless(candidate_input)

        baseline_violations = set(baseline.violations)
        candidate_violations = set(candidate.violations)

        repo = PolicyRepository(db)
        try:
            baseline_rules = self._rule_map(repo=repo, policy_name=payload.baseline_policy_name)
            candidate_rules = self._rule_map(repo=repo, policy_name=payload.candidate_policy_name)
        except OperationalError:
            db.rollback()
            baseline_rules = {}
            candidate_rules = {}
        changed_rules = self._changed_rules(baseline_rules=baseline_rules, candidate_rules=candidate_rules)

        risk_level, required_approvals_suggested, governance_actions = self._simulation_risk_controls(
            baseline_allowed=baseline.allowed,
            candidate_allowed=candidate.allowed,
            changed_rules=changed_rules,
        )

        diff = PolicySimulationDiffOut(
            baseline_allowed=baseline.allowed,
            candidate_allowed=candidate.allowed,
            changed=(baseline.allowed != candidate.allowed) or (baseline_violations != candidate_violations),
            added_violations=sorted(candidate_violations - baseline_violations),
            removed_violations=sorted(baseline_violations - candidate_violations),
            changed_rules=changed_rules,
            risk_level=risk_level,
            required_approvals_suggested=required_approvals_suggested,
            governance_actions=governance_actions,
        )
        return PolicySimulationOut(baseline=baseline, candidate=candidate, diff=diff)

    @staticmethod
    def _rule_map(repo: PolicyRepository, policy_name: str) -> dict[str, str]:
        policy = repo.get_or_create_policy(policy_name)
        return {rule.rule_key: rule.rule_value for rule in repo.list_rules(policy.id)}

    @staticmethod
    def _changed_rules(*, baseline_rules: dict[str, str], candidate_rules: dict[str, str]) -> list[str]:
        keys = sorted(set(baseline_rules) | set(candidate_rules))
        changed: list[str] = []
        for key in keys:
            before = baseline_rules.get(key)
            after = candidate_rules.get(key)
            if before != after:
                changed.append(f"{key}: {before or 'unset'} -> {after or 'unset'}")
        return changed

    @staticmethod
    def _simulation_risk_controls(
        *,
        baseline_allowed: bool,
        candidate_allowed: bool,
        changed_rules: list[str],
    ) -> tuple[Literal["low", "medium", "high"], int, list[str]]:
        if baseline_allowed and not candidate_allowed:
            return (
                "high",
                2,
                [
                    "Require 2 admin approvals before activating candidate policy.",
                    "Run staged rollout and monitor policy execution logs for 24h.",
                ],
            )

        if len(changed_rules) >= 2:
            return (
                "medium",
                2,
                [
                    "Require peer review sign-off for rule deltas.",
                    "Record simulation artifacts in change log.",
                ],
            )

        return (
            "low",
            1,
            [
                "Record simulation result and proceed through standard approval flow.",
            ],
        )

    def compare_catalog_profiles(self, db: Session, payload: PolicyCatalogCompareRequest) -> PolicyCatalogCompareOut:
        repo = PolicyRepository(db)
        try:
            baseline = repo.get_or_create_policy(payload.baseline_policy_name)
            candidate = repo.get_or_create_policy(payload.candidate_policy_name)

            changed_thresholds: list[str] = []
            if baseline.min_wallet_health_score != candidate.min_wallet_health_score:
                changed_thresholds.append(
                    f"min_wallet_health_score: {baseline.min_wallet_health_score} -> {candidate.min_wallet_health_score}"
                )
            if baseline.max_single_tx_sats != candidate.max_single_tx_sats:
                changed_thresholds.append(
                    f"max_single_tx_sats: {baseline.max_single_tx_sats} -> {candidate.max_single_tx_sats}"
                )

            baseline_rules = {rule.rule_key: rule.rule_value for rule in repo.list_rules(baseline.id)}
            candidate_rules = {rule.rule_key: rule.rule_value for rule in repo.list_rules(candidate.id)}
            changed_rules = self._changed_rules(baseline_rules=baseline_rules, candidate_rules=candidate_rules)

            risk_level: Literal["low", "medium", "high"] = "low"
            if len(changed_thresholds) + len(changed_rules) >= 3:
                risk_level = "high"
            elif changed_thresholds or changed_rules:
                risk_level = "medium"

            return PolicyCatalogCompareOut(
                baseline_policy_name=baseline.name,
                candidate_policy_name=candidate.name,
                changed_thresholds=changed_thresholds,
                changed_rules=changed_rules,
                risk_level=risk_level,
            )
        except OperationalError:
            db.rollback()
            return PolicyCatalogCompareOut(
                baseline_policy_name=payload.baseline_policy_name,
                candidate_policy_name=payload.candidate_policy_name,
                changed_thresholds=[],
                changed_rules=[],
                risk_level="low",
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
