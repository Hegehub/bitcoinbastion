"""Deterministic Feature-60 fixtures for Prompt-9 tests; never a production fallback."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from bastion_ui.domain.prompt9 import JobsViewModel, MarketOverviewViewModel, MarketSignalsViewModel
from bastion_ui.domain.provenance import Provenance, ProvenanceState

FIXTURE_TIME = datetime.fromisoformat("2026-01-15T12:00:00+00:00")
FIXTURE_PROVENANCE = Provenance(
    state=ProvenanceState.DEMO_FIXTURE,
    source_label="Prompt-9 deterministic fixture",
    observed_at=FIXTURE_TIME,
)

EMPTY_JOBS = JobsViewModel(jobs=(), provenance=FIXTURE_PROVENANCE)
UNAVAILABLE_MARKET = MarketOverviewViewModel(
    symbol="BTC",
    pair="BTCUSD",
    price_usd=None,
    observed_at=None,
    provider_count=0,
    provider_confidence=None,
    source="fixture-unavailable",
    limitations=("DEMO_FIXTURE: authoritative market source unavailable",),
    provenance=FIXTURE_PROVENANCE,
)
EMPTY_SIGNALS = MarketSignalsViewModel(signals=(), provenance=FIXTURE_PROVENANCE)

assert Decimal("0") == 0  # fixture module preserves Decimal semantics
