from dataclasses import dataclass


@dataclass(slots=True)
class ChainStateEvaluation:
    tip_height: int
    observed_block_height: int
    headers_height: int
    confirmation_depth: int
    reorg_risk_score: float
    finality_score: float
    finality_band: str
    explainability: dict[str, object]


class ChainStateService:
    def evaluate(
        self,
        *,
        tip_height: int,
        observed_block_height: int,
        headers_height: int | None = None,
    ) -> ChainStateEvaluation:
        headers = headers_height if headers_height is not None else tip_height
        confirmation_depth = max(0, (tip_height - observed_block_height) + 1)
        header_tip_gap = abs(headers - tip_height)
        header_observed_gap = abs(headers - observed_block_height)

        depth_risk = max(0.0, 1.0 - min(1.0, confirmation_depth / 8.0))
        header_tip_risk = min(1.0, header_tip_gap / 4.0)
        header_observed_risk = min(1.0, header_observed_gap / 8.0)
        reorg_risk = round(
            min(1.0, (depth_risk * 0.7) + (header_tip_risk * 0.2) + (header_observed_risk * 0.1)),
            4,
        )
        finality = round(max(0.0, min(1.0, (1.0 - reorg_risk) * min(1.0, confirmation_depth / 8.0))), 4)

        if finality >= 0.82:
            band = "strong"
        elif finality >= 0.5:
            band = "moderate"
        else:
            band = "weak"

        return ChainStateEvaluation(
            tip_height=tip_height,
            observed_block_height=observed_block_height,
            headers_height=headers,
            confirmation_depth=confirmation_depth,
            reorg_risk_score=reorg_risk,
            finality_score=finality,
            finality_band=band,
            explainability={
                "inputs": {
                    "tip_height": tip_height,
                    "observed_block_height": observed_block_height,
                    "headers_height": headers,
                },
                "derived": {
                    "confirmation_depth": confirmation_depth,
                    "depth_risk_component": round(depth_risk, 4),
                    "header_tip_gap_blocks": header_tip_gap,
                    "header_observed_gap_blocks": header_observed_gap,
                    "header_tip_risk_component": round(header_tip_risk, 4),
                    "header_observed_risk_component": round(header_observed_risk, 4),
                },
                "scoring": "finality=(1-reorg_risk)*min(1,confirmations/8)",
                "calibration_version": "chain_state_v2",
            },
        )
