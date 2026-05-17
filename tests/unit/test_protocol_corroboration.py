from app.services.blockchain.chain_state_service import ChainStateService
from app.services.mempool.mempool_analyzer_service import MempoolAnalyzerService, MempoolSnapshot
from app.services.utxo.utxo_analyzer_service import UTXOAnalyzerService


def test_chain_state_protocol_corroboration_fields_present() -> None:
    out = ChainStateService().evaluate(
        tip_height=900_000,
        observed_block_height=899_998,
        data_source="provider_probe",
        provider_count=1,
        corroborated_by=["esplora"],
        conflicting_providers=["provider_b"],
    )
    f = out.freshness
    for key in [
        "provider_count","corroborated_by","conflicting_providers","confidence_adjustment","freshness_band",
        "fallback_active","single_source_advisory","advisory_not_consensus_proof","operator_guidance","limitations",
    ]:
        assert key in f
    assert f["single_source_advisory"] is True


def test_mempool_and_utxo_protocol_advisory_flags() -> None:
    mem = MempoolAnalyzerService().analyze(MempoolSnapshot(backlog_tx_count=1, backlog_vbytes=1000, median_fee_rate_sat_vb=2, high_priority_fee_rate_sat_vb=5))
    assert mem.freshness["single_source_advisory"] is True
    assert mem.freshness["advisory_not_consensus_proof"] is True

    utxo = UTXOAnalyzerService().analyze(utxo_values_sats=[10_000, 20_000])
    assert utxo.freshness["single_source_advisory"] is True
    assert utxo.freshness["advisory_not_consensus_proof"] is True
