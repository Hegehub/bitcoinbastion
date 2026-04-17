from pydantic import BaseModel, Field


class UTXOSpendProjectionOut(BaseModel):
    scenario: str
    fee_rate_sat_vb: float
    estimated_inputs: int
    estimated_vbytes: int
    estimated_fee_sats: int


class UTXOAnalysisOut(BaseModel):
    utxo_count: int
    dust_outputs: int
    dust_ratio: float = Field(ge=0.0, le=1.0)
    fragmentation_score: float = Field(ge=0.0, le=1.0)
    estimated_inputs_to_spend_1m_sats: int
    consolidation_candidate_count: int
    confidence: float = Field(ge=0.0, le=1.0)
    freshness: dict[str, object]
    explainability: dict[str, object]
    fee_projections: list[UTXOSpendProjectionOut]
