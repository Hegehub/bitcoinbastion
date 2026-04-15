import json

from app.db.models.explainability import EvidenceNode
from app.db.models.signal import Signal
from app.schemas.recommendation import RecommendationItemOut, SignalRecommendationOut


class SignalRecommendationService:
    def build(
        self,
        signal: Signal,
        evidence_nodes: list[EvidenceNode] | None = None,
        policy_refs: list[str] | None = None,
    ) -> SignalRecommendationOut:
        horizons = self._extract_horizons(signal)
        dominant = str(horizons.get("dominant", "short"))
        evidence_refs = self._extract_evidence_refs(signal=signal, evidence_nodes=evidence_nodes)
        effective_policy_refs = policy_refs or self._extract_policy_refs(signal)

        recs: list[RecommendationItemOut] = []
        if signal.severity == "high":
            recs.append(
                RecommendationItemOut(
                    priority="high",
                    horizon=dominant,
                    action="Escalate to operator review and publish an alert digest immediately.",
                    rationale="High-severity signals require rapid human validation and communication.",
                    evidence_refs=evidence_refs,
                    policy_refs=effective_policy_refs,
                )
            )
        if float(horizons.get("short", 0.0)) >= 0.6:
            recs.append(
                RecommendationItemOut(
                    priority="medium",
                    horizon="short",
                    action="Run short-term risk checks (fees, mempool, wallet exposure) before next spend.",
                    rationale="Short-horizon pressure indicates near-term execution risk.",
                    evidence_refs=evidence_refs,
                    policy_refs=effective_policy_refs,
                )
            )
        if float(horizons.get("long", 0.0)) >= 0.6:
            recs.append(
                RecommendationItemOut(
                    priority="medium",
                    horizon="long",
                    action="Create a strategic note and revisit treasury allocation assumptions.",
                    rationale="Long-horizon significance suggests durable structural impact.",
                    evidence_refs=evidence_refs,
                    policy_refs=effective_policy_refs,
                )
            )

        if not recs:
            recs.append(
                RecommendationItemOut(
                    priority="low",
                    horizon=dominant,
                    action="Monitor signal evolution and keep it in the daily review queue.",
                    rationale="Current signal does not cross action threshold but should remain tracked.",
                    evidence_refs=evidence_refs,
                    policy_refs=effective_policy_refs,
                )
            )

        return SignalRecommendationOut(
            signal_id=signal.id,
            generated_by="signal_recommendation_v2",
            recommendations=recs,
        )

    @staticmethod
    def _extract_horizons(signal: Signal) -> dict[str, float | str]:
        try:
            payload = json.loads(signal.explainability_json or "{}")
        except json.JSONDecodeError:
            payload = {}
        if not isinstance(payload, dict):
            return {}
        raw = payload.get("horizons", {})
        return raw if isinstance(raw, dict) else {}

    @staticmethod
    def _extract_evidence_refs(signal: Signal, evidence_nodes: list[EvidenceNode] | None = None) -> list[str]:
        if evidence_nodes:
            ranked = sorted(evidence_nodes, key=lambda node: node.weight, reverse=True)
            refs = [node.node_key for node in ranked if node.node_key]
            return refs[:3]

        try:
            refs = json.loads(signal.source_refs_json or "[]")
        except json.JSONDecodeError:
            refs = []
        if isinstance(refs, list):
            return [str(item) for item in refs[:3]]
        return []

    @staticmethod
    def _extract_policy_refs(signal: Signal) -> list[str]:
        try:
            payload = json.loads(signal.details_json or "{}")
        except json.JSONDecodeError:
            return []

        if not isinstance(payload, dict):
            return []

        result: list[str] = []
        raw_name = payload.get("policy_name")
        if isinstance(raw_name, str) and raw_name:
            result.append(raw_name)
        raw_rules = payload.get("applied_policy_rules")
        if isinstance(raw_rules, list):
            result.extend(str(item) for item in raw_rules[:3])
        return result
