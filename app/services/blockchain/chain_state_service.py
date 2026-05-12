from dataclasses import dataclass
from app.services.explainability.contract import build_explainability_contract


@dataclass(slots=True)
class ChainStateEvaluation:
    tip_height: int
    observed_block_height: int
    headers_height: int
    confirmation_depth: int
    reorg_risk_score: float
    finality_score: float
    finality_band: str
    confidence_score: float
    freshness: dict[str, object]
    explainability: dict[str, object]


class ChainStateService:
    def evaluate(
        self,
        *,
        tip_height: int,
        observed_block_height: int,
        headers_height: int | None = None,
        provider_tip_height: int | None = None,
        provider_confidence: float | None = None,
        provider_data_age_seconds: int | None = None,
        data_source: str = "query",
    ) -> ChainStateEvaluation:
        headers = headers_height if headers_height is not None else tip_height
        confirmation_depth = max(0, (tip_height - observed_block_height) + 1)

        # Finality depth quality is intentionally conservative and non-probabilistic.
        if confirmation_depth <= 0:
            depth_quality = 0.0
        elif confirmation_depth == 1:
            depth_quality = 0.08
        elif confirmation_depth == 2:
            depth_quality = 0.2
        elif confirmation_depth == 3:
            depth_quality = 0.35
        elif confirmation_depth <= 5:
            depth_quality = 0.48
        elif confirmation_depth <= 11:
            depth_quality = 0.62
        else:
            depth_quality = 0.72

        header_tip_gap = abs(headers - tip_height)
        header_observed_gap = abs(headers - observed_block_height)

        provider_gap = abs(provider_tip_height - tip_height) if provider_tip_height is not None else 0
        normalized_provider_conf = max(0.0, min(1.0, float(provider_confidence or 0.0)))

        depth_risk = max(0.0, 1.0 - depth_quality)
        header_tip_risk = min(1.0, header_tip_gap / 2.0)
        header_observed_risk = min(1.0, header_observed_gap / 4.0)

        provider_gap_risk = 0.0
        if provider_tip_height is not None:
            provider_gap_risk = min(1.0, provider_gap / 2.0) * max(0.35, normalized_provider_conf)

        stale_provider_risk = 0.0
        stale_band = "unknown"
        if provider_data_age_seconds is not None:
            age = max(0, int(provider_data_age_seconds))
            if age <= 30:
                stale_band = "fresh"
                stale_provider_risk = 0.0
            elif age <= 120:
                stale_band = "aging"
                stale_provider_risk = 0.1
            elif age <= 600:
                stale_band = "stale"
                stale_provider_risk = 0.22
            else:
                stale_band = "very_stale"
                stale_provider_risk = 0.34

        source_risk = 0.0
        if data_source == "repository_fallback":
            source_risk = 0.12
        elif data_source == "provider_fallback":
            source_risk = 0.2

        reorg_risk = round(
            min(
                1.0,
                (depth_risk * 0.55)
                + (header_tip_risk * 0.18)
                + (header_observed_risk * 0.12)
                + (provider_gap_risk * 0.08)
                + (stale_provider_risk * 0.05)
                + source_risk,
            ),
            4,
        )

        finality = round(max(0.0, min(1.0, depth_quality * (1.0 - reorg_risk))), 4)

        if confirmation_depth >= 12 and finality >= 0.5 and reorg_risk <= 0.35:
            band = "strong"
        elif confirmation_depth >= 3 and finality >= 0.3 and reorg_risk <= 0.55:
            band = "moderate"
        else:
            band = "weak"

        confidence = 0.84
        if data_source == "repository_fallback":
            confidence -= 0.16
        elif data_source == "provider_fallback":
            confidence -= 0.24
        if provider_tip_height is not None:
            confidence = min(confidence, 0.65 + (normalized_provider_conf * 0.2))
            confidence -= min(0.18, provider_gap * 0.03)
        if provider_data_age_seconds is not None:
            confidence -= min(0.22, max(0, int(provider_data_age_seconds)) / 1200)
        if header_tip_gap > 0:
            confidence -= min(0.18, header_tip_gap * 0.04)
        confidence = round(max(0.1, min(0.95, confidence)), 4)

        return ChainStateEvaluation(
            tip_height=tip_height,
            observed_block_height=observed_block_height,
            headers_height=headers,
            confirmation_depth=confirmation_depth,
            reorg_risk_score=reorg_risk,
            finality_score=finality,
            finality_band=band,
            confidence_score=confidence,
            freshness={
                "source": data_source,
                "source_type": "provider" if data_source == "provider_probe" else "runtime",
                "provider_name": "esplora" if data_source == "provider_probe" else "unknown",
                "is_mock": data_source == "provider_fallback",
                "is_fallback": data_source in {"repository_fallback", "provider_fallback"},
                "provider_data_age_seconds": provider_data_age_seconds,
                "provider_freshness_band": stale_band,
            },
            explainability={
                "inputs": {
                    "tip_height": tip_height,
                    "observed_block_height": observed_block_height,
                    "headers_height": headers,
                    "provider_tip_height": provider_tip_height,
                    "provider_confidence": normalized_provider_conf,
                    "provider_data_age_seconds": provider_data_age_seconds,
                    "data_source": data_source,
                },
                "derived": {
                    "confirmation_depth": confirmation_depth,
                    "depth_quality_component": round(depth_quality, 4),
                    "header_tip_gap_blocks": header_tip_gap,
                    "header_observed_gap_blocks": header_observed_gap,
                    "provider_tip_gap_blocks": provider_gap,
                    "provider_freshness_band": stale_band,
                },
                "risk_components": {
                    "depth_risk_component": round(depth_risk, 4),
                    "header_tip_risk_component": round(header_tip_risk, 4),
                    "header_observed_risk_component": round(header_observed_risk, 4),
                    "provider_gap_risk_component": round(provider_gap_risk, 4),
                    "stale_provider_risk_component": round(stale_provider_risk, 4),
                    "source_risk_component": round(source_risk, 4),
                },
                "scoring": {
                    "note": "Conservative risk model. finality_score is operational confidence, not consensus finality.",
                    "finality_formula": "depth_quality*(1-reorg_risk)",
                },
                "source_quality": {
                    "source_type": "provider" if data_source == "provider_probe" else "runtime",
                    "provider_name": "esplora" if data_source == "provider_probe" else "unknown",
                    "is_mock": data_source == "provider_fallback",
                    "is_fallback": data_source in {"repository_fallback", "provider_fallback"},
                    "limitations": "Chain-state confidence is operational and conservative; not consensus-finality proof.",
                },
                "contract": build_explainability_contract(
                    domain="protocol_layer",
                    confidence=confidence,
                    freshness={
                        "source": data_source,
                        "provider_data_age_seconds": provider_data_age_seconds,
                        "provider_freshness_band": stale_band,
                    },
                    source_type="provider" if data_source == "provider_probe" else "runtime",
                    provider_name="esplora" if data_source == "provider_probe" else "unknown",
                    is_mock=data_source == "provider_fallback",
                    is_fallback=data_source in {"repository_fallback", "provider_fallback"},
                    limitations=[
                        "Operational confidence only; not consensus finality proof.",
                        "Provider fallback lowers certainty.",
                    ],
                    signals={
                        "confirmation_depth": confirmation_depth,
                        "reorg_risk_score": reorg_risk,
                    },
                ),
                "calibration_version": "chain_state_v4_conservative",
            },
        )
