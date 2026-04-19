class InheritanceVerificationService:
    def evaluate(self, *, owner_id: int) -> dict[str, object]:
        completeness = 0.78 if owner_id % 2 == 0 else 0.52
        human_dependency = 0.35 if owner_id % 2 == 0 else 0.78
        readability = 0.72 if owner_id % 3 != 0 else 0.48

        critical_gaps: list[str] = []
        if completeness < 0.6:
            critical_gaps.append("Inheritance flow lacks complete custody handoff steps.")
        if human_dependency > 0.7:
            critical_gaps.append("Inheritance relies on a single operator's tacit knowledge.")
        if readability < 0.6:
            critical_gaps.append("Heir-facing instructions are operationally ambiguous.")

        status = "strong" if not critical_gaps else "weak" if len(critical_gaps) >= 2 else "moderate"

        return {
            "owner_id": owner_id,
            "status": status,
            "completeness_score": round(completeness, 3),
            "human_dependency_score": round(human_dependency, 3),
            "operational_readability_score": round(readability, 3),
            "critical_gaps": critical_gaps,
            "recommendations": [
                "Publish explicit inheritance execution checklist.",
                "Run annual inheritance tabletop exercise.",
            ],
            "freshness": {"source": "inheritance_verifier_v1"},
            "confidence": 0.72,
            "explainability": {
                "signals": ["artifact completeness", "human dependency", "instruction readability"],
            },
        }
