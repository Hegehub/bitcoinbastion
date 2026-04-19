class CitadelPolicyService:
    def evaluate(self, *, owner_id: int) -> dict[str, object]:
        score = 68 if owner_id % 2 == 0 else 57
        maturity = "moderate" if score >= 60 else "weak"
        return {
            "owner_id": owner_id,
            "policy_maturity_score": score,
            "maturity": maturity,
            "gaps": [
                "No explicit emergency policy profile" if score < 65 else "Missing periodic simulation evidence",
            ],
            "freshness": {"source": "policy_runtime_snapshot"},
            "confidence": 0.71,
            "explainability": {"scoring_basis": ["policy coverage", "simulation recency", "emergency constraints"]},
        }
