from app.schemas.utxo import UTXOAnalysisOut
from app.services.utxo.utxo_analyzer_service import UTXOAnalyzerService


class WalletStructureAnalyzer:
    def __init__(self) -> None:
        self.utxo = UTXOAnalyzerService()

    def profile(self, *, utxo_values_sats: list[int]) -> UTXOAnalysisOut:
        return self.utxo.analyze(utxo_values_sats=utxo_values_sats)
