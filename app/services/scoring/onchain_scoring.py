from dataclasses import dataclass

from app.integrations.bitcoin.provider import ChainEvent
from app.services.blockchain.chain_state_service import ChainStateEvaluation


@dataclass
class OnchainScore:
    significance: float
    confidence: float
    explainability: dict[str, object]
    tags: list[str]


class OnchainScoringService:
    """Explainable baseline scoring for on-chain events."""

    LARGE_TRANSFER_THRESHOLD = 1_000_000_000

    def score(self, event: ChainEvent, *, chain_state: ChainStateEvaluation | None = None) -> OnchainScore:
        transfer_component = min(1.0, event.value_sats / 2_000_000_000)
        dormancy_days = self._payload_int(event.payload, "dormancy_days")
        watched_entity = bool(event.payload.get("watched_entity"))

        dormancy_component = min(1.0, dormancy_days / 3650) if dormancy_days > 0 else 0.0
        watched_component = 0.2 if watched_entity else 0.0
        event_type_component = 0.2 if event.event_type == "large_transfer" else 0.1

        raw_score = (transfer_component * 0.6) + (dormancy_component * 0.25) + watched_component + event_type_component
        significance = min(1.0, raw_score)

        confidence = 0.65
        if event.value_sats >= self.LARGE_TRANSFER_THRESHOLD:
            confidence += 0.2
        if watched_entity:
            confidence += 0.1

        chain_state_penalty = 0.0
        chain_state_bonus = 0.0
        chain_state_warning = ""
        if chain_state is not None:
            if chain_state.finality_band == "weak":
                chain_state_penalty = 0.22
                chain_state_warning = "Low finality context reduces confidence; monitor for reorg risk."
            elif chain_state.finality_band == "moderate":
                chain_state_penalty = 0.08
            else:
                chain_state_bonus = 0.04
            chain_state_penalty += min(0.15, chain_state.reorg_risk_score * 0.12)

        confidence = min(0.98, confidence + chain_state_bonus)
        confidence = max(0.1, confidence - chain_state_penalty)

        explainability: dict[str, object] = {
            "transfer_component": round(transfer_component, 4),
            "dormancy_component": round(dormancy_component, 4),
            "watched_component": round(watched_component, 4),
            "event_type_component": round(event_type_component, 4),
            "reason": "onchain_significance_baseline",
            "chain_state_penalty": round(chain_state_penalty, 4),
            "chain_state_bonus": round(chain_state_bonus, 4),
            "chain_state_warning": chain_state_warning,
        }

        tags = [event.event_type]
        if watched_entity:
            tags.append("watched_entity")
        if dormancy_days >= 365:
            tags.append("dormant_coins")
        if chain_state is not None:
            tags.append(f"finality_{chain_state.finality_band}")

        return OnchainScore(
            significance=round(significance, 4),
            confidence=round(confidence, 4),
            explainability=explainability,
            tags=tags,
        )

    @staticmethod
    def _payload_int(payload: dict[str, str | int | float], key: str) -> int:
        value = payload.get(key, 0)
        if isinstance(value, bool):
            return 0
        if isinstance(value, int):
            return value
        if isinstance(value, float):
            return int(value)
        if isinstance(value, str) and value.isdigit():
            return int(value)
        return 0
