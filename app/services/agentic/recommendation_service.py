import json

from app.db.models.explainability import EvidenceEdge, EvidenceNode
from app.db.models.signal import Signal
from app.schemas.recommendation import RecommendationItemOut, SignalRecommendationOut


class SignalRecommendationService:
    HORIZON_NAMES = {"short", "medium", "long"}
    MAX_REFS = 3

    def build(
        self,
        signal: Signal,
        evidence_nodes: list[EvidenceNode] | None = None,
        evidence_edges: list[EvidenceEdge] | None = None,
        policy_refs: list[str] | None = None,
    ) -> SignalRecommendationOut:
        horizons = self._extract_horizons(signal)
        dominant = self._extract_dominant_horizon(horizons)
        evidence_refs = self._extract_evidence_refs(signal=signal, evidence_nodes=evidence_nodes)
        evidence_paths = self._extract_evidence_paths(evidence_refs=evidence_refs, evidence_edges=evidence_edges)
        raw_policy_refs = policy_refs if policy_refs is not None else self._extract_policy_refs(signal)
        effective_policy_refs = self._normalize_refs(raw_policy_refs)
        action_confidence = self._action_confidence(signal=signal, evidence_refs=evidence_refs)

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
                    evidence_paths=evidence_paths,
                    action_confidence=action_confidence,
                )
            )
        if self._horizon_value(horizons, "short") >= 0.6:
            recs.append(
                RecommendationItemOut(
                    priority="medium",
                    horizon="short",
                    action="Run short-term risk checks (fees, mempool, wallet exposure) before next spend.",
                    rationale="Short-horizon pressure indicates near-term execution risk.",
                    evidence_refs=evidence_refs,
                    policy_refs=effective_policy_refs,
                    evidence_paths=evidence_paths,
                    action_confidence=action_confidence,
                )
            )
        if self._horizon_value(horizons, "long") >= 0.6:
            recs.append(
                RecommendationItemOut(
                    priority="medium",
                    horizon="long",
                    action="Create a strategic note and revisit treasury allocation assumptions.",
                    rationale="Long-horizon significance suggests durable structural impact.",
                    evidence_refs=evidence_refs,
                    policy_refs=effective_policy_refs,
                    evidence_paths=evidence_paths,
                    action_confidence=action_confidence,
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
                    evidence_paths=evidence_paths,
                    action_confidence=action_confidence,
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
            return SignalRecommendationService._normalize_refs(refs)

        try:
            refs = json.loads(signal.source_refs_json or "[]")
        except json.JSONDecodeError:
            refs = []
        if isinstance(refs, list):
            normalized = [str(item) for item in refs]
            return SignalRecommendationService._normalize_refs(normalized)
        return []

    @staticmethod
    def _extract_evidence_paths(
        *,
        evidence_refs: list[str],
        evidence_edges: list[EvidenceEdge] | None = None,
    ) -> list[str]:
        if not evidence_edges or not evidence_refs:
            return []

        allowed = set(evidence_refs)
        paths: list[str] = []
        seen: set[str] = set()
        for edge in evidence_edges:
            if not edge.from_node_key or not edge.to_node_key or not edge.relation:
                continue
            if edge.from_node_key in allowed or edge.to_node_key in allowed:
                path = f"{edge.from_node_key} --{edge.relation}--> {edge.to_node_key}"
                if path in seen:
                    continue
                seen.add(path)
                paths.append(path)
            if len(paths) >= SignalRecommendationService.MAX_REFS:
                break
        return paths

    @staticmethod
    def _action_confidence(signal: Signal, evidence_refs: list[str]) -> float:
        base = SignalRecommendationService._coerce_prob(getattr(signal, "confidence", 0.0))
        evidence_boost = min(len(evidence_refs), SignalRecommendationService.MAX_REFS) * 0.05
        return round(min(1.0, base + evidence_boost), 3)

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
            result.extend(str(item) for item in raw_rules)
        return SignalRecommendationService._normalize_refs(result)

    @classmethod
    def _extract_dominant_horizon(cls, horizons: dict[str, float | str]) -> str:
        dominant = horizons.get("dominant", "short")
        if isinstance(dominant, str) and dominant in cls.HORIZON_NAMES:
            return dominant
        return "short"

    @staticmethod
    def _horizon_value(horizons: dict[str, float | str], key: str) -> float:
        return SignalRecommendationService._coerce_prob(horizons.get(key, 0.0))

    @staticmethod
    def _coerce_prob(value: object) -> float:
        if isinstance(value, bool):
            return 0.0
        if isinstance(value, (int, float)):
            return max(0.0, min(1.0, float(value)))
        if isinstance(value, str):
            try:
                as_float = float(value)
            except ValueError:
                return 0.0
            return max(0.0, min(1.0, as_float))
        return 0.0

    @staticmethod
    def _normalize_refs(refs: list[str]) -> list[str]:
        unique = [ref.strip() for ref in refs if ref and ref.strip()]
        return list(dict.fromkeys(unique))[: SignalRecommendationService.MAX_REFS]
