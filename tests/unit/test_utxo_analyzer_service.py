from app.services.utxo.utxo_analyzer_service import UTXOAnalyzerService


def test_utxo_analyzer_detects_dust_heavy_wallet() -> None:
    out = UTXOAnalyzerService().analyze(utxo_values_sats=[200, 300, 400, 500, 2_000])

    assert out.wallet_profile == "dust_heavy"
    assert out.dust_ratio >= 0.6
    assert out.consolidation_candidates_ranked


def test_utxo_analyzer_detects_fragmented_wallet() -> None:
    out = UTXOAnalyzerService().analyze(utxo_values_sats=[5_000, 7_000, 9_000, 12_000, 450_000])

    assert out.fragmentation_score > 0.4
    assert out.wallet_profile in {"fragmented", "many_small_utxos"}


def test_utxo_analyzer_handles_single_whale_utxo_wallet() -> None:
    out = UTXOAnalyzerService().analyze(utxo_values_sats=[5_000_000])

    assert out.wallet_profile == "single_whale_utxo"
    assert out.estimated_inputs_to_spend_1m_sats == 1
    assert out.urgent_spend_feasible is True


def test_utxo_analyzer_flags_many_small_utxos_and_high_fee_stress() -> None:
    values = [15_000] * 120
    out = UTXOAnalyzerService().analyze(utxo_values_sats=values)

    assert out.wallet_profile == "many_small_utxos"
    assert any(p.scenario == "stress_emergency_fee" for p in out.fee_projections)
    assert out.high_fee_burden_ratio > 0


def test_utxo_analyzer_detects_insufficient_liquidity_for_urgent_spend() -> None:
    out = UTXOAnalyzerService().analyze(
        utxo_values_sats=[50_000, 60_000], target_spend_sats=1_000_000
    )

    assert out.urgent_spend_feasible is False
    assert out.liquidity_shortfall_sats > 0


def test_utxo_analyzer_ranks_consolidation_candidates_dust_first() -> None:
    out = UTXOAnalyzerService().analyze(utxo_values_sats=[500, 900, 1_500, 20_000, 30_000, 500_000])

    ranked = out.consolidation_candidates_ranked
    assert ranked[:2] == [500, 900]


def test_utxo_analyzer_handles_empty_wallet_snapshot() -> None:
    out = UTXOAnalyzerService().analyze(utxo_values_sats=[])

    assert out.utxo_count == 0
    assert out.fragmentation_score == 1.0
    assert out.fee_projections == []
    assert out.wallet_profile == "empty"
    assert out.freshness["is_fallback"] is True


def test_utxo_analyzer_exposes_source_quality_labels() -> None:
    out = UTXOAnalyzerService().analyze(utxo_values_sats=[900, 1500, 30000, 500000])
    assert out.freshness["source_type"] == "runtime"
    assert out.freshness["provider_name"] == "unknown"
    assert out.freshness["is_fallback"] is False
    assert out.explainability["source_quality"]["limitations"]
