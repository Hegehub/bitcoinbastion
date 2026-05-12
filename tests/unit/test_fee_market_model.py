from app.services.mempool.fee_market_model import FeeMarketModel
from app.services.mempool.mempool_analyzer_service import MempoolAnalyzerService, MempoolSnapshot


def _state(vbytes: int, median: float, high: float, age: int = 20):
    snap = MempoolSnapshot(
        backlog_tx_count=max(1, vbytes // 1000),
        backlog_vbytes=vbytes,
        median_fee_rate_sat_vb=median,
        high_priority_fee_rate_sat_vb=high,
        snapshot_age_seconds=age,
    )
    return MempoolAnalyzerService().analyze(snap)


def test_fee_market_target_blocks_affect_recommendation() -> None:
    state = _state(80_000_000, 20, 40)
    fast = FeeMarketModel().estimate(mempool=state, target_blocks=1)
    slow = FeeMarketModel().estimate(mempool=state, target_blocks=12)

    assert fast.suggested_fee_rate_sat_vb > slow.suggested_fee_rate_sat_vb


def test_fee_market_congestion_materially_changes_fee_output() -> None:
    low = _state(15_000_000, 3, 9)
    extreme = _state(220_000_000, 60, 160)

    low_out = FeeMarketModel().estimate(mempool=low, target_blocks=3)
    extreme_out = FeeMarketModel().estimate(mempool=extreme, target_blocks=3)

    assert extreme_out.suggested_fee_rate_sat_vb > low_out.suggested_fee_rate_sat_vb
    assert extreme_out.high_fee_scenario_sat_vb > extreme_out.suggested_fee_rate_sat_vb


def test_fee_market_stale_freshness_reduces_confidence() -> None:
    fresh = _state(90_000_000, 25, 55, age=20)
    stale = _state(90_000_000, 25, 55, age=1_000)

    fresh_out = FeeMarketModel().estimate(mempool=fresh, target_blocks=3)
    stale_out = FeeMarketModel().estimate(mempool=stale, target_blocks=3)

    assert stale_out.confidence < fresh_out.confidence
    assert stale_out.explainability["assumptions"]
