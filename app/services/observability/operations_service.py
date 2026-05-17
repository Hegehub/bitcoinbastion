from sqlalchemy.orm import Session

from app.db.repositories.delivery_repository import DeliveryRepository
from app.db.repositories.job_run_repository import JobRunRepository
from app.db.repositories.onchain_repository import OnchainRepository
from app.schemas.observability import (
    ChainStateOut,
    DeliveryStatsOut,
    JobStatsOut,
    OperationsSnapshotOut,
    ProviderHealthOut,
    RecoverySLOOut,
    RuntimeSeverityOut,
    RuntimeDegradedModeOut,
    OperationalEvidencePacketOut,
)
from app.services.blockchain.chain_state_service import ChainStateService
from app.services.observability.recovery_service import RecoveryCheckService
from app.services.observability.provider_health_service import ProviderHealthService
from app.services.mempool.mempool_analyzer_service import MempoolAnalyzerService, MempoolSnapshot
from app.services.explainability.contract import build_audit_packet
from app.services.explainability.contract import propagate_confidence
from app.core.telemetry import (
    increment_provider_failure_metric,
    set_observability_runtime_metrics,
    set_provider_health_detail_metrics,
    set_provider_health_state_metric,
)


class OperationsSnapshotService:
    @staticmethod
    def _runtime_severity(
        *,
        failed_jobs: int,
        failed_deliveries: int,
        provider_share: float,
        provider_count_total: int,
        chain_state: object,
        recovery_slo: dict[str, object],
    ) -> RuntimeSeverityOut:
        dimensions: dict[str, str] = {}
        conditions: list[str] = []
        guidance: list[str] = []
        score = 0

        # provider failure / stale data
        data_source = str(getattr(chain_state, "freshness", {}).get("source", "unknown"))
        source_band = str(getattr(chain_state, "freshness", {}).get("provider_freshness_band", "unknown"))
        if data_source in {"provider_fallback", "repository_fallback"}:
            dimensions["provider_failure"] = "critical"
            conditions.append("Provider fallback active")
            score += 3
            guidance.append("Validate provider outage and failover path before enabling automated actions.")
        elif provider_count_total == 0:
            dimensions["provider_failure"] = "warning"
            conditions.append("No provider observations in the last 24h")
            score += 1
        else:
            dimensions["provider_failure"] = "ok"

        if source_band in {"stale", "very_stale"}:
            dimensions["stale_data"] = "warning" if source_band == "stale" else "critical"
            conditions.append(f"Provider data freshness is {source_band}")
            score += 1 if source_band == "stale" else 2
            guidance.append("Run fresh provider probe and block high-impact policy decisions until freshness recovers.")
        else:
            dimensions["stale_data"] = "ok"

        # chain-state degradation
        finality_band = str(getattr(chain_state, "finality_band", "weak"))
        reorg_risk = float(getattr(chain_state, "reorg_risk_score", 1.0))
        if finality_band == "weak" or reorg_risk >= 0.7:
            dimensions["chain_state_degradation"] = "critical"
            conditions.append("Chain-state finality is weak or reorg risk is high")
            score += 3
            guidance.append("Pause non-essential broadcasts and require manual chain-state confirmation.")
        elif finality_band == "moderate" or reorg_risk >= 0.5:
            dimensions["chain_state_degradation"] = "warning"
            score += 1
        else:
            dimensions["chain_state_degradation"] = "ok"

        # recovery drift
        recovery_status = str(recovery_slo.get("status", "unknown"))
        unresolved = int(recovery_slo.get("signals", {}).get("unresolved_critical_findings", 0) or 0)
        if recovery_status == "critical" or unresolved >= 2:
            dimensions["recovery_drift"] = "critical"
            conditions.append("Recovery readiness SLO is critical")
            score += 3
            guidance.append("Run highest-priority recovery drill and clear unresolved critical findings.")
        elif recovery_status == "degraded":
            dimensions["recovery_drift"] = "warning"
            score += 1
        else:
            dimensions["recovery_drift"] = "ok"

        # delivery failure
        if failed_deliveries >= 5:
            dimensions["delivery_failure"] = "critical"
            conditions.append("Delivery failures exceeded critical threshold in 24h")
            score += 2
            guidance.append("Inspect delivery logs, destination health, and authentication constraints.")
        elif failed_deliveries > 0:
            dimensions["delivery_failure"] = "warning"
            score += 1
        else:
            dimensions["delivery_failure"] = "ok"

        # policy violation proxy from job failures
        if failed_jobs >= 10:
            dimensions["policy_violation"] = "critical"
            conditions.append("Job failures indicate potential policy/runtime enforcement violations")
            score += 2
        elif failed_jobs > 0:
            dimensions["policy_violation"] = "warning"
            score += 1
        else:
            dimensions["policy_violation"] = "ok"

        # operational backlog
        if failed_jobs >= 6:
            dimensions["operational_backlog"] = "critical"
            conditions.append("Failed job backlog exceeded safe threshold")
            score += 2
            guidance.append("Prioritize replay for safe idempotent jobs and defer non-critical workloads.")
        elif failed_jobs >= 2:
            dimensions["operational_backlog"] = "warning"
            score += 1
        else:
            dimensions["operational_backlog"] = "ok"

        level = "ok"
        if score >= 8:
            level = "critical"
        elif score >= 3:
            level = "warning"

        escalation_required = level == "critical" or len(conditions) >= 3
        if not guidance:
            guidance = ["Continue routine checks; no escalation required."]

        return RuntimeSeverityOut(
            level=level,
            escalation_required=escalation_required,
            score=score,
            dimensions=dimensions,
            escalation_conditions=conditions,
            operator_guidance=guidance[:5],
            explainability={
                "deterministic_model": True,
                "provider_share": round(provider_share, 3),
                "thresholds": {
                    "critical_score": 8,
                    "warning_score": 3,
                    "delivery_failure_critical_24h": 5,
                    "job_failure_critical_24h": 10,
                },
                "alert_fatigue_controls": {
                    "aggregate_score_required": True,
                    "condition_count_gate": 3,
                },
            },
        )

    @staticmethod
    def _degraded_mode(
        *,
        chain_state: object,
        mempool_state: object,
        failed_deliveries: int,
        provider_count_total: int,
    ) -> RuntimeDegradedModeOut:
        reasons: list[str] = []
        component_states: dict[str, str] = {}
        penalty = 0.0

        chain_freshness = str(getattr(chain_state, "freshness", {}).get("provider_freshness_band", "unknown"))
        chain_source = str(getattr(chain_state, "freshness", {}).get("source", "unknown"))
        if chain_source in {"provider_fallback", "repository_fallback"} or chain_freshness in {"stale", "very_stale"}:
            component_states["chain_state"] = "degraded"
            reasons.append("stale_chain_state")
            penalty += 0.2
        else:
            component_states["chain_state"] = "nominal"

        mempool_freshness = str(getattr(mempool_state, "freshness", {}).get("freshness_band", "unknown"))
        if mempool_freshness in {"stale", "very_stale"}:
            component_states["mempool"] = "degraded"
            reasons.append("stale_mempool_state")
            penalty += 0.15
        else:
            component_states["mempool"] = "nominal"

        if failed_deliveries > 0:
            component_states["delivery"] = "degraded"
            reasons.append("delivery_degradation")
            penalty += 0.12
        else:
            component_states["delivery"] = "nominal"

        if provider_count_total == 0:
            component_states["provider"] = "degraded"
            reasons.append("partial_provider_outage")
            penalty += 0.15
        else:
            component_states["provider"] = "nominal"

        partial_observability = provider_count_total == 0
        component_states["observability"] = "partial_outage" if partial_observability else "nominal"
        if partial_observability:
            reasons.append("partial_observability_outage")
            penalty += 0.1

        active = len(reasons) > 0
        return RuntimeDegradedModeOut(
            active=active,
            reasons=sorted(set(reasons)),
            component_states=component_states,
            confidence_penalty=round(min(0.6, penalty), 3),
            explainability={
                "explicit_mode": True,
                "silent_failure_prevention": True,
                "fallback_confidence_reduction_applied": active,
            },
        )

    @staticmethod
    def _operational_evidence_packet(
        *,
        runtime_severity: RuntimeSeverityOut,
        degraded_mode: RuntimeDegradedModeOut,
        recovery: object,
        provider_name: str,
        provider_share: float,
        failed_deliveries: int,
        sent_deliveries: int,
        chain_state: object,
    ) -> OperationalEvidencePacketOut:
        unresolved = int(getattr(recovery, "recovery_slo", {}).get("signals", {}).get("unresolved_critical_findings", 0) or 0)
        recovery_status = str(getattr(recovery, "recovery_slo", {}).get("status", "unknown"))
        drill = dict(getattr(recovery, "drill_execution", {}))
        quality = getattr(chain_state, "freshness", {})
        confidence = propagate_confidence(
            base_confidence=max(0.35, 1.0 - float(getattr(chain_state, "reorg_risk_score", 1.0))),
            freshness_band=str(quality.get("provider_freshness_band", "unknown")),
            is_fallback=bool(quality.get("is_fallback", False)),
        )
        confidence = round(max(0.05, confidence - float(degraded_mode.confidence_penalty)), 4)

        packet = build_audit_packet(
            packet_type="operational_runtime_evidence",
            evidence_refs=[
                "observability.snapshot",
                f"provider:{provider_name}",
                f"runtime_severity:{runtime_severity.level}",
                f"recovery_slo:{recovery_status}",
            ],
            source_quality={
                "provider_name": provider_name,
                "provider_share": round(provider_share, 3),
                "provider_freshness_band": quality.get("provider_freshness_band", "unknown"),
                "is_fallback": bool(quality.get("is_fallback", False)),
            },
            confidence=confidence,
            transformations=["runtime_severity_model", "degraded_mode_mapping", "recovery_slo_projection"],
            policy_context={"escalation_required": runtime_severity.escalation_required},
            recommendation_rationale="Operational evidence packet summarizes runtime risk posture for operators.",
            lineage=[{"domain": "observability", "reference": "operations_snapshot", "confidence": confidence}],
        )

        return OperationalEvidencePacketOut(
            packet_type=str(packet.get("packet_type", "operational_runtime_evidence")),
            runtime_state=("degraded" if degraded_mode.active else "nominal"),
            degraded_dependencies=list(degraded_mode.reasons)[:8],
            provider_quality=dict(packet.get("source_quality", {})),
            unresolved_critical_findings=unresolved,
            delivery_health={
                "failed_24h": failed_deliveries,
                "sent_24h": sent_deliveries,
                "degraded": failed_deliveries > 0,
            },
            drill_status={
                "next_drill_code": drill.get("next_drill_code", "routine_recovery_probe"),
                "next_drill_priority": drill.get("next_drill_priority", "low"),
                "automated_drills_ready": bool(drill.get("automated_drills_ready", False)),
            },
            recovery_slo_status=recovery_status,
            confidence=confidence,
            evidence_refs=list(packet.get("evidence_refs", []))[:8],
            explainability={
                "severity_level": runtime_severity.level,
                "escalation_conditions": runtime_severity.escalation_conditions[:6],
                "degraded_mode_active": degraded_mode.active,
            },
        )

    def snapshot(self, db: Session) -> OperationsSnapshotOut:
        jobs = JobRunRepository(db)
        deliveries = DeliveryRepository(db)
        onchain = OnchainRepository(db)

        failed_jobs = jobs.failed_count_last_24h()
        failed_deliveries = deliveries.failed_count_last_24h()
        observed_block_height = onchain.latest_block_height() or 899_995
        provider_counts = onchain.provider_counts_last_24h()
        provider_count_total = sum(count for _, count in provider_counts)
        chain_state = ChainStateService().evaluate(
            tip_height=observed_block_height + 1,
            observed_block_height=observed_block_height,
            headers_height=observed_block_height + 1,
        )
        mempool_state = MempoolAnalyzerService().analyze(
            MempoolSnapshot(
                backlog_tx_count=75_000,
                backlog_vbytes=95_000_000,
                median_fee_rate_sat_vb=18.0,
                high_priority_fee_rate_sat_vb=42.0,
                snapshot_age_seconds=900 if provider_count_total == 0 else 180,
            )
        )
        recovery = RecoveryCheckService().evaluate(db=db)
        provider_name = provider_counts[0][0] if provider_counts else "unknown"
        provider_share = (
            round(provider_counts[0][1] / provider_count_total, 3)
            if provider_counts and provider_count_total > 0
            else 0.0
        )

        runtime_severity = self._runtime_severity(
            failed_jobs=failed_jobs,
            failed_deliveries=failed_deliveries,
            provider_share=provider_share,
            provider_count_total=provider_count_total,
            chain_state=chain_state,
            recovery_slo=recovery.recovery_slo,
        )
        degraded_mode = self._degraded_mode(
            chain_state=chain_state,
            mempool_state=mempool_state,
            failed_deliveries=failed_deliveries,
            provider_count_total=provider_count_total,
        )
        unresolved_findings = int(recovery.recovery_slo.get("signals", {}).get("unresolved_critical_findings", 0) or 0)
        operational_evidence = self._operational_evidence_packet(
            runtime_severity=runtime_severity,
            degraded_mode=degraded_mode,
            recovery=recovery,
            provider_name=provider_name,
            provider_share=provider_share,
            failed_deliveries=failed_deliveries,
            sent_deliveries=deliveries.sent_count_last_24h(),
            chain_state=chain_state,
        )

        set_observability_runtime_metrics(
            severity_score=runtime_severity.score,
            degraded_mode_active=degraded_mode.active,
            provider_name=provider_name,
            provider_share=provider_share,
            delivery_failures_24h=failed_deliveries,
            unresolved_critical_findings=unresolved_findings,
            citadel_runtime_healthy=(recovery.recovery_slo.get("status") == "healthy"),
        )

        health_evidence = ProviderHealthService().collect(db=db)
        providers: list[ProviderHealthOut] = []
        for evidence in health_evidence:
            set_provider_health_state_metric(
                provider_type=evidence.provider_type,
                provider_name=evidence.provider_name,
                healthy=evidence.healthy,
                is_fallback=evidence.is_fallback,
                is_mock=evidence.is_mock,
            )
            stale_evidence = evidence.freshness_seconds >= 1800
            degradation_reason = None if evidence.healthy else (evidence.error_type or "provider_unhealthy")
            guidance = ["Continue routine provider checks."] if evidence.healthy else ["Verify provider runtime and failover path.", "Review sanitized provider errors and refresh evidence."]
            set_provider_health_detail_metrics(
                provider_type=evidence.provider_type,
                provider_name=evidence.provider_name,
                latency_ms=evidence.latency_ms,
                is_fallback=evidence.is_fallback,
                confidence=evidence.confidence,
                last_success_age_seconds=evidence.freshness_seconds if evidence.healthy else max(evidence.freshness_seconds, 1),
            )
            if not evidence.healthy:
                increment_provider_failure_metric(
                    provider_type=evidence.provider_type,
                    provider_name=evidence.provider_name,
                    error_type=evidence.error_type,
                )
            providers.append(
                ProviderHealthOut(
                    provider=evidence.provider_type,
                    provider_name=evidence.provider_name,
                    healthy=evidence.healthy,
                    details=(
                        f"provider={evidence.provider_name} source_type={evidence.source_type} "
                        f"fallback={evidence.is_fallback} mock={evidence.is_mock} "
                        f"error_type={evidence.error_type or 'none'}"
                    ),
                    confidence=evidence.confidence,
                    freshness_seconds=evidence.freshness_seconds,
                    stale_evidence=stale_evidence,
                    is_fallback=evidence.is_fallback,
                    is_mock=evidence.is_mock,
                    degradation_reason=degradation_reason,
                    operator_guidance=guidance,
                )
            )

        return OperationsSnapshotOut(
            queue_depth=0,
            stale_jobs=failed_jobs,
            providers=providers,
            jobs=JobStatsOut(
                started_24h=jobs.started_count_last_24h(),
                failed_24h=failed_jobs,
            ),
            deliveries=DeliveryStatsOut(
                sent_24h=deliveries.sent_count_last_24h(),
                failed_24h=failed_deliveries,
            ),
            chain_state=ChainStateOut.model_validate(chain_state, from_attributes=True),
            recovery_slo=RecoverySLOOut.model_validate(recovery.recovery_slo),
            runtime_severity=runtime_severity,
            degraded_mode=degraded_mode,
            operational_evidence=operational_evidence,
        )
