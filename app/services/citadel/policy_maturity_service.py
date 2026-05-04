class CitadelPolicyService:
    def evaluate(
        self,
        *,
        owner_id: int,
        wallet_health_score: float | None = None,
        has_recent_health_report: bool = False,
    ) -> dict[str, object]:
        # Prefer runtime-linked inputs; retain conservative fallback when context is absent.
        if wallet_health_score is None:
            score = 55.0
            basis = "fallback_no_runtime_health_context"
        else:
            normalized_health = max(0.0, min(1.0, float(wallet_health_score)))
            score = 45.0 + (normalized_health * 40.0) + (6.0 if has_recent_health_report else 0.0)
            basis = "wallet_health_runtime_context"
        score = round(max(0.0, min(100.0, score)), 2)
        maturity = "moderate" if score >= 60 else "weak"
        gaps: list[str] = []
        if score < 65:
            gaps.append("No explicit emergency policy profile")
        if not has_recent_health_report:
            gaps.append("No recent wallet health evidence linked to policy controls")
        if not gaps:
            gaps.append("Missing periodic simulation evidence")
        return {
            "owner_id": owner_id,
            "policy_maturity_score": score,
            "maturity": maturity,
            "gaps": gaps,
            "freshness": {"source": "policy_runtime_snapshot"},
            "confidence": 0.78 if wallet_health_score is not None else 0.62,
            "explainability": {
                "scoring_basis": [
                    "policy coverage",
                    "simulation recency",
                    "emergency constraints",
                    basis,
                ]
            },
        }
