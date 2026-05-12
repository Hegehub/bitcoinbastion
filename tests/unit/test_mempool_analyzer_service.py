from app.services.mempool.mempool_analyzer_service import MempoolAnalyzerService, MempoolSnapshot


def _snapshot(backlog_vbytes: int, median: float, high: float, age: int | None = 15) -> MempoolSnapshot:
    return MempoolSnapshot(
        backlog_tx_count=max(1, backlog_vbytes // 1000),
        backlog_vbytes=backlog_vbytes,
        median_fee_rate_sat_vb=median,
        high_priority_fee_rate_sat_vb=high,
        snapshot_age_seconds=age,
    )


def test_mempool_state_classifies_low_normal_elevated_congested_extreme() -> None:
    service = MempoolAnalyzerService()
    assert service.analyze(_snapshot(10_000_000, 3, 8)).congestion_state == "low"
    assert service.analyze(_snapshot(40_000_000, 7, 15)).congestion_state == "normal"
    assert service.analyze(_snapshot(80_000_000, 20, 40)).congestion_state == "elevated"
    assert service.analyze(_snapshot(150_000_000, 35, 80)).congestion_state == "congested"
    assert service.analyze(_snapshot(220_000_000, 55, 150)).congestion_state == "extreme"


def test_mempool_state_marks_stale_snapshots_and_reduces_confidence() -> None:
    service = MempoolAnalyzerService()
    fresh = service.analyze(_snapshot(80_000_000, 20, 45, age=20))
    stale = service.analyze(_snapshot(80_000_000, 20, 45, age=900))

    assert fresh.freshness["freshness_band"] == "fresh"
    assert stale.freshness["freshness_band"] == "very_stale"
    assert stale.confidence < fresh.confidence


def test_mempool_priority_bands_are_monotonic() -> None:
    state = MempoolAnalyzerService().analyze(_snapshot(100_000_000, 25, 60))
    assert state.priority_bands["low"] <= state.priority_bands["medium"]
    assert state.priority_bands["medium"] <= state.priority_bands["high"]
    assert state.priority_bands["high"] <= state.priority_bands["urgent"]


def test_mempool_state_exposes_source_quality_labels() -> None:
    state = MempoolAnalyzerService().analyze(_snapshot(70_000_000, 14, 35, age=45))
    assert state.freshness["source_type"] == "runtime"
    assert state.freshness["provider_name"] == "unknown"
    assert state.freshness["is_mock"] is False
    assert state.freshness["is_fallback"] is False
    assert state.explainability["limitations"]
