from app.services.mempool.fee_market_model import FeeMarketModel
from app.services.mempool.mempool_analyzer_service import MempoolAnalyzerService, MempoolSnapshot


def test_mempool_analyzer_classifies_congestion() -> None:
    state = MempoolAnalyzerService().analyze(
        MempoolSnapshot(
            backlog_tx_count=120_000,
            backlog_vbytes=130_000_000,
            median_fee_rate_sat_vb=35,
            high_priority_fee_rate_sat_vb=78,
        )
    )

    assert state.congestion_state == "severe"
    assert state.priority_bands["high"] >= state.priority_bands["medium"]


def test_fee_market_model_reflects_target_urgency() -> None:
    mempool = MempoolAnalyzerService().analyze(
        MempoolSnapshot(
            backlog_tx_count=80_000,
            backlog_vbytes=70_000_000,
            median_fee_rate_sat_vb=20,
            high_priority_fee_rate_sat_vb=40,
        )
    )

    fast = FeeMarketModel().estimate(mempool=mempool, target_blocks=2)
    slow = FeeMarketModel().estimate(mempool=mempool, target_blocks=12)

    assert fast.suggested_fee_rate_sat_vb > slow.suggested_fee_rate_sat_vb
    assert fast.high_fee_scenario_sat_vb >= fast.suggested_fee_rate_sat_vb
