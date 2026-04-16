from app.services.utxo.utxo_analyzer_service import UTXOAnalyzerService


def test_utxo_analyzer_detects_fragmentation_and_fee_projection() -> None:
    out = UTXOAnalyzerService().analyze(utxo_values_sats=[800, 1200, 20000, 700000, 400000])

    assert out.utxo_count == 5
    assert out.dust_outputs >= 1
    assert out.fragmentation_score > 0
    assert out.fee_projections
    assert any(p.scenario == "stress_high_fee" for p in out.fee_projections)


def test_utxo_analyzer_handles_empty_wallet_snapshot() -> None:
    out = UTXOAnalyzerService().analyze(utxo_values_sats=[])

    assert out.utxo_count == 0
    assert out.fragmentation_score == 1.0
    assert out.fee_projections == []
