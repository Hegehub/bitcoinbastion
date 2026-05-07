from app.services.citadel.sovereignty_graph_service import SovereigntyGraphService
from app.services.mempool.fee_market_model import FeeMarketModel
from app.services.mempool.mempool_analyzer_service import MempoolAnalyzerService, MempoolSnapshot


class DisasterSimulationService:
    SCENARIO_RULES: dict[str, dict[str, object]] = {
        "loss_signer": {
            "aliases": {"loss_signer", "signer_loss"},
            "affected_dependency_types": {"signing"},
            "base_shock": 0.46,
            "remediations": [
                "Add independent signer device and verify quorum recovery path.",
                "Run signer-loss drill with documented operator handoff.",
            ],
        },
        "vendor_outage": {
            "aliases": {"vendor_outage", "coordinator_outage"},
            "affected_dependency_types": {"orchestration", "policy_assumption"},
            "base_shock": 0.24,
            "remediations": [
                "Validate coordinator failover path and offline signing fallback.",
                "Verify policy execution continuity during coordinator outage.",
            ],
        },
        "backup_loss": {
            "aliases": {"backup_loss", "artifact_loss"},
            "affected_dependency_types": {"recovery", "artifact_dependency"},
            "base_shock": 0.31,
            "remediations": [
                "Create geographically independent backup set and re-verify checksum.",
                "Rehearse descriptor + runbook restoration from secondary channel.",
            ],
        },
    }

    @classmethod
    def _resolve_scenario(cls, normalized: str) -> tuple[str, dict[str, object]]:
        for canonical, rule in cls.SCENARIO_RULES.items():
            aliases = rule.get("aliases", set())
            if normalized in aliases:
                return canonical, rule
        return "vendor_outage", cls.SCENARIO_RULES["vendor_outage"]

    def simulate(self, *, owner_id: int, scenario_code: str) -> dict[str, object]:
        normalized = scenario_code.strip().lower()
        scenario_key, scenario_rule = self._resolve_scenario(normalized)

        graph = SovereigntyGraphService().build(owner_id=owner_id)
        edges = list(graph.get("edges", []))
        spofs = list(graph.get("single_points_of_failure", []))
        affected_types = set(scenario_rule["affected_dependency_types"])

        blocked_paths = [
            f"{edge['source']}->{edge['target']}"
            for edge in edges
            if edge.get("dependency_type") in affected_types
        ]
        remaining_paths = [
            f"{edge['source']}->{edge['target']}"
            for edge in edges
            if edge.get("dependency_type") not in affected_types
        ]
        critical_failure_points = sorted(
            {
                edge["target"]
                for edge in spofs
                if edge.get("dependency_type") in affected_types or edge.get("single_point_of_failure")
            }
        )

        base_shock = float(scenario_rule["base_shock"])
        spof_penalty = min(0.28, len(spofs) * 0.05)
        blocked_penalty = min(0.22, len(blocked_paths) * 0.04)
        mempool_snapshot = MempoolSnapshot(
            backlog_tx_count=40_000 + len(blocked_paths) * 15_000,
            backlog_vbytes=55_000_000 + len(spofs) * 12_000_000,
            median_fee_rate_sat_vb=8.0 + len(blocked_paths) * 4.0,
            high_priority_fee_rate_sat_vb=18.0 + len(blocked_paths) * 8.0,
        )
        mempool_state = MempoolAnalyzerService().analyze(mempool_snapshot)
        mempool_market = FeeMarketModel().estimate(mempool=mempool_state, target_blocks=3)
        mempool_penalty = min(0.18, mempool_market.high_fee_scenario_sat_vb / 1000)
        survivability = round(max(0.05, 1.0 - base_shock - spof_penalty - blocked_penalty - mempool_penalty), 3)
        confidence = round(min(0.95, 0.62 + (0.02 * len(edges)) - (0.04 if len(spofs) > 3 else 0.0)), 3)

        return {
            "owner_id": owner_id,
            "scenario_code": scenario_key,
            "survivability_score": survivability,
            "blocked_paths": blocked_paths,
            "remaining_paths": remaining_paths,
            "critical_failure_points": critical_failure_points,
            "recommended_remediations": list(scenario_rule["remediations"]),
            "freshness": {"source": "deterministic_ruleset", "version": "citadel_disaster_v2"},
            "confidence": confidence,
            "explainability": {
                "rule_set": "citadel_disaster_v2",
                "base_shock": base_shock,
                "spof_penalty": spof_penalty,
                "blocked_penalty": blocked_penalty,
                "graph_spof_count": len(spofs),
                "graph_edge_count": len(edges),
                "affected_dependency_types": sorted(affected_types),
                "mempool_state": mempool_state.congestion_state,
                "mempool_high_fee_scenario_sat_vb": mempool_market.high_fee_scenario_sat_vb,
                "mempool_penalty": mempool_penalty,
            },
        }
