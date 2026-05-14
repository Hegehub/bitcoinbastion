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
        base_confidence = 0.78 if wallet_health_score is not None else 0.62
        freshness_band = "fresh" if has_recent_health_report else "unknown"
        confidence = max(0.1, base_confidence - (0.0 if has_recent_health_report else 0.1))
        evidence_chain = [
            {
                "domain": "policy",
                "reference": f"policy_owner:{owner_id}",
                "confidence": confidence,
                "source_type": "runtime" if wallet_health_score is not None else "fallback",
                "details": {
                    "basis": basis,
                    "has_recent_health_report": has_recent_health_report,
                    "freshness_band": freshness_band,
                },
            }
        ]
        return {
            "owner_id": owner_id,
            "policy_maturity_score": score,
            "maturity": maturity,
            "gaps": gaps,
            "freshness": {"source": "policy_runtime_snapshot"},
            "confidence": round(confidence, 3),
            "explainability": {
                "scoring_basis": [
                    "policy coverage",
                    "simulation recency",
                    "emergency constraints",
                    basis,
                ],
                "evidence_chain": evidence_chain,
                "freshness": {"source": "policy_runtime_snapshot", "freshness_band": freshness_band},
                "source_quality": {
                    "source_type": "runtime" if wallet_health_score is not None else "fallback",
                    "is_fallback": wallet_health_score is None,
                },
                "audit_packet": {
                    "packet_type": "policy_violation" if gaps else "policy_review",
                    "evidence_refs": [f"policy_owner:{owner_id}"],
                    "source_quality": {
                        "source_type": "runtime" if wallet_health_score is not None else "fallback",
                        "is_fallback": wallet_health_score is None,
                    },
                    "confidence": round(confidence, 3),
                    "transformations": ["policy_maturity_scoring"],
                    "policy_context": {"gaps": gaps, "maturity": maturity},
                    "recommendation_rationale": "Escalate policy controls when maturity gaps are present.",
                    "lineage": evidence_chain,
                },
            },
        }
