from app.services.citadel.recovery_artifact_service import RecoveryArtifactRecord, RecoveryArtifactService
from app.services.citadel.sovereignty_graph_service import SovereigntyGraphService
from app.services.mempool.fee_market_model import FeeMarketModel
from app.services.mempool.mempool_analyzer_service import MempoolAnalyzerService, MempoolSnapshot
from app.services.script.descriptor_awareness_service import DescriptorAwarenessService


class DisasterSimulationService:
    SCENARIO_RULES: dict[str, dict[str, object]] = {
        "signer_loss": {
            "aliases": {"loss_signer", "signer_loss"},
            "affected_dependency_types": {"signing", "device_dependency"},
            "base_shock": 0.34,
            "fee_pressure_multiplier": 1.15,
            "remediations": [
                "Add independent signer and validate quorum emergency path.",
                "Pair each signer with redundant hardware and documented recovery handoff.",
            ],
        },
        "backup_compromise": {
            "aliases": {"backup_loss", "artifact_loss", "backup_compromise"},
            "affected_dependency_types": {"recovery", "artifact_dependency"},
            "base_shock": 0.38,
            "fee_pressure_multiplier": 1.05,
            "remediations": [
                "Rotate backup set and re-verify integrity signatures.",
                "Establish geographically separated backup escrow channel.",
            ],
        },
        "coordinator_outage": {
            "aliases": {"vendor_outage", "coordinator_outage"},
            "affected_dependency_types": {"orchestration"},
            "base_shock": 0.22,
            "fee_pressure_multiplier": 1.0,
            "remediations": [
                "Validate offline signing fallback independent of coordinator stack.",
                "Run coordinator failover drill with immutable runbook steps.",
            ],
        },
        "descriptor_corruption": {
            "aliases": {"descriptor_corruption", "descriptor_loss"},
            "affected_dependency_types": {"descriptor_dependency", "inheritance_descriptor_dependency"},
            "base_shock": 0.32,
            "fee_pressure_multiplier": 1.0,
            "remediations": [
                "Rebuild descriptor registry from verified source-of-truth snapshot.",
                "Add descriptor checksum verification at every policy milestone.",
            ],
        },
        "inheritance_trigger": {
            "aliases": {"inheritance_trigger", "heir_activation"},
            "affected_dependency_types": {"inheritance_policy_dependency", "artifact_dependency"},
            "base_shock": 0.29,
            "fee_pressure_multiplier": 1.0,
            "remediations": [
                "Rehearse inheritance execution with non-primary operator participation.",
                "Link inheritance controls to policy escalation approval path.",
            ],
        },
        "high_fee_emergency_spend": {
            "aliases": {"high_fee_emergency_spend", "emergency_spend", "fee_spike"},
            "affected_dependency_types": {"signing", "provider_dependency", "recovery"},
            "base_shock": 0.27,
            "fee_pressure_multiplier": 1.45,
            "remediations": [
                "Pre-stage high-priority spend templates with capped input complexity.",
                "Maintain pre-consolidated emergency UTXO lanes for fee spikes.",
            ],
        },
        "provider_outage": {
            "aliases": {"provider_outage", "chain_provider_outage"},
            "affected_dependency_types": {"provider_dependency"},
            "base_shock": 0.25,
            "fee_pressure_multiplier": 1.1,
            "remediations": [
                "Run dual-provider quorum checks and failover validation.",
                "Pin fallback provider endpoints and monitor divergence alerts.",
            ],
        },
        "recovery_instruction_loss": {
            "aliases": {"recovery_instruction_loss", "instruction_loss"},
            "affected_dependency_types": {"inheritance_policy_dependency", "recovery"},
            "base_shock": 0.3,
            "fee_pressure_multiplier": 1.0,
            "remediations": [
                "Regenerate operator runbook from signed, versioned templates.",
                "Require periodic dry-run attestations for recovery instruction completeness.",
            ],
        },
    }

    @classmethod
    def _resolve_scenario(cls, normalized: str) -> tuple[str, dict[str, object]]:
        for canonical, rule in cls.SCENARIO_RULES.items():
            aliases = rule.get("aliases", set())
            if normalized in aliases:
                return canonical, rule
        return "coordinator_outage", cls.SCENARIO_RULES["coordinator_outage"]

    @staticmethod
    def _path(edge: dict[str, object]) -> str:
        return f"{edge['source']}->{edge['target']}"

    @staticmethod
    def _recovery_state(owner_id: int, has_descriptor: bool, has_recent_health_report: bool) -> dict[str, object]:
        artifacts = [
            RecoveryArtifactRecord(
                artifact_type="descriptor",
                label=f"owner-{owner_id}-descriptor",
                is_verified=has_descriptor,
                required_for_recovery=True,
                verification_age_days=14 if has_recent_health_report else 180,
            ),
            RecoveryArtifactRecord(
                artifact_type="backup",
                label=f"owner-{owner_id}-backup",
                is_verified=has_recent_health_report,
                required_for_recovery=True,
                verification_age_days=21 if has_recent_health_report else 210,
            ),
            RecoveryArtifactRecord(
                artifact_type="instructions",
                label=f"owner-{owner_id}-runbook",
                is_verified=has_recent_health_report,
                required_for_recovery=False,
                verification_age_days=30 if has_recent_health_report else 180,
            ),
        ]
        return RecoveryArtifactService().summarize(artifacts=artifacts)

    def simulate(self, *, owner_id: int, scenario_code: str) -> dict[str, object]:
        normalized = scenario_code.strip().lower()
        scenario_key, scenario_rule = self._resolve_scenario(normalized)

        descriptor_required = scenario_key in {"descriptor_corruption"}
        graph = SovereigntyGraphService().build(
            owner_id=owner_id,
            has_descriptor=descriptor_required,
            has_recent_health_report=scenario_key in {"high_fee_emergency_spend", "provider_outage"},
            wallet_type="multisig-2of3" if scenario_key in {"signer_loss", "high_fee_emergency_spend"} else "single-sig",
        )
        edges = list(graph.get("edges", []))
        spofs = list(graph.get("single_points_of_failure", []))
        has_descriptor = any(node.get("node_type") == "descriptor" for node in graph.get("nodes", []))
        has_recent_health_report = bool(graph.get("confidence", 0.0) >= 0.8)
        recovery_state = self._recovery_state(
            owner_id=owner_id,
            has_descriptor=has_descriptor,
            has_recent_health_report=has_recent_health_report,
        )

        affected_types = set(scenario_rule["affected_dependency_types"])
        blocked_edges = [edge for edge in edges if edge.get("dependency_type") in affected_types]
        blocked_paths = [self._path(edge) for edge in blocked_edges]
        remaining_paths = [self._path(edge) for edge in edges if edge.get("dependency_type") not in affected_types]

        critical_failure_points = sorted(
            {
                str(edge["target"])
                for edge in spofs
                if edge.get("dependency_type") in affected_types or edge.get("single_point_of_failure")
            }
        )

        base_shock = float(scenario_rule["base_shock"])
        spof_penalty = min(0.22, len(spofs) * 0.025)
        blocked_penalty = min(0.28, len(blocked_edges) * 0.03)
        recovery_penalty = min(
            0.2,
            max(0.0, (1.0 - float(recovery_state.get("completeness_score", 0.0))) * 0.25),
        )
        descriptor_profile = DescriptorAwarenessService().evaluate(
            has_descriptor=has_descriptor,
            has_recovery_instructions=has_recent_health_report,
            has_backup_reference=has_recent_health_report,
        )
        descriptor_penalty = min(
            0.22,
            max(0.0, (1.0 - float(descriptor_profile.completeness_score)) * 0.2)
            + (0.08 if scenario_key == "descriptor_corruption" and not has_descriptor else 0.0),
        )

        fee_pressure_multiplier = float(scenario_rule["fee_pressure_multiplier"])
        mempool_snapshot = MempoolSnapshot(
            backlog_tx_count=int(35_000 + (len(blocked_edges) * 12_000 * fee_pressure_multiplier)),
            backlog_vbytes=int(50_000_000 + (len(spofs) * 10_000_000 * fee_pressure_multiplier)),
            median_fee_rate_sat_vb=8.0 + (len(blocked_edges) * 3.5 * fee_pressure_multiplier),
            high_priority_fee_rate_sat_vb=18.0 + (len(blocked_edges) * 7.0 * fee_pressure_multiplier),
        )
        mempool_state = MempoolAnalyzerService().analyze(mempool_snapshot)
        mempool_market = FeeMarketModel().estimate(mempool=mempool_state, target_blocks=3)
        mempool_penalty = min(0.2, mempool_market.high_fee_scenario_sat_vb / 900)

        survivability = round(
            max(
                0.04,
                1.0
                - base_shock
                - spof_penalty
                - blocked_penalty
                - recovery_penalty
                - descriptor_penalty
                - mempool_penalty,
            ),
            3,
        )

        confidence = round(
            min(
                0.96,
                max(
                    0.52,
                    0.66
                    + (0.07 if has_recent_health_report else 0.0)
                    + (0.03 if has_descriptor else -0.03)
                    - min(0.14, len(blocked_edges) * 0.01),
                ),
            ),
            3,
        )

        return {
            "owner_id": owner_id,
            "scenario_code": scenario_key,
            "survivability_score": survivability,
            "blocked_paths": blocked_paths,
            "remaining_paths": remaining_paths,
            "critical_failure_points": critical_failure_points,
            "recommended_remediations": list(scenario_rule["remediations"]),
            "freshness": {"source": "deterministic_ruleset", "version": "citadel_disaster_v3"},
            "confidence": confidence,
            "explainability": {
                "rule_set": "citadel_disaster_v3",
                "base_shock": base_shock,
                "spof_penalty": spof_penalty,
                "blocked_penalty": blocked_penalty,
                "recovery_penalty": recovery_penalty,
                "descriptor_penalty": descriptor_penalty,
                "graph_spof_count": len(spofs),
                "graph_edge_count": len(edges),
                "affected_dependency_types": sorted(affected_types),
                "blocked_edge_types": sorted({str(edge.get("dependency_type")) for edge in blocked_edges}),
                "recovery_completeness_score": recovery_state.get("completeness_score", 0.0),
                "descriptor_completeness_score": descriptor_profile.completeness_score,
                "mempool_state": mempool_state.congestion_state,
                "mempool_high_fee_scenario_sat_vb": mempool_market.high_fee_scenario_sat_vb,
                "mempool_penalty": mempool_penalty,
                "confidence_components": {
                    "base": 0.66,
                    "health_bonus": 0.07 if has_recent_health_report else 0.0,
                    "descriptor_effect": 0.03 if has_descriptor else -0.03,
                    "blocked_path_penalty": min(0.14, len(blocked_edges) * 0.01),
                },
            },
        }
