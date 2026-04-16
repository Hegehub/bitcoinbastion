class DisasterSimulationService:
    def simulate(self, *, owner_id: int, scenario_code: str) -> dict[str, object]:
        normalized = scenario_code.strip().lower()

        survivability = 0.62
        blocked_paths = []
        if normalized in {"loss_signer", "signer_loss"}:
            survivability = 0.42
            blocked_paths = ["primary_signing_path"]
        elif normalized in {"vendor_outage", "coordinator_outage"}:
            survivability = 0.55
            blocked_paths = ["coordinator_path"]

        remaining_paths = ["backup_recovery_path"] if survivability < 0.7 else ["primary_signing_path", "backup_recovery_path"]
        return {
            "owner_id": owner_id,
            "scenario_code": normalized,
            "survivability_score": survivability,
            "blocked_paths": blocked_paths,
            "remaining_paths": remaining_paths,
            "critical_failure_points": ["single signer"] if survivability < 0.5 else [],
            "recommended_remediations": [
                "Add independent signer device.",
                "Validate recovery runbook under outage scenario.",
            ],
            "freshness": {"source": "deterministic_ruleset", "version": "v1"},
            "confidence": 0.7,
            "explainability": {"rule_set": "citadel_disaster_v1"},
        }
