from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from bastion_ui.domain.operations.models import (
    HealthViewModel,
    IncidentsViewModel,
    IncidentViewModel,
    IntelligenceHealthViewModel,
    OperationsSLOListViewModel,
    OperationsSLOViewModel,
    ProvidersViewModel,
    ProviderViewModel,
    StorageStoreViewModel,
    StorageViewModel,
)
from bastion_ui.domain.provenance import Provenance, ProvenanceState
from bastion_ui.transport.generated_http import (
    HealthApiV1HealthGetSuccess,
    IntelligenceHealthIntelligenceGetSuccess,
    OperationsListIncidentsSuccess,
    OperationsListSloSuccess,
    ProvidersApiV1HealthProvidersGetSuccess,
    StorageStatusApiV1StorageStatusGetSuccess,
)


def adapt_intelligence_health(
    response: IntelligenceHealthIntelligenceGetSuccess,
) -> IntelligenceHealthViewModel:
    payload = response.root
    return IntelligenceHealthViewModel(
        status=payload.status,
        degraded=payload.degraded_state,
        provider_confidence=payload.provider_confidence,
        last_success=payload.last_success,
        last_failure=payload.last_failure,
        limitations=(
            tuple(payload.operational_limitations)
            if payload.operational_limitations is not None
            else None
        ),
    )


def _live(source: str, observed_at: datetime | None) -> Provenance:
    return Provenance(
        state=ProvenanceState.LIVE,
        source_label=source,
        observed_at=observed_at or datetime.now(UTC),
    )


def adapt_health(
    response: HealthApiV1HealthGetSuccess, *, observed_at: datetime | None = None
) -> HealthViewModel:
    payload = response.root
    return HealthViewModel(
        application=payload.app,
        status=payload.status,
        details=tuple(sorted((payload.details or {}).items())),
        provenance=_live("Bitcoin Bastion health API", observed_at),
    )


def adapt_providers(
    response: ProvidersApiV1HealthProvidersGetSuccess, *, observed_at: datetime | None = None
) -> ProvidersViewModel:
    return ProvidersViewModel(
        providers=tuple(
            ProviderViewModel(
                name=item.provider_name,
                provider_type=item.provider_type,
                state=item.health_state or "unknown",
                last_success_at=item.last_success_at,
                last_failure_at=item.last_failure_at,
                latency_ms=item.avg_latency_ms,
                failure_count=item.failure_count,
            )
            for item in sorted(response.root, key=lambda value: value.provider_name.casefold())
        ),
        provenance=_live("Bitcoin Bastion provider health API", observed_at),
    )


def adapt_storage(
    response: StorageStatusApiV1StorageStatusGetSuccess, *, observed_at: datetime | None = None
) -> StorageViewModel:
    payload = response.root
    # `details` is intentionally excluded: backend drivers may add infrastructure metadata.
    return StorageViewModel(
        status=payload.status.root,
        profile=payload.profile,
        required_ok=payload.summary.required_ok,
        critical_failures=payload.summary.critical_failures,
        warnings=payload.summary.warnings,
        degraded=payload.degraded_mode.active,
        degraded_reason=payload.degraded_mode.reason,
        degraded_impact=tuple(payload.degraded_mode.impact or ()),
        stores=tuple(
            StorageStoreViewModel(
                name=name,
                status=store.status.root,
                role=store.role.root,
                purpose=store.purpose,
                latency_ms=store.latency_ms,
            )
            for name, store in sorted(payload.stores.items())
        ),
        provenance=_live("Bitcoin Bastion storage status API", observed_at),
    )


def adapt_incidents(response: OperationsListIncidentsSuccess) -> IncidentsViewModel:
    values = tuple(
        IncidentViewModel(
            incident_id=item.incident_id,
            severity=item.severity.root,
            status=item.status.root,
            target=item.affected_target,
            summary=item.summary,
            source=item.source,
            limitations=item.limitations,
            opened_at=item.opened_at,
            updated_at=item.updated_at,
            resolved_at=item.resolved_at,
        )
        for item in response.root
    )
    observed = max((item.updated_at for item in values), default=None)
    return IncidentsViewModel(
        incidents=values, provenance=_live("Operations incident detector", observed)
    )


def adapt_operations_slo(response: OperationsListSloSuccess) -> OperationsSLOListViewModel:
    values = tuple(
        OperationsSLOViewModel(
            slo_id=item.slo_id,
            title=item.title,
            service=item.service,
            indicator=item.indicator_id,
            target=Decimal(item.target),
            current=Decimal(item.current) if item.current is not None else None,
            unit=item.unit.root,
            comparison=item.comparison.root,
            window_seconds=item.window_seconds,
            status=item.status.root,
            sample_count=item.sample_count,
            observed_at=item.observed_at,
            source=item.source,
            limitations=item.limitations,
        )
        for item in response.root
    )
    observed = max((item.observed_at for item in values), default=None)
    return OperationsSLOListViewModel(
        objectives=values, provenance=_live("Operations SLO evaluator", observed)
    )
