from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict

from bastion_ui.domain.provenance import Provenance, ProvenanceState
from bastion_ui.transport.generated_http import (
    JobsApiV1OperationsJobsGetSuccess,
    MarketCurrentOverviewSuccess,
    TopSignalsApiV1SignalsTopGetSuccess,
)


class JobViewModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    name: str
    status: str
    started_at: datetime | None
    finished_at: datetime | None
    duration_ms: int | None
    next_run_at: datetime | None
    retry_count: int | None
    safe_failure_summary: str | None


class JobsViewModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    jobs: tuple[JobViewModel, ...]
    provenance: Provenance


class MarketOverviewViewModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    symbol: str
    pair: str
    price_usd: Decimal | None
    observed_at: datetime | None
    provider_count: int
    provider_confidence: Decimal | None
    source: str
    limitations: tuple[str, ...]
    provenance: Provenance


class MarketSignalViewModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    signal_id: int
    signal_type: str
    title: str
    summary: str
    severity: str
    confidence: Decimal
    backend_score: Decimal
    publication_status: str
    observed_at: datetime
    stale: bool | None
    stale_reason: str | None


class MarketSignalsViewModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    signals: tuple[MarketSignalViewModel, ...]
    provenance: Provenance


def _live(source: str, observed_at: datetime | None) -> Provenance:
    return Provenance(
        state=ProvenanceState.LIVE,
        source_label=source,
        observed_at=observed_at or datetime.now(UTC),
    )


def adapt_jobs(response: JobsApiV1OperationsJobsGetSuccess) -> JobsViewModel:
    jobs = tuple(
        JobViewModel(
            name=item.job_name,
            status=item.health_state or "unknown",
            started_at=item.last_start_at,
            finished_at=item.last_finish_at,
            duration_ms=item.duration_ms,
            next_run_at=item.next_scheduled_at,
            retry_count=item.retry_count,
            # Backend exposes only a bounded failure_reason. Worker identity is omitted.
            safe_failure_summary=item.failure_reason or None,
        )
        for item in response.root
    )
    observed_values = [
        value for item in jobs if (value := item.finished_at or item.started_at) is not None
    ]
    observed = max(observed_values, default=None)
    return JobsViewModel(jobs=jobs, provenance=_live("Operations jobs health API", observed))


def adapt_market_overview(response: MarketCurrentOverviewSuccess) -> MarketOverviewViewModel:
    item = response.root.data
    return MarketOverviewViewModel(
        symbol=item.symbol,
        pair=item.pair,
        price_usd=Decimal(item.price_usd) if item.price_usd is not None else None,
        observed_at=item.observed_at,
        provider_count=item.provider_count,
        provider_confidence=(
            Decimal(item.provider_confidence) if item.provider_confidence is not None else None
        ),
        source=item.source,
        limitations=tuple(item.limitations),
        provenance=_live(item.source, item.observed_at),
    )


def adapt_market_signals(response: TopSignalsApiV1SignalsTopGetSuccess) -> MarketSignalsViewModel:
    items = response.root.data.items
    signals = tuple(
        MarketSignalViewModel(
            signal_id=item.id,
            signal_type=item.signal_type,
            title=item.title,
            summary=item.summary,
            severity=item.severity,
            confidence=item.confidence,
            backend_score=item.score,
            publication_status="published" if item.is_published else "not published",
            observed_at=item.created_at,
            stale=item.freshness.is_stale if item.freshness is not None else None,
            stale_reason=item.freshness.stale_reason if item.freshness is not None else None,
        )
        for item in items
    )
    observed = max((item.observed_at for item in signals), default=None)
    return MarketSignalsViewModel(signals=signals, provenance=_live("Signals API", observed))
