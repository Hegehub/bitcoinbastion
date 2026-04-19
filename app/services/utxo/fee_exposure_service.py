from app.domain.utxo import FeeScenario
from app.schemas.utxo import UTXOSpendProjectionOut


class FeeExposureService:
    INPUT_VBYTES = 68
    OUTPUT_VBYTES = 31
    OVERHEAD_VBYTES = 10

    def estimate_projection(
        self,
        *,
        inputs: int,
        fee_scenario: FeeScenario,
        outputs: int = 2,
    ) -> UTXOSpendProjectionOut:
        estimated_vbytes = self.OVERHEAD_VBYTES + (inputs * self.INPUT_VBYTES) + (outputs * self.OUTPUT_VBYTES)
        fee_sats = int(estimated_vbytes * fee_scenario.fee_rate_sat_vb)
        return UTXOSpendProjectionOut(
            scenario=fee_scenario.label,
            fee_rate_sat_vb=fee_scenario.fee_rate_sat_vb,
            estimated_inputs=inputs,
            estimated_vbytes=estimated_vbytes,
            estimated_fee_sats=fee_sats,
        )
