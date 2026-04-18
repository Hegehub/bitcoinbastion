class RepairPlanService:
    def build(self, *, owner_id: int) -> dict[str, object]:
        items = [
            {
                "priority_score": 92,
                "title": "Add redundant signer",
                "description": "Introduce a second independent signer device/location.",
                "impact_area": "custody_resilience",
                "difficulty": "medium",
                "estimated_effort": "1-2 days",
                "status": "open",
            },
            {
                "priority_score": 85,
                "title": "Verify recovery artifacts",
                "description": "Run artifact verification checklist and attach evidence metadata.",
                "impact_area": "recovery_readiness",
                "difficulty": "low",
                "estimated_effort": "4-6 hours",
                "status": "open",
            },
        ]
        return {
            "owner_id": owner_id,
            "items": items,
            "freshness": {"source": "citadel_repair_planner"},
            "confidence": 0.75,
            "explainability": {"priority_logic": "severity + dependency centrality + recovery impact"},
        }
