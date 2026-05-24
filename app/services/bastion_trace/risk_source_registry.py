import json
from app.db.repositories.bastion_trace_repository import BastionTraceRepository
from app.schemas.bastion_trace import TraceSourceStatus, TraceSourceType, TraceSourceTrustLevel
from app.services.bastion_trace.source_freshness import evaluate_source_freshness


class RiskSourceRegistryService:
    BASELINE_SOURCES = [
        "baseline_internal_rules",
        "baseline_address_validator",
        "baseline_scoring_engine",
        "baseline_origin_classifier",
    ]

    def __init__(self, repo: BastionTraceRepository) -> None:
        self.repo = repo

    def ensure_baseline_sources(self) -> None:
        existing = {s.source_name for s in self.repo.list_sources()}
        for name in self.BASELINE_SOURCES:
            if name in existing:
                continue
            self.repo.create_source(
                source_name=name,
                source_type=TraceSourceType.SYNTHETIC_BASELINE.value,
                trust_level=TraceSourceTrustLevel.LOW.value,
                enabled=True,
                limitations=["baseline_source_not_external_provider"],
            )

    def list_sources(self) -> list[TraceSourceStatus]:
        self.ensure_baseline_sources()
        records = self.repo.list_sources()
        out: list[TraceSourceStatus] = []
        for item in records:
            freshness = evaluate_source_freshness(item.updated_at)
            out.append(
                TraceSourceStatus(
                    id=item.id,
                    source_name=item.source_name,
                    source_type=TraceSourceType(item.source_type),
                    trust_level=TraceSourceTrustLevel(item.trust_level),
                    enabled=item.enabled,
                    freshness=freshness,
                    confidence=0.3,
                    last_refreshed_at=item.updated_at,
                    last_refresh_status="baseline",
                    limitations=json.loads(item.limitations_json),
                    is_internal=True,
                    is_external=False,
                    is_synthetic=item.source_type == TraceSourceType.SYNTHETIC_BASELINE.value,
                    is_node_backed=False,
                )
            )
        return out

    def get_source(self, source_name: str) -> TraceSourceStatus | None:
        for source in self.list_sources():
            if source.source_name == source_name:
                return source
        return None
