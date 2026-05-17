from __future__ import annotations

from app.schemas.mining import (
    MiningExplainabilityOut,
    StratumV2AdoptionSummaryOut,
    StratumV2CapabilityEvaluationInput,
    StratumV2CapabilityEvaluationOut,
)
from app.db.repositories.mining_repository import MiningRepository
from app.services.mining.source_quality import calculate_source_quality_confidence

ALLOWED_STATUSES = {"supported", "unsupported", "partial", "unknown", "claimed_unverified", "verified"}


class StratumV2CapabilityService:
    def __init__(self, repository: MiningRepository | None = None) -> None:
        self.repository = repository

    def evaluate(self, payload: StratumV2CapabilityEvaluationInput) -> StratumV2CapabilityEvaluationOut:
        statuses = payload.model_dump()
        capability_fields = {
            "supports_stratum_v2",
            "supports_job_declaration",
            "supports_template_distribution",
            "supports_template_provider",
            "supports_translator_proxy",
            "supports_encrypted_channel",
            "miner_can_build_templates",
            "pool_can_override_templates",
            "miner_template_control_level",
        }
        normalized: dict[str, str] = {
            k: (v if isinstance(v, str) and v in ALLOWED_STATUSES else "unknown") for k, v in statuses.items() if k in capability_fields
        }

        # Hard guard: no false verified status.
        if normalized.get("supports_stratum_v2") in {"unknown", "unsupported", "partial"}:
            normalized = {k: ("claimed_unverified" if v == "verified" else v) for k, v in normalized.items()}

        positive: list[str] = []
        negative: list[str] = []
        missing: list[str] = []
        score = 0.0
        weights = {
            "verified": 1.0,
            "supported": 0.85,
            "claimed_unverified": 0.6,
            "partial": 0.4,
            "unknown": 0.2,
            "unsupported": 0.0,
        }

        for field_name, status in normalized.items():
            score += weights[status]
            label = field_name.replace("_", " ")
            if status in {"verified", "supported"}:
                positive.append(f"{label}: {status}")
            elif status in {"unsupported", "partial", "unknown"}:
                negative.append(f"{label}: {status}")
            if status in {"unsupported", "unknown", "partial"}:
                missing.append(field_name)

        max_score = float(len(normalized)) or 1.0
        capability_confidence = score / max_score
        source_quality = calculate_source_quality_confidence(
            source_type=payload.source_type,
            freshness_seconds=payload.freshness_seconds,
            is_fallback=payload.is_fallback,
            is_synthetic=payload.is_synthetic,
            is_verified=payload.is_verified,
        )
        confidence = (capability_confidence + payload.confidence + source_quality.confidence) / 3.0
        if any(v == "unknown" for v in normalized.values()):
            confidence = max(0.0, confidence - 0.1)
        confidence = min(1.0, max(0.0, round(confidence, 4)))

        summary = self._summary_from_statuses(normalized)
        notes = list(payload.limitations)
        if any(v == "claimed_unverified" for v in normalized.values()):
            notes.append("Claims are unverified; no active network probing is performed in M2-02.")

        return StratumV2CapabilityEvaluationOut(
            capability_summary=summary,
            missing_capabilities=missing,
            positive_factors=positive,
            negative_factors=negative,
            confidence=confidence,
            limitations=notes,
            explainability=MiningExplainabilityOut(
                drivers=positive[:4],
                factor_breakdown=[{"capability": k, "status": v} for k, v in normalized.items()],
                source_quality_impact=[
                    f"source_type={payload.source_type}",
                    f"base_confidence={payload.confidence}",
                    f"source_base_score={source_quality.base_score}",
                    f"freshness_penalty={source_quality.freshness_penalty}",
                    f"fallback_penalty={source_quality.fallback_penalty}",
                    f"synthetic_penalty={source_quality.synthetic_penalty}",
                    f"verification_boost={source_quality.verification_boost}",
                ],
                notes=notes,
            ),
            statuses=normalized,
        )

    def summarize_adoption(self) -> StratumV2AdoptionSummaryOut:
        if self.repository is None:
            raise ValueError("repository is required for adoption summary")

        pools = self.repository.list_pools(limit=10000, offset=0)
        total_pools = len(pools)
        latest = self.repository.list_latest_stratum_v2_capabilities()

        sv2_supported = 0
        job_supported = 0
        template_control_supported = 0
        unknown_count = 0
        claimed_unverified_count = 0
        confidence_sum = 0.0

        for cap in latest:
            if cap.capability_state in {"supported", "verified"}:
                sv2_supported += 1
            if cap.job_declaration_state in {"supported", "verified"}:
                job_supported += 1
            if cap.translator_proxy_state in {"supported", "verified"}:
                template_control_supported += 1
            if (
                cap.capability_state == "unknown"
                or cap.job_declaration_state == "unknown"
                or cap.translator_proxy_state == "unknown"
            ):
                unknown_count += 1
            if (
                cap.capability_state == "claimed_unverified"
                or cap.job_declaration_state == "claimed_unverified"
                or cap.translator_proxy_state == "claimed_unverified"
                or cap.encrypted_channel_state == "claimed_unverified"
            ):
                claimed_unverified_count += 1
            confidence_sum += float(cap.confidence_score)

        adoption_rate = (sv2_supported / total_pools) if total_pools > 0 else 0.0
        base_confidence = (confidence_sum / len(latest)) if latest else 0.0
        if total_pools > len(latest):
            base_confidence = max(0.0, base_confidence - 0.15)
        if unknown_count > 0:
            base_confidence = max(0.0, base_confidence - 0.1)

        limitations = [
            "Adoption rate excludes unknown as supported and is advisory.",
            "Claimed-unverified statuses are tracked separately from verified support.",
        ]
        if total_pools != len(latest):
            limitations.append("Some pools do not yet have capability snapshots.")
        if unknown_count > 0:
            limitations.append("Unknown capability states reduce confidence in adoption summary.")

        return StratumV2AdoptionSummaryOut(
            total_pools=total_pools,
            sv2_supported_count=sv2_supported,
            job_declaration_supported_count=job_supported,
            template_control_supported_count=template_control_supported,
            unknown_count=unknown_count,
            claimed_unverified_count=claimed_unverified_count,
            adoption_rate=round(adoption_rate, 4),
            confidence=round(min(1.0, max(0.0, base_confidence)), 4),
            limitations=limitations,
            explainability=MiningExplainabilityOut(
                drivers=[
                    f"total_pools={total_pools}",
                    f"snapshot_pools={len(latest)}",
                    f"sv2_supported_count={sv2_supported}",
                ],
                factor_breakdown=[
                    {"metric": "adoption_rate", "value": round(adoption_rate, 4)},
                    {"metric": "unknown_count", "value": unknown_count},
                    {"metric": "claimed_unverified_count", "value": claimed_unverified_count},
                ],
                source_quality_impact=[f"confidence={round(min(1.0, max(0.0, base_confidence)), 4)}"],
                notes=limitations,
            ),
        )

    @staticmethod
    def _summary_from_statuses(statuses: dict[str, str]) -> str:
        if all(value in {"verified", "supported"} for value in statuses.values()):
            return "Strong Stratum V2 capability posture with broad support across evaluated dimensions."
        if any(value == "unsupported" for value in statuses.values()):
            return "Capability posture includes unsupported dimensions and requires remediation."
        if any(value == "partial" for value in statuses.values()):
            return "Capability posture is partial; some Stratum V2 features are incomplete."
        if any(value == "claimed_unverified" for value in statuses.values()):
            return "Capabilities are reported as claimed-unverified and require independent validation."
        return "Capability posture is uncertain due to unknown or low-confidence inputs."
